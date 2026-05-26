"""
models.py
---------
SQLAlchemy ORM models for the Transplant Patient Timeline Platform.

Tables:
  - patients      : one row per patient, stores date range and total follow-up days
  - measurements  : all clinical / lab / ChIP-seq data points
  - notes         : free-text clinical annotations added by users
  - uploads       : audit log of every CSV upload
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Text, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Patient(Base):
    """One row per unique PatientID found in uploaded CSV data."""
    __tablename__ = "patients"

    id         = Column(String, primary_key=True)   # PatientID from CSV
    first_date = Column(Date,   nullable=False)      # earliest measurement date
    last_date  = Column(Date,   nullable=False)      # latest measurement date
    total_days = Column(Integer, nullable=False)     # last_date - first_date in days

    measurements = relationship("Measurement", back_populates="patient", cascade="all, delete-orphan")
    notes        = relationship("Note",        back_populates="patient", cascade="all, delete-orphan")


class Measurement(Base):
    """
    One row per data point (lab result, biopsy event, plasma sample, ChIP-seq value).
    All dates are stored both as calendar date and as day_offset (days since patient Day 1).
    """
    __tablename__ = "measurements"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    date       = Column(Date,   nullable=False)
    day_offset = Column(Integer, nullable=False)  # days since patient's Day 1 (first_date)
    label      = Column(String, nullable=False, index=True)
    value      = Column(String, nullable=True)    # stored as text; cast to float at query time
    category   = Column(String, nullable=False)   # 'Lab Data' | 'Biopsies' | 'Plasma Samples'

    patient = relationship("Patient", back_populates="measurements")


class Note(Base):
    """
    Free-text clinical notes added by users, attached to a patient and a specific day.
    Stored in the database; no backend authentication, so all notes are shared lab-wide.
    """
    __tablename__ = "notes"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    day_offset = Column(Integer, nullable=False)
    date       = Column(Date,   nullable=True)
    content    = Column(Text,   nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    patient = relationship("Patient", back_populates="notes")


class Upload(Base):
    """Audit log of every CSV upload, including row count and any parse errors."""
    __tablename__ = "uploads"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    filename    = Column(String,  nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    row_count   = Column(Integer, nullable=True)
    patient_count = Column(Integer, nullable=True)
    status      = Column(String,  nullable=False, default="ok")  # 'ok' | 'partial' | 'error'
    error_log   = Column(Text,    nullable=True)   # JSON-encoded list of error messages
