#!/usr/bin/env python3
"""Generate docs/config.json from transplant_dates.csv and bedgraphs_by_label/ directory."""

import csv
import json
import os
from datetime import datetime

# ── Unit map for common lab names ──
UNIT_MAP = {
    "ALANINE.AM.TRAN (ALT)": "U/L",
    "ASPART.AM.TRANS (AST)": "U/L",
    "ALK. PHOS.": "U/L",
    "GGTP": "U/L",
    "LDH": "U/L",
    "DIASTASE": "U/L",
    "CREATININE": "mg/dL",
    "UREA": "mg/dL",
    "T.BILIRUBIN": "mg/dL",
    "BILE ACIDS": "µmol/L",
    "ALBUMIN": "g/dL",
    "HGB": "g/dL",
    "GLUCOSE": "mg/dL",
    "SODIUM": "mEq/L",
    "POTASSIUM": "mEq/L",
    "WBC": "K/µL",
    "PLATELETS": "K/µL",
    "NEUTROPHILE": "K/µL",
    "LYMPHOCYTE": "K/µL",
    "INR": "",
    "CMV-PCR": "copies/mL",
    "EBV-PCR": "copies/mL",
}

BEDGRAPH_DIR = "bedgraphs_by_label"
CSV_FILE = "transplant_dates.csv"
OUTPUT_FILE = os.path.join("docs", "config.json")


def parse_patients(csv_path):
    """Read transplant_dates.csv (no header) and return patient list."""
    patients = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            patient_id = row[0].strip()
            birth_year = row[1].strip()
            organ = row[2].strip()
            transplant_date_str = row[3].strip()

            # Skip patients with empty transplant date
            if not transplant_date_str:
                continue

            # Parse DD/MM/YYYY date
            try:
                dt = datetime.strptime(transplant_date_str, "%d/%m/%Y")
                reference_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

            # Handle edge cases
            if birth_year == ".":
                birth_year = ""

            patients.append({
                "id": patient_id,
                "referenceDate": reference_date,
                "referenceLabel": "Transplant",
                "metadata": {
                    "organ": organ if organ else "",
                    "birthYear": birth_year,
                },
            })

    patients.sort(key=lambda p: p["id"])
    return patients


def classify_track(filename):
    """Classify a bedGraph filename into category, track name, and unit."""
    name_no_ext = filename.replace(".bedGraph", "")

    if name_no_ext.startswith("Biopsy"):
        return "Biopsy", "Biopsies", ""

    if name_no_ext.startswith("H3K4me3"):
        # Parse "H3K4me3_value-X_number-N_of_M" format
        parts = name_no_ext.split("_")
        number = ""
        total = ""
        for part in parts:
            if part.startswith("number-"):
                tokens = part.replace("number-", "").split("_")
                number = tokens[0]
            if part.startswith("of_") or part.endswith("of_3"):
                pass
        # Simpler: extract from the pattern
        import re
        m = re.search(r"number-(\d+)_of_(\d+)", name_no_ext)
        if m:
            number, total = m.group(1), m.group(2)
            track_name = f"H3K4me3 ({number}/{total})"
        else:
            track_name = name_no_ext
        return track_name, "Epigenetic", ""

    # Lab Data: track name = filename without extension
    unit = UNIT_MAP.get(name_no_ext, "")
    return name_no_ext, "Lab Data", unit


def scan_tracks(bedgraph_dir):
    """Scan bedgraph directory and build track list."""
    tracks = []
    for fname in sorted(os.listdir(bedgraph_dir)):
        if not fname.endswith(".bedGraph"):
            continue
        track_name, category, unit = classify_track(fname)
        tracks.append({
            "name": track_name,
            "file": fname,
            "category": category,
            "unit": unit,
        })
    return tracks


def build_categories():
    """Return category definitions."""
    return {
        "Lab Data": {"type": "continuous", "color": "#4f8ef7"},
        "Biopsies": {"type": "event", "color": "#f59e0b"},
        "Epigenetic": {"type": "continuous", "color": "#7c3aed"},
    }


def main():
    patients = parse_patients(CSV_FILE)
    tracks = scan_tracks(BEDGRAPH_DIR)
    categories = build_categories()

    config = {
        "patients": patients,
        "tracks": tracks,
        "categories": categories,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Generated {OUTPUT_FILE}")
    print(f"  Patients: {len(patients)}")
    print(f"  Tracks:   {len(tracks)}")
    for cat_name in categories:
        count = sum(1 for t in tracks if t["category"] == cat_name)
        print(f"    {cat_name}: {count}")


if __name__ == "__main__":
    main()
