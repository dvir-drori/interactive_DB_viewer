"""
pipeline/processor.py
---------------------
Core data-processing logic extracted and refactored from FilesGenerator-bedgraph.py.

Responsibilities:
  1. Parse and validate an uploaded CSV file
  2. Normalize dates and calculate day offsets (Day 1 = patient's earliest date)
  3. Upsert patients and measurements into the SQLite database
  4. Return a structured summary (patient count, row count, errors)

CSV expected columns:
  PatientID  : unique patient identifier (string)
  Date       : date of measurement (any format pandas can parse)
  Label      : name of the measured parameter (e.g. CREATININE, H3K4me3)
  Value      : numeric or categorical measurement value (stored as string)
  Category   : 'Lab Data' | 'Biopsies' | 'Plasma Samples'

All original pipeline logic (date anchoring, category splitting) is preserved exactly.
"""

import json
import pandas as pd
from sqlalchemy.orm import Session
from models import Patient, Measurement, Upload
import logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"PatientID", "Date", "Label", "Value", "Category"}
VALID_CATEGORIES  = {"Lab Data", "Biopsies", "Plasma Samples"}


def process_csv(file_bytes: bytes, filename: str, db: Session) -> dict:
    """
    Main entry point called by the FastAPI upload endpoint.

    Parameters
    ----------
    file_bytes : raw bytes of the uploaded CSV file
    filename   : original filename (for audit log)
    db         : active SQLAlchemy database session

    Returns
    -------
    dict with keys:
        patient_count  : number of unique patients ingested
        row_count      : number of measurement rows successfully stored
        errors         : list of human-readable error/warning strings
        status         : 'ok' | 'partial' | 'error'
    """
    errors = []

    # ------------------------------------------------------------------ #
    # Step 1: Parse CSV
    # ------------------------------------------------------------------ #
    try:
        df = pd.read_csv(
            pd.io.common.BytesIO(file_bytes),
            dtype=str,          # keep everything as string initially
            encoding="utf-8",
        )
    except Exception as exc:
        return _fail(filename, db, f"Could not parse CSV: {exc}")

    # ------------------------------------------------------------------ #
    # Step 2: Validate columns
    # ------------------------------------------------------------------ #
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return _fail(filename, db, f"Missing required columns: {missing}")

    # ------------------------------------------------------------------ #
    # Step 3: Normalize dates
    # ------------------------------------------------------------------ #
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad_dates = df["Date"].isna().sum()
    if bad_dates > 0:
        errors.append(f"{bad_dates} rows had unparseable dates and were skipped.")
    df = df.dropna(subset=["Date", "PatientID"])

    if df.empty:
        return _fail(filename, db, "No valid rows remain after date parsing.")

    # ------------------------------------------------------------------ #
    # Step 4: Validate categories
    # ------------------------------------------------------------------ #
    unknown_cats = set(df["Category"].dropna().unique()) - VALID_CATEGORIES
    if unknown_cats:
        errors.append(f"Unknown categories found (rows kept): {unknown_cats}")

    # ------------------------------------------------------------------ #
    # Step 5: Calculate day offsets — Day 1 = patient's earliest date
    # (Preserves original FilesGenerator-bedgraph.py logic exactly)
    # ------------------------------------------------------------------ #
    patient_first_dates = df.groupby("PatientID")["Date"].min()
    df["day_offset"] = df.apply(
        lambda row: (row["Date"] - patient_first_dates[row["PatientID"]]).days + 1,
        axis=1,
    ).astype(int)

    # ------------------------------------------------------------------ #
    # Step 6: Upsert patients
    # ------------------------------------------------------------------ #
    patient_stats = df.groupby("PatientID").agg(
        first_date=("Date", "min"),
        last_date=("Date",  "max"),
    ).reset_index()

    for _, prow in patient_stats.iterrows():
        pid        = str(prow["PatientID"])
        first_date = prow["first_date"].date()
        last_date  = prow["last_date"].date()
        total_days = (prow["last_date"] - prow["first_date"]).days + 1

        existing = db.get(Patient, pid)
        if existing:
            # Update date range if new data extends it
            existing.first_date = min(existing.first_date, first_date)
            existing.last_date  = max(existing.last_date,  last_date)
            existing.total_days = (existing.last_date - existing.first_date).days + 1
        else:
            db.add(Patient(
                id=pid,
                first_date=first_date,
                last_date=last_date,
                total_days=total_days,
            ))

    db.flush()

    # ------------------------------------------------------------------ #
    # Step 7: Delete existing measurements for affected patients, then re-insert
    # (Ensures a re-upload of the same file is idempotent)
    # ------------------------------------------------------------------ #
    affected_patients = df["PatientID"].unique().tolist()
    db.query(Measurement).filter(
        Measurement.patient_id.in_(affected_patients)
    ).delete(synchronize_session=False)

    # ------------------------------------------------------------------ #
    # Step 8: Insert measurements
    # ------------------------------------------------------------------ #
    rows_added = 0
    for _, row in df.iterrows():
        try:
            db.add(Measurement(
                patient_id=str(row["PatientID"]),
                date=row["Date"].date(),
                day_offset=int(row["day_offset"]),
                label=str(row["Label"]).strip(),
                value=str(row["Value"]).strip() if pd.notna(row["Value"]) else None,
                category=str(row["Category"]).strip(),
            ))
            rows_added += 1
        except Exception as exc:
            errors.append(f"Row skipped ({row.get('PatientID','?')} / {row.get('Label','?')}): {exc}")

    # ------------------------------------------------------------------ #
    # Step 9: Write upload audit log
    # ------------------------------------------------------------------ #
    status = "ok" if not errors else "partial"
    db.add(Upload(
        filename=filename,
        row_count=rows_added,
        patient_count=len(affected_patients),
        status=status,
        error_log=json.dumps(errors) if errors else None,
    ))

    db.commit()
    logger.info("Upload complete: %d rows, %d patients, %d errors", rows_added, len(affected_patients), len(errors))

    return {
        "patient_count": len(affected_patients),
        "row_count":     rows_added,
        "errors":        errors,
        "status":        status,
    }


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #

def _fail(filename: str, db: Session, message: str) -> dict:
    """Record a failed upload in the audit log and return an error response."""
    try:
        db.add(Upload(filename=filename, status="error", error_log=json.dumps([message])))
        db.commit()
    except Exception:
        pass
    return {"patient_count": 0, "row_count": 0, "errors": [message], "status": "error"}
