"""
pipeline/export.py
------------------
Re-generates the IGV-compatible static files (bedGraph, FASTA, GFF) from
the database. Called either manually or from the /api/export endpoint.

All file formats are written in pure Python — no biopython or pyfaidx needed.

Output files:
  output_dir/patients.fasta
  output_dir/patients.fasta.fai
  output_dir/bedgraphs_by_label/*.bedGraph
  output_dir/annotations.gff
"""

import os
import shutil
import random
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from models import Patient, Measurement


def random_rgb():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def write_fasta_and_fai(records: list[dict], fasta_path: Path):
    """
    Write a FASTA file and its .fai index in pure Python.
    records: list of {'id': str, 'length': int}

    FASTA format:
        >patient_id
        AAAA...A   (length bases, all A)

    FAI format (one line per sequence):
        name  length  offset  bases_per_line  bytes_per_line
    """
    fai_lines = []
    offset = 0

    with open(fasta_path, "w", newline="\n") as f:
        for rec in records:
            pid    = rec["id"]
            length = rec["length"]

            header = f">{pid}\n"
            seq    = "A" * length + "\n"

            f.write(header)
            offset_after_header = offset + len(header)
            f.write(seq)

            # FAI: name, seq_length, byte_offset_of_seq, bases_per_line, bytes_per_line
            fai_lines.append(f"{pid}\t{length}\t{offset_after_header}\t{length}\t{length + 1}")
            offset = offset_after_header + len(seq)

    with open(str(fasta_path) + ".fai", "w", newline="\n") as f:
        f.write("\n".join(fai_lines) + "\n")


def export_all(db: Session, output_dir: str) -> dict:
    """
    Export all data from the database to IGV-compatible static files.

    Parameters
    ----------
    db         : active SQLAlchemy session
    output_dir : directory where output files will be written

    Returns
    -------
    dict with keys: fasta_path, bedgraph_count, annotations_path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    bedgraph_dir = output_path / "bedgraphs_by_label"
    if bedgraph_dir.exists():
        shutil.rmtree(bedgraph_dir)
    bedgraph_dir.mkdir()

    patients     = db.query(Patient).all()
    measurements = db.query(Measurement).all()

    if not patients:
        return {"error": "No patients in database. Upload a CSV first."}

    # ------------------------------------------------------------------ #
    # 1. Write patients.fasta + .fai (pure Python, no biopython)
    # ------------------------------------------------------------------ #
    fasta_path = output_path / "patients.fasta"
    records = [{"id": p.id, "length": p.total_days} for p in patients]
    write_fasta_and_fai(records, fasta_path)

    # ------------------------------------------------------------------ #
    # 2. Build bedGraph files
    # ------------------------------------------------------------------ #
    df = pd.DataFrame([{
        "patient_id": m.patient_id,
        "day_offset": m.day_offset,
        "label":      m.label,
        "value":      m.value,
        "category":   m.category,
    } for m in measurements])

    bedgraph_count = 0

    # Lab Data — continuous numeric tracks
    lab_df = df[df["category"] == "Lab Data"]
    label_colors = {label: random_rgb() for label in lab_df["label"].dropna().unique()}

    for label in lab_df["label"].dropna().unique():
        label_name = label.replace("%", "")
        r, g, b    = label_colors[label]
        filepath   = bedgraph_dir / f"{label_name}.bedGraph"
        with open(filepath, "w") as f:
            f.write(f'track type=bedGraph name="{label_name}" description="{label_name}" '
                    f'color={r},{g},{b} visibility=full autoScale=on\n')
            for _, row in lab_df[lab_df["label"] == label].iterrows():
                try:
                    value = float(row["value"])
                except (TypeError, ValueError):
                    continue
                start = int(row["day_offset"]) - 1
                end   = int(row["day_offset"])
                f.write(f"{row['patient_id']}\t{start}\t{end}\t{value}\n")
        bedgraph_count += 1

    # Biopsies + Plasma Samples — binary event tracks
    binary_df = df[df["category"].isin(["Biopsies", "Plasma Samples"])]
    for test in binary_df["label"].dropna().unique():
        test_df       = binary_df[binary_df["label"] == test]
        unique_values = test_df["value"].dropna().unique()
        num_values    = len(unique_values)
        for idx, val in enumerate(unique_values, start=1):
            r, g, b   = random_rgb()
            safe_val  = str(val).replace(" ", "_").replace("/", "_")
            filename  = f"{test}_value-{safe_val}_number-{idx}_of_{num_values}.bedGraph"
            with open(bedgraph_dir / filename, "w") as f:
                f.write(f'track type=bedGraph name="{test}_{safe_val}" '
                        f'description="{test}_{safe_val}" '
                        f'color={r},{g},{b} visibility=full autoScale=off viewLimits=0:1\n')
                for _, row in test_df[test_df["value"] == val].iterrows():
                    start = int(row["day_offset"]) - 1
                    end   = int(row["day_offset"])
                    f.write(f"{row['patient_id']}\t{start}\t{end}\t1.0\n")
            bedgraph_count += 1

    # ------------------------------------------------------------------ #
    # 3. Write annotations.gff
    # ------------------------------------------------------------------ #
    annotations_path = output_path / "annotations.gff"
    with open(annotations_path, "w") as f:
        f.write("##gff-version 3\n")
        for m in measurements:
            date_str = m.date.strftime("%Y-%m-%d") if m.date else "Unknown"
            f.write(f"{m.patient_id}\t.\tbiological_test\t{m.day_offset}\t{m.day_offset}"
                    f"\t.\t+\t.\tNote=\"{date_str}\"\n")

    return {
        "fasta_path":       str(fasta_path),
        "bedgraph_count":   bedgraph_count,
        "annotations_path": str(annotations_path),
    }
