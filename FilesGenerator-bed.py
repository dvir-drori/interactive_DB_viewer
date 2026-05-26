import shutil

import pandas as pd
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import  random
import os

#---------------------------------------------------
# This is an older version, generates bed files instead of bedgraphs
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


# Create FASTA
fasta_records = []
for patient_id, group in df.groupby('PatientID'):
    seq_length = group['Position'].max()
    sequence = 'A' * seq_length
    record = SeqRecord(Seq(sequence), id=str(patient_id), description="")
    fasta_records.append(record)
SeqIO.write(fasta_records, 'patients.fasta', 'fasta')



label_colors = {}
for label in df['Label'].unique():
    label_colors[label] = f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

# Remove and recreate the output directory
if os.path.exists("beds_by_label"):
    shutil.rmtree("beds_by_label")
os.makedirs("beds_by_label", exist_ok=True)

for label in df['Label'].unique():
    color = label_colors.get(label, "#000000").lstrip("#")
    r, g, b = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))

    with open(f"beds_by_label/{label}.bed", "w") as bed_file:
        bed_file.write('track name="{0}" description="{0}" visibility=2 itemRgb="On"\n'.format(label))

        for _, row in df[df['Label'] == label].iterrows():
            chrom = row['PatientID']
            start = int(row['Position']) - 1
            end = int(row['Position'])
            try:
                value = float(row['Value'])
                score = max(0, min(int(value), 1000))
            except:
                score = 1
            strand = "+"
            date_str = row['Date'].strftime('%Y-%m-%d')
            name = f"{label}_{date_str}"
            bed_file.write(f"{chrom}\t{start}\t{end}\t{name}\t{score}\t{strand}\t{start}\t{end}\t{r},{g},{b}\n")


with open("patients.fasta") as fasta_file, open("patients.fasta.fai", "w") as index_file:
    for record in SeqIO.parse(fasta_file, "fasta"):
        seq_len = len(record.seq)
        index_file.write(f"{record.id}\t{seq_len}\t0\t{seq_len}\t{seq_len}\n")