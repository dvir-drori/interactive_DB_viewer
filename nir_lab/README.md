# NIR Lab — Transplant Patient Clinical Timeline Platform

A full-stack web application for visualizing longitudinal clinical and epigenomic data
from transplant patients. Built for the NIR Lab (ChIP-seq diagnostics).

---

## Overview

The platform replaces a previous IGV-web proof-of-concept with a purpose-built clinical
interface. It provides:

- **Patient list** — overview table of all patients with follow-up duration and measurement count
- **Patient timeline** — interactive multi-track chart (lab values, clinical events, ChIP-seq heatmap)
- **Multi-patient comparison** — overlay any label across 2–4 patients aligned to Day 1
- **CSV upload** — drag-and-drop ingestion of new patient data
- **Clinical notes** — free-text annotations attached to specific days, stored in database
- **IGV viewer** — original IGV-web interface preserved as an advanced tab

---

## Project Structure

```
nir_lab/
├── backend/
│   ├── main.py              FastAPI application and all API endpoints
│   ├── models.py            SQLAlchemy database models
│   ├── database.py          SQLite connection setup
│   ├── pipeline/
│   │   ├── processor.py     CSV ingestion logic (refactored from original script)
│   │   └── export.py        Database → bedGraph/FASTA/GFF export
│   ├── requirements.txt     Python dependencies
│   └── nir_lab.db           SQLite database (created automatically on first run)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx           Router and top navigation
│   │   ├── pages/
│   │   │   ├── PatientList.jsx   Patient overview table
│   │   │   ├── PatientView.jsx   Single-patient drill-down
│   │   │   ├── CompareView.jsx   Multi-patient comparison
│   │   │   ├── UploadPage.jsx    CSV upload interface
│   │   │   └── IGVView.jsx       IGV embedded viewer
│   │   └── components/
│   │       ├── TimelineChart.jsx   Plotly multi-track timeline
│   │       ├── ChipSeqTrack.jsx    ChIP-seq heatmap (H3K4me3)
│   │       ├── TrackSelector.jsx   Track toggle sidebar
│   │       └── NotesPanel.jsx      Clinical notes sidebar
│   ├── package.json
│   └── vite.config.js
│
├── FilesGenerator-bedgraph.py   Original pipeline script (standalone, preserved)
├── setup.bat                    One-time installation script (Windows)
├── start_server.bat             Server launcher (double-click to start)
└── README.md                    This file
```

---

## Installation (Windows Server)

### Prerequisites

Install these once on the server machine:

| Software | Download | Version |
|---|---|---|
| Python | https://python.org | 3.11 or newer |
| Node.js | https://nodejs.org | 20 LTS |

During Python installation, check **"Add Python to PATH"**.

### First-time setup

1. Copy the `nir_lab` folder to `C:\Dvir\nir_lab` (or any location)
2. Double-click **`setup.bat`**
3. Wait for all packages to install and the frontend to build (~2–3 minutes)
4. You should see: `Setup complete!`

### Starting the server

Double-click **`start_server.bat`**

The platform will be available at:
- `http://localhost:8000` — from the server machine
- `http://<server-ip>:8000` — from any computer on the lab network

To find your server IP: open Command Prompt and run `ipconfig`. Look for "IPv4 Address".

---

## Optional: Run as a Windows Service (auto-start on boot)

Install NSSM (Non-Sucking Service Manager):
1. Download from https://nssm.cc/download
2. Extract and open Command Prompt as Administrator in the nssm folder
3. Run: `nssm install NIRLabServer`
4. Set:
   - **Path**: `C:\Dvir\nir_lab\backend\venv\Scripts\uvicorn.exe`
   - **Arguments**: `main:app --host 0.0.0.0 --port 8000`
   - **Startup directory**: `C:\Dvir\nir_lab\backend`
5. Click **Install service**
6. Run: `nssm start NIRLabServer`

The server will now start automatically every time Windows boots.

---

## Data Format

### CSV upload format

Your CSV must have exactly these columns (names are case-sensitive):

| Column | Description | Example |
|---|---|---|
| `PatientID` | Unique patient identifier | `P001` |
| `Date` | Date of measurement | `2023-05-14` |
| `Label` | Name of the measured parameter | `CREATININE` |
| `Value` | Numeric or categorical value | `1.2` |
| `Category` | One of three values (see below) | `Lab Data` |

**Valid Category values:**
- `Lab Data` — continuous numeric measurements (blood tests, enzymes, etc.)
- `Biopsies` — discrete biopsy events with categorical result
- `Plasma Samples` — plasma sampling events, including ChIP-seq readouts (H3K4me3)

**Timeline anchor:** Day 1 = the earliest recorded date for each patient.
All chart x-axes show "days since Day 1".

### ChIP-seq values (H3K4me3 and similar)

For ChIP-seq labels in the `Plasma Samples` category, use numeric enrichment levels:
- `1` = Low enrichment (detected)
- `2` = Moderate enrichment
- `3` = High enrichment

These are displayed as a color heatmap in the patient timeline view.

---

## Using the Original Pipeline Script

`FilesGenerator-bedgraph.py` is preserved for generating IGV static files directly:

```bash
# Rename your CSV to Transplant-data.csv (or edit the INPUT_CSV variable)
python FilesGenerator-bedgraph.py
```

This generates `patients.fasta`, `patients.fasta.fai`, `bedgraphs_by_label/`, and
`annotations.gff` — which can be uploaded to the IGV-web GitHub repository as before.

---

## API Reference

The backend exposes a REST API at `http://<server>:8000/api/`.
Interactive documentation is available at `http://<server>:8000/docs`.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| POST | `/api/upload` | Upload and ingest a CSV file |
| GET | `/api/patients` | List all patients |
| GET | `/api/patients/{id}/summary` | Patient metadata + available labels |
| GET | `/api/patients/{id}/measurements` | Time-series data (filterable by label) |
| GET | `/api/patients/{id}/events` | Biopsy + Plasma Sample events |
| GET | `/api/patients/{id}/notes` | Clinical notes for a patient |
| POST | `/api/patients/{id}/notes` | Add a clinical note |
| DELETE | `/api/notes/{id}` | Delete a note |
| GET | `/api/compare` | Multi-patient comparison data |
| POST | `/api/export` | Re-generate IGV static files from DB |

---

## Development

To run in development mode with hot reload:

```bash
# Terminal 1 — backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Frontend runs on `http://localhost:5173` and proxies `/api` calls to port 8000.

---

## Notes on Patient Data Privacy

- The database (`nir_lab.db`) is stored locally on the server and never leaves the lab network.
- No authentication is implemented — all users on the LAN can access all data.
- If patient identifiers are sensitive, ensure the server is not accessible outside the lab network (firewall the port).
- The GitHub repository contains **no patient data** — only source code.
