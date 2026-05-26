"""
main.py
-------
FastAPI application for the Transplant Patient Clinical Timeline Platform.

Endpoints:
  POST /api/upload                            Upload and ingest a CSV file
  GET  /api/upload/history                   List previous uploads
  GET  /api/patients                          List all patients
  GET  /api/patients/{id}/summary             Patient metadata + available labels
  GET  /api/patients/{id}/measurements        Time-series data (filterable)
  GET  /api/patients/{id}/events              Biopsy + Plasma Sample events
  GET  /api/patients/{id}/notes               List notes for a patient
  POST /api/patients/{id}/notes               Add a note
  DELETE /api/notes/{note_id}                 Delete a note
  GET  /api/compare                           Multi-patient comparison data
  POST /api/export                            Re-generate IGV static files from DB

The app also serves the React frontend's built files from /static/.
Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import json
import os
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from database import engine, get_db
from models import Base, Patient, Measurement, Note, Upload
from pipeline.processor import process_csv
from pipeline.export import export_all

# ------------------------------------------------------------------ #
# Application setup
# ------------------------------------------------------------------ #
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transplant Patient Timeline API",
    description="Backend for the NIR Lab clinical timeline visualization platform.",
    version="1.0.0",
)

# Allow the React dev server (port 5173) to call the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------ #
# Pydantic schemas (request / response models)
# ------------------------------------------------------------------ #

class NoteCreate(BaseModel):
    day_offset: int
    date:       Optional[date] = None
    content:    str


class NoteOut(BaseModel):
    id:         int
    patient_id: str
    day_offset: int
    date:       Optional[date]
    content:    str
    created_at: datetime

    class Config:
        from_attributes = True


class PatientOut(BaseModel):
    id:                str
    first_date:        date
    last_date:         date
    total_days:        int
    measurement_count: int

    class Config:
        from_attributes = True


class UploadOut(BaseModel):
    id:            int
    filename:      str
    uploaded_at:   datetime
    row_count:     Optional[int]
    patient_count: Optional[int]
    status:        str
    errors:        List[str] = []

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
# Upload endpoints
# ------------------------------------------------------------------ #

@app.post("/api/upload", summary="Upload and ingest a CSV data file")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a CSV with columns: PatientID, Date, Label, Value, Category.
    Parses the file, validates it, and stores all data in the database.
    Returns a summary including patient count, row count, and any errors.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    contents = await file.read()
    result   = process_csv(contents, file.filename, db)

    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["errors"])

    return result


@app.get("/api/upload/history", response_model=List[UploadOut], summary="List upload history")
def get_upload_history(db: Session = Depends(get_db)):
    uploads = db.query(Upload).order_by(Upload.uploaded_at.desc()).limit(50).all()
    result  = []
    for u in uploads:
        errors = json.loads(u.error_log) if u.error_log else []
        result.append(UploadOut(
            id=u.id, filename=u.filename, uploaded_at=u.uploaded_at,
            row_count=u.row_count, patient_count=u.patient_count,
            status=u.status, errors=errors,
        ))
    return result


# ------------------------------------------------------------------ #
# Patient endpoints
# ------------------------------------------------------------------ #

@app.get("/api/patients", response_model=List[PatientOut], summary="List all patients")
def list_patients(db: Session = Depends(get_db)):
    """Returns all patients with metadata and measurement count."""
    patients = db.query(Patient).order_by(Patient.id).all()
    result   = []
    for p in patients:
        count = db.query(func.count(Measurement.id)).filter(
            Measurement.patient_id == p.id
        ).scalar()
        result.append(PatientOut(
            id=p.id, first_date=p.first_date, last_date=p.last_date,
            total_days=p.total_days, measurement_count=count,
        ))
    return result


@app.get("/api/patients/{patient_id}/summary", summary="Patient metadata + available labels")
def patient_summary(patient_id: str, db: Session = Depends(get_db)):
    """
    Returns patient date range and a grouped list of available labels per category.
    Used to populate the track selector panel in the frontend.
    """
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    rows = (
        db.query(Measurement.category, Measurement.label)
        .filter(Measurement.patient_id == patient_id)
        .distinct()
        .all()
    )

    labels_by_category: dict = {}
    for category, label in rows:
        labels_by_category.setdefault(category, [])
        if label not in labels_by_category[category]:
            labels_by_category[category].append(label)

    return {
        "id":                 patient.id,
        "first_date":         patient.first_date.isoformat(),
        "last_date":          patient.last_date.isoformat(),
        "total_days":         patient.total_days,
        "labels_by_category": labels_by_category,
    }


@app.get("/api/patients/{patient_id}/measurements", summary="Time-series data for a patient")
def get_measurements(
    patient_id: str,
    labels:     Optional[str] = Query(None, description="Comma-separated list of labels to include"),
    category:   Optional[str] = Query(None, description="Filter by category"),
    db:         Session = Depends(get_db),
):
    """
    Returns all measurements for a patient, optionally filtered by label and/or category.
    Each row includes: day_offset, date, label, value, category.
    Used to build the Plotly timeline chart.
    """
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    query = db.query(Measurement).filter(Measurement.patient_id == patient_id)

    if labels:
        label_list = [l.strip() for l in labels.split(",")]
        query = query.filter(Measurement.label.in_(label_list))
    if category:
        query = query.filter(Measurement.category == category)

    rows = query.order_by(Measurement.day_offset).all()

    return [
        {
            "day_offset": m.day_offset,
            "date":       m.date.isoformat() if m.date else None,
            "label":      m.label,
            "value":      m.value,
            "category":   m.category,
        }
        for m in rows
    ]


@app.get("/api/patients/{patient_id}/events", summary="Clinical events (biopsies + plasma samples)")
def get_events(patient_id: str, db: Session = Depends(get_db)):
    """
    Returns all Biopsy and Plasma Sample events for a patient.
    Used to draw event markers on the timeline.
    """
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    rows = (
        db.query(Measurement)
        .filter(
            Measurement.patient_id == patient_id,
            Measurement.category.in_(["Biopsies", "Plasma Samples"]),
        )
        .order_by(Measurement.day_offset)
        .all()
    )

    return [
        {
            "day_offset": m.day_offset,
            "date":       m.date.isoformat() if m.date else None,
            "label":      m.label,
            "value":      m.value,
            "category":   m.category,
        }
        for m in rows
    ]


# ------------------------------------------------------------------ #
# Notes endpoints
# ------------------------------------------------------------------ #

@app.get("/api/patients/{patient_id}/notes", response_model=List[NoteOut], summary="Get notes for a patient")
def get_notes(patient_id: str, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")
    return db.query(Note).filter(Note.patient_id == patient_id).order_by(Note.day_offset).all()


@app.post("/api/patients/{patient_id}/notes", response_model=NoteOut, summary="Add a note")
def add_note(patient_id: str, note_data: NoteCreate, db: Session = Depends(get_db)):
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")
    note = Note(
        patient_id=patient_id,
        day_offset=note_data.day_offset,
        date=note_data.date,
        content=note_data.content,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@app.delete("/api/notes/{note_id}", summary="Delete a note")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    db.delete(note)
    db.commit()
    return {"deleted": note_id}


# ------------------------------------------------------------------ #
# Comparison endpoint
# ------------------------------------------------------------------ #

@app.get("/api/compare", summary="Multi-patient comparison data")
def compare_patients(
    patients: str = Query(..., description="Comma-separated patient IDs"),
    label:    str = Query(..., description="Label to compare across patients"),
    db:       Session = Depends(get_db),
):
    """
    Returns time-series data for a single label across multiple patients,
    all aligned to Day 1. Used by the CompareView page.
    """
    patient_ids = [p.strip() for p in patients.split(",")]
    result = {}

    for pid in patient_ids:
        rows = (
            db.query(Measurement)
            .filter(
                Measurement.patient_id == pid,
                Measurement.label == label,
            )
            .order_by(Measurement.day_offset)
            .all()
        )
        result[pid] = [
            {
                "day_offset": m.day_offset,
                "date":       m.date.isoformat() if m.date else None,
                "value":      m.value,
            }
            for m in rows
        ]

    return result


# ------------------------------------------------------------------ #
# IGV export endpoint
# ------------------------------------------------------------------ #

@app.post("/api/export", summary="Re-generate IGV static files from database")
def export_igv(
    output_dir: str = Query(
        default="igv_export",
        description="Directory where bedGraph/FASTA files will be written",
    ),
    db: Session = Depends(get_db),
):
    """
    Re-generates patients.fasta, bedgraphs_by_label/*.bedGraph and annotations.gff
    from the current database contents. Used to keep the IGV viewer tab in sync.
    """
    result = export_all(db, output_dir)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ------------------------------------------------------------------ #
# Serve React frontend (production build)
# ------------------------------------------------------------------ #

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all route: serve React's index.html for any non-API path."""
        index = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"detail": "Frontend not built yet. Run: cd frontend && npm run build"}
