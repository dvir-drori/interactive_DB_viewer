"""
FilesGenerator-bedgraph.py
--------------------------
ORIGINAL PIPELINE SCRIPT — preserved for standalone use.
Pure Python + Pandas only — no biopython or pyfaidx required.

Usage:
    python FilesGenerator-bedgraph.py

Input:
    Place your CSV file as 'Transplant-data.csv' in the same directory.
    Required columns: PatientID, Date, Label, Value, Category

Output:
    patients.fasta, patients.fasta.fai, bedgraphs_by_label/, annotations.gff
"""

import os
import shutil
import random
import pandas as pd

INPUT_CSV  = 'Transplant-data.csv'
OUTPUT_DIR = 'bedgraphs_by_label'

def random_rgb():
    return random.randint(0,255), random.randint(0,255), random.randint(0,255)

def write_fasta_and_fai(records, fasta_path):
    """Write FASTA + FAI index in pure Python. records = list of (id, length)."""
    fai_lines = []
    offset    = 0
    with open(fasta_path, "w", newline="\n") as f:
        for pid, length in records:
            header = f">{pid}\n"
            seq    = "A" * length + "\n"
            f.write(header)
            offset_after_header = offset + len(header)
            f.write(seq)
            fai_lines.append(f"{pid}\t{length}\t{offset_after_header}\t{length}\t{length+1}")
            offset = offset_after_header + len(seq)
    with open(fasta_path + ".fai", "w", newline="\n") as f:
        f.write("\n".join(fai_lines) + "\n")

# ── Load CSV ──────────────────────────────────────────────────────────
print(f"Loading {INPUT_CSV}...")
df = pd.read_csv(INPUT_CSV, dtype='str')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date', 'PatientID'])
print(f"  {len(df)} valid rows, {df['PatientID'].nunique()} patients")

# ── Day offsets ───────────────────────────────────────────────────────
patient_first_dates = df.groupby('PatientID')['Date'].min()
df['Position'] = df.apply(
    lambda row: (row['Date'] - patient_first_dates[row['PatientID']]).days + 1,
    axis=1
)

# ── FASTA + FAI ───────────────────────────────────────────────────────
print("Writing patients.fasta...")
records = [
    (str(pid), int(group['Position'].max()))
    for pid, group in df.groupby('PatientID')
]
write_fasta_and_fai(records, 'patients.fasta')

# ── bedGraph files ────────────────────────────────────────────────────
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)

# Lab Data
lab_df = df[df['Category'] == 'Lab Data']
print(f"Writing {lab_df['Label'].nunique()} Lab Data tracks...")
for label in lab_df['Label'].dropna().unique():
    label_name = label.replace('%', '')
    r, g, b    = random_rgb()
    with open(f"{OUTPUT_DIR}/{label_name}.bedGraph", "w") as f:
        f.write(f'track type=bedGraph name="{label_name}" description="{label_name}" '
                f'color={r},{g},{b} visibility=full autoScale=on\n')
        for _, row in lab_df[lab_df['Label'] == label].iterrows():
            try:
                value = float(row['Value'])
            except (ValueError, TypeError):
                continue
            start = int(row['Position']) - 1
            f.write(f"{row['PatientID']}\t{start}\t{int(row['Position'])}\t{value}\n")

# Biopsies + Plasma Samples
binary_df = df[df['Category'].isin(['Biopsies', 'Plasma Samples'])]
print(f"Writing {binary_df['Label'].nunique()} event tracks...")
for test in binary_df['Label'].dropna().unique():
    test_df       = binary_df[binary_df['Label'] == test]
    unique_values = test_df['Value'].dropna().unique()
    for idx, val in enumerate(unique_values, start=1):
        r, g, b  = random_rgb()
        safe_val = str(val).replace(" ","_").replace("/","_")
        fname    = f"{OUTPUT_DIR}/{test}_value-{safe_val}_number-{idx}_of_{len(unique_values)}.bedGraph"
        with open(fname, "w") as f:
            f.write(f'track type=bedGraph name="{test}_{safe_val}" '
                    f'description="{test}_{safe_val}" '
                    f'color={r},{g},{b} visibility=full autoScale=off viewLimits=0:1\n')
            for _, row in test_df[test_df['Value'] == val].iterrows():
                start = int(row['Position']) - 1
                f.write(f"{row['PatientID']}\t{start}\t{int(row['Position'])}\t1.0\n")

# ── GFF annotations ───────────────────────────────────────────────────
print("Writing annotations.gff...")
with open("annotations.gff", "w") as f:
    f.write("##gff-version 3\n")
    for _, row in df.iterrows():
        date_str = row['Date'].strftime("%Y-%m-%d")
        pos      = int(row['Position'])
        f.write(f"{row['PatientID']}\t.\tbiological_test\t{pos}\t{pos}\t.\t+\t.\tNote=\"{date_str}\"\n")

print("\nDone.")
