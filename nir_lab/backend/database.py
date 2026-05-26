"""
database.py
-----------
SQLite database connection using SQLAlchemy.

The database file (nir_lab.db) is created automatically on first run
in the same directory as this file. No separate database server is required.

Usage:
    from database import SessionLocal, engine
    from models import Base

    Base.metadata.create_all(bind=engine)   # create tables if they don't exist

    with SessionLocal() as db:
        results = db.query(...)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database file path — stored next to the backend scripts
# On Render: store DB on persistent disk at /data/ (survives redeploys)
# Locally:   store next to the backend scripts
if os.path.isdir("/data"):
    DB_PATH = "/data/nir_lab.db"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH  = os.path.join(BASE_DIR, "nir_lab.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI threading
    echo=False,  # set True to log all SQL queries during development
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency: yields a database session and ensures it is closed
    after the request is complete (even if an exception occurs).

    Usage in endpoint:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
