"""
FilesGenerator-bedgraph.py
--------------------------
ORIGINAL PIPELINE SCRIPT — preserved for standalone use.

Generates IGV-compatible static files directly from a CSV file,
WITHOUT using the database. Useful for:
  - Generating files for the IGV-web viewer tab
  - Batch processing outside the web platform
  - Testing / debugging

Usage:
    python FilesGenerator-bedgraph.py

Input:
    Place your CSV file as 'Transplant-data.csv' in the same directory.
    Required columns: PatientID, Date, Label, Value, Category

Output files (written to the current directory):
    patients.fasta              — fake genome (chromosome = patient, pos = days)
    patients.fasta.fai          — FASTA index for IGV
    bedgraphs_by_label/*.bedGraph  — one bedGraph per clinical label
    annotations.gff             — date annotations for all events

For the web platform upload workflow, use the web interface instead.
This script and the web platform use identical data-processing logic.
"""

import shutil
import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import os
import random
from pyfaidx import Fasta

# ------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------ #
INPUT_CSV    = 'Transplant-data.csv'    # change this to your CSV filename
OUTPUT_FASTA = 'patients.fasta'
OUTPUT_GFF   = 'annotations.gff'
OUTPUT_DIR   = 'bedgraphs_by_label'

# ------------------------------------------------------------------ #
# Step 1: Load and validate CSV
# ------------------------------------------------------------------ #
print(f"Loading {INPUT_CSV}...")
df = pd.read_csv(INPUT_CSV, dtype='str')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df = df.dropna(subset=['Date', 'PatientID'])
print(f"  {len(df)} valid rows, {df['PatientID'].nunique()} patients")

# ------------------------------------------------------------------ #
# Step 2: Calculate day offsets (Day 1 = patient's earliest date)
# ------------------------------------------------------------------ #
patient_first_dates = df.groupby('PatientID')['Date'].min()
df['Position'] = df.apply(
    lambda row: (row['Date'] - patient_first_dates[row['PatientID']]).days + 1,
    axis=1
)

# ------------------------------------------------------------------ #
# Step 3: Generate patients.fasta
# ------------------------------------------------------------------ #
print(f"Writing {OUTPUT_FASTA}...")
fasta_records = []
for patient_id, group in df.groupby('PatientID'):
    seq_length = group['Position'].max()
    record = SeqRecord(Seq('A' * seq_length), id=str(patient_id), description="")
    fasta_records.append(record)
SeqIO.write(fasta_records, OUTPUT_FASTA, 'fasta')
Fasta(OUTPUT_FASTA)   # generates .fai index

# ------------------------------------------------------------------ #
# Step 4: Generate bedGraph files
# ------------------------------------------------------------------ #
def random_rgb():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)

# Lab Data — continuous numeric tracks
lab_df = df[df['Category'] == 'Lab Data']
print(f"Writing {lab_df['Label'].nunique()} Lab Data bedGraph tracks...")
label_colors = {label: random_rgb() for label in lab_df['Label'].dropna().unique()}

for label in lab_df['Label'].dropna().unique():
    label_name = label.replace('%', '')
    r, g, b = label_colors[label]
    with open(f"{OUTPUT_DIR}/{label_name}.bedGraph", "w") as bg_file:
        bg_file.write(
            f'track type=bedGraph name="{label_name}" description="{label_name}" '
            f'color={r},{g},{b} visibility=full autoScale=on\n'
        )
        for _, row in lab_df[lab_df['Label'] == label].iterrows():
            chrom = row['PatientID']
            start = int(row['Position']) - 1
            end   = int(row['Position'])
            try:
                value = float(row['Value'])
            except (ValueError, TypeError):
                continue
            bg_file.write(f"{chrom}\t{start}\t{end}\t{value}\n")

# Biopsies + Plasma Samples — binary event tracks
binary_df   = df[df['Category'].isin(['Biopsies', 'Plasma Samples'])]
print(f"Writing {binary_df['Label'].nunique()} event bedGraph tracks...")

for test in binary_df['Label'].dropna().unique():
    test_df       = binary_df[binary_df['Label'] == test]
    unique_values = test_df['Value'].dropna().unique()
    num_values    = len(unique_values)

    for idx, val in enumerate(unique_values, start=1):
        r, g, b   = random_rgb()
        safe_val  = str(val).replace(" ", "_").replace("/", "_")
        filename  = f"{OUTPUT_DIR}/{test}_value-{safe_val}_number-{idx}_of_{num_values}.bedGraph"
        track_name = f"{test}_{safe_val}"

        with open(filename, "w") as bg_file:
            bg_file.write(
                f'track type=bedGraph name="{track_name}" description="{track_name}" '
                f'color={r},{g},{b} visibility=full autoScale=off viewLimits=0:1\n'
            )
            for _, row in test_df[test_df['Value'] == val].iterrows():
                chrom = row['PatientID']
                start = int(row['Position']) - 1
                end   = int(row['Position'])
                bg_file.write(f"{chrom}\t{start}\t{end}\t1.0\n")

# ------------------------------------------------------------------ #
# Step 5: Generate annotations.gff
# ------------------------------------------------------------------ #
print(f"Writing {OUTPUT_GFF}...")
with open(OUTPUT_GFF, "w") as gff_file:
    gff_file.write("##gff-version 3\n")
    for _, row in df.iterrows():
        chrom    = row['PatientID']
        start    = int(row['Position'])
        date_str = row['Date'].strftime("%Y-%m-%d") if pd.notnull(row['Date']) else "Unknown"
        gff_file.write(
            f"{chrom}\t.\tbiological_test\t{start}\t{start}\t.\t+\t.\tNote=\"{date_str}\"\n"
        )

print("\nDone. Upload patients.fasta, patients.fasta.fai and bedgraphs_by_label/ to the IGV website.")
