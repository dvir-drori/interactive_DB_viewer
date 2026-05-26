import shutil
from operator import index
import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import os
import random
from pyfaidx import Fasta

#---------------------------------------------------
# This script processes transplant patient data to generate:
# 1. patients.fasta
# 2. patients.fasta.fai
# 3. bedgraphs by label in bedgraphs_by_label/
# 4. annotations.gff
# 1,2,3 are uploaded to the git of the website
#---------------------------------------------------

# Load CSV and parse dates
df = pd.read_csv('Transplant-data_0901_viral.csv', dtype='str')
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Drop rows with missing date or patient ID
df = df.dropna(subset=['Date', 'PatientID'])

# Assign position relative to each patient's first date
patient_first_dates = df.groupby('PatientID')['Date'].min()
df['Position'] = df.apply(
    lambda row: (row['Date'] - patient_first_dates[row['PatientID']]).days + 1,
    axis=1
)

# Create FASTA file with sequences per patient
fasta_records = []
for patient_id, group in df.groupby('PatientID'):
    seq_length = group['Position'].max()
    sequence = 'A' * seq_length
    record = SeqRecord(Seq(sequence), id=str(patient_id), description="")
    fasta_records.append(record)
SeqIO.write(fasta_records, 'patients.fasta', 'fasta')

# Generate FASTA index using pyfaidx
Fasta('patients.fasta')

# Random color generator
def random_rgb():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)

# Create directory for output tracks
if os.path.exists("bedgraphs_by_label"):
    shutil.rmtree("bedgraphs_by_label")
os.makedirs("bedgraphs_by_label", exist_ok=True)

lab_df = df[df['Category'] == 'Lab Data']
label_colors = {label: random_rgb() for label in lab_df['Label'].dropna().unique()}

for label in lab_df['Label'].dropna().unique():
    label_name = label.replace('%', '')
    r, g, b = label_colors[label]
    with open(f"bedgraphs_by_label/{label_name}.bedGraph", "w") as bg_file:
        bg_file.write(
            f'track type=bedGraph name="{label_name}" description="{label_name}" '
            f'color={r},{g},{b} visibility=full autoScale=on\n'
        )
        for _, row in lab_df[lab_df['Label'] == label].iterrows():
            chrom = row['PatientID']
            start = int(row['Position']) - 1
            end = int(row['Position'])
            try:
                value = float(row['Value'])
            except:
                continue
            bg_file.write(f"{chrom}\t{start}\t{end}\t{value}\n")

binary_df = df[df['Category'].isin(['Biopsies', 'Plasma Samples'])]
unique_tests = binary_df['Label'].dropna().unique()

for test in unique_tests:
    test_df = binary_df[binary_df['Label'] == test]
    if test_df.empty or 'Value' not in test_df.columns:
        continue

    unique_values = test_df['Value'].dropna().unique()
    num_values = len(unique_values)

    index = 1
    for val in unique_values:
        r, g, b = random_rgb()
        safe_val = str(val).replace(" ", "_").replace("/", "_")
        filename = f"bedgraphs_by_label/{test}_value-{safe_val}_number-{index}_of_{num_values}.bedGraph"
        index += 1
        track_name = f"{test}_{safe_val}"

        with open(filename, "w") as bg_file:
            bg_file.write(
                f'track type=bedGraph name="{track_name}" description="{track_name}" '
                f'color={r},{g},{b} visibility=full autoScale=off viewLimits=0:1\n'
            )
            for _, row in test_df[test_df['Value'] == val].iterrows():
                chrom = row['PatientID']
                start = int(row['Position']) - 1
                end = int(row['Position'])
                value = 1.0
                bg_file.write(f"{chrom}\t{start}\t{end}\t{value}\n")

with open("annotations.gff", "w") as gff_file:
    gff_file.write("##gff-version 3\n")

    for _, row in df.iterrows():
        chrom = row['PatientID']
        start = int(row['Position'])
        end = start
        date_str = row['Date'].strftime("%Y-%m-%d") if pd.notnull(row['Date']) else "Unknown"

        gff_file.write(
            f"{chrom}\t.\tbiological_test\t{start}\t{end}\t.\t+\t.\tNote=\"{date_str}\"\n"
        )