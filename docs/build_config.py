#!/usr/bin/env python3
"""
build_config.py
---------------
Regenerate docs/config.json for the Plotly timeline viewer.

Why this exists
===============
Each measurement in the bedGraph files is stored as a *day offset* from the
patient's earliest record (day 0 = first record). The viewer turns those
offsets back into calendar dates by adding them to the patient's
``referenceDate``. For that to be correct, ``referenceDate`` must be the
patient's FIRST RECORD date — not the transplant date. Anchoring on the
transplant date is what produced the wrong years (e.g. 2027) on the x-axis.

This script rebuilds config.json so that:
  * every patient that actually has bedGraph data is included;
  * ``referenceDate`` / ``firstDate`` = the patient's earliest record date,
    reconstructed exactly from annotations.gff (which stores the real date of
    every point);
  * ``transplantDate`` and metadata (organ, birth year) are attached when
    available, for the optional transplant marker and the patient info line.

Run from the repo root:  python docs/build_config.py
"""

import csv
import glob
import json
import os
import re
import datetime
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))          # docs/
BEDGRAPH_DIR = os.path.join(HERE, "bedgraphs_by_label")
ANNOTATIONS = os.path.join(HERE, "annotations.gff")
CONFIG_OUT = os.path.join(HERE, "config.json")
# transplant_dates.csv: PatientID, birthYear, organ, transplantDate(DD/MM/YYYY)
TRANSPLANT_CSV = os.path.join(HERE, "transplant_dates.csv")

# Track catalogue (name, file, category, unit). Keep in sync with the data.
UNITS = {
    "ALANINE.AM.TRAN (ALT)": "U/L", "ALBUMIN": "g/dL", "ALK. PHOS.": "U/L",
    "ASPART.AM.TRANS (AST)": "U/L", "BILE ACIDS": "µmol/L", "CREATININE": "mg/dL",
    "DIASTASE": "U/L", "GGTP": "U/L", "GLUCOSE": "mg/dL", "HGB": "g/dL",
    "INR": "", "LDH": "U/L", "LYMPHOCYTE": "K/µL", "NEUTROPHILE": "K/µL",
    "PLATELETS": "K/µL", "POTASSIUM": "mEq/L", "SODIUM": "mEq/L",
    "T.BILIRUBIN": "mg/dL", "UREA": "mg/dL", "WBC": "K/µL",
    "CMV-PCR": "copies/mL", "EBV-PCR": "copies/mL",
}
CATEGORIES = {
    "Lab Data": {"type": "continuous", "color": "#4f8ef7"},
    "Biopsies": {"type": "event", "color": "#f59e0b"},
    "Epigenetic": {"type": "continuous", "color": "#7c3aed"},
}


def infer_first_dates():
    """firstDate[pid] = date at a point minus its (position-1) day offset."""
    pat = re.compile(
        r'^(\S+)\t\.\tbiological_test\t(\d+)\t\d+\t\.\t\+\t\.\tNote="(\d{4}-\d{2}-\d{2})"'
    )
    votes = {}
    with open(ANNOTATIONS) as fh:
        next(fh, None)  # skip ##gff-version line
        for line in fh:
            m = pat.match(line)
            if not m:
                continue
            pid, pos, dstr = m.group(1), int(m.group(2)), m.group(3)
            fd = datetime.date.fromisoformat(dstr) - datetime.timedelta(days=pos - 1)
            votes.setdefault(pid, Counter())[fd] += 1
    return {pid: c.most_common(1)[0][0].isoformat() for pid, c in votes.items()}


def load_transplant_meta():
    meta = {}
    if not os.path.exists(TRANSPLANT_CSV):
        return meta
    with open(TRANSPLANT_CSV) as fh:
        for row in csv.reader(fh):
            if not row or not row[0].startswith("TRN"):
                continue
            pid = row[0]
            by = row[1].strip() if len(row) > 1 else ""
            organ = row[2].strip() if len(row) > 2 else ""
            tdate = ""
            if len(row) > 3 and row[3].strip():
                try:
                    tdate = datetime.datetime.strptime(
                        row[3].strip(), "%d/%m/%Y").date().isoformat()
                except ValueError:
                    tdate = ""
            meta[pid] = {"birthYear": by, "organ": organ, "transplantDate": tdate}
    return meta


def patients_with_data():
    ids = set()
    for f in glob.glob(os.path.join(BEDGRAPH_DIR, "*.bedGraph")):
        with open(f) as fh:
            for line in fh:
                if line.startswith("track") or not line.strip():
                    continue
                ids.add(line.split("\t", 1)[0])
    return ids


def build_tracks():
    tracks = []
    for f in sorted(glob.glob(os.path.join(BEDGRAPH_DIR, "*.bedGraph"))):
        fname = os.path.basename(f)
        name = fname[:-len(".bedGraph")]
        if name.startswith("Biopsy"):
            tracks.append({"name": "Biopsy", "file": fname,
                           "category": "Biopsies", "unit": ""})
        elif name.startswith("H3K4me3"):
            # e.g. H3K4me3_value-2_number-2_of_3  ->  "H3K4me3 (2/3)"
            m = re.search(r"number-(\d+)_of_(\d+)", name)
            label = f"H3K4me3 ({m.group(1)}/{m.group(2)})" if m else name
            tracks.append({"name": label, "file": fname,
                           "category": "Epigenetic", "unit": ""})
        else:
            tracks.append({"name": name, "file": fname,
                           "category": "Lab Data", "unit": UNITS.get(name, "")})
    return tracks


def main():
    first = infer_first_dates()
    meta = load_transplant_meta()
    data_ids = patients_with_data()

    patients = []
    for pid in sorted(data_ids):
        fd = first.get(pid)
        if not fd:
            # No annotation for this patient — skip rather than guess a date.
            continue
        m = meta.get(pid, {})
        entry = {
            "id": pid,
            "referenceDate": fd,
            "referenceLabel": "First record",
            "firstDate": fd,
        }
        if m.get("transplantDate"):
            entry["transplantDate"] = m["transplantDate"]
        md = {}
        if m.get("organ"):
            md["organ"] = m["organ"]
        if m.get("birthYear"):
            md["birthYear"] = m["birthYear"]
        entry["metadata"] = md
        patients.append(entry)

    config = {"patients": patients, "tracks": build_tracks(), "categories": CATEGORIES}
    with open(CONFIG_OUT, "w") as fh:
        json.dump(config, fh, indent=2)

    print(f"Wrote {CONFIG_OUT}: {len(patients)} patients, {len(config['tracks'])} tracks")


if __name__ == "__main__":
    main()
