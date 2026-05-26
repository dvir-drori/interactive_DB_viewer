"""
pipeline/processor.py
---------------------
Core data-processing logic for ingesting CSV files into the database.
Pure Python + Pandas only — no biopython or pyfaidx required.

CSV expected columns:
  PatientID  : unique patient identifier (string)
  Date       : date of measurement (any format pandas can parse)
  Label      : name of the measured parameter (e.g. CREATININE, H3K4me3)
  Value      : numeric or categorical measurement value (stored as string)
  Category   : 'Lab Data' | 'Biopsies' | 'Plasma Samples'
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
    Parse, validate and ingest a CSV file into the database.

    Returns dict with: patient_count, row_count, errors, status
    """
    errors = []

    # ------------------------------------------------------------------ #
    # Step 1: Parse CSV
    # ------------------------------------------------------------------ #
    try:
        df = pd.read_csv(
            pd.io.common.BytesIO(file_bytes),
            dtype=str,
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
    bad_dates  = df["Date"].isna().sum()
    if bad_dates > 0:
        errors.append(f"{bad_dates} rows had unparseable dates and were skipped.")
    df = df.dropna(subset=["Date", "PatientID"])

    if df.empty:
        return _fail(filename, db, "No valid rows remain after date parsing.")

    # ------------------------------------------------------------------ #
    # Step 4: Warn on unknown categories (keep rows)
    # ------------------------------------------------------------------ #
    unknown_cats = set(df["Category"].dropna().unique()) - VALID_CATEGORIES
    if unknown_cats:
        errors.append(f"Unknown categories found (rows kept): {unknown_cats}")

    # ------------------------------------------------------------------ #
    # Step 5: Calculate day offsets — Day 1 = patient's earliest date
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
            existing.first_date = min(existing.first_date, first_date)
            existing.last_date  = max(existing.last_date,  last_date)
            existing.total_days = (existing.last_date - existing.first_date).days + 1
        else:
            db.add(Patient(
                id=pid, first_date=first_date,
                last_date=last_date, total_days=total_days,
            ))
    db.flush()

    # ------------------------------------------------------------------ #
    # Step 7: Delete existing measurements for affected patients, re-insert
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
    # Step 9: Audit log
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

    return {
        "patient_count": len(affected_patients),
        "row_count":     rows_added,
        "errors":        errors,
        "status":        status,
    }


def _fail(filename: str, db: Session, message: str) -> dict:
    try:
        db.add(Upload(filename=filename, status="error", error_log=json.dumps([message])))
        db.commit()
    except Exception:
        pass
    return {"patient_count": 0, "row_count": 0, "errors": [message], "status": "error"}
