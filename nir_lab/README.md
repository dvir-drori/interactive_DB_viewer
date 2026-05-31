# NIR Lab — Transplant Patient Timeline Viewer

A config-driven, interactive clinical timeline viewer for transplant patients.
Visualize lab results, biopsy events, and epigenetic (H3K4me3) data across
hundreds of patients — all in a single static HTML page deployed on GitHub Pages.

**Live site:** [https://dvir-drori.github.io/interactive_DB_viewer/](https://dvir-drori.github.io/interactive_DB_viewer/)

---

## Features

### Patient Navigation
- **221 transplant patients** loaded from `config.json`
- Dropdown selector with patient ID
- Metadata display: organ type, birth year, transplant date
- Day 0 = transplant date, shown as a dashed vertical line on all charts

### Track System (26 built-in tracks)
- **22 Lab Data tracks** — ALT, AST, Creatinine, WBC, HGB, Platelets, and more
- **1 Biopsy track** — discrete events rendered as diamond markers
- **3 Epigenetic tracks** — H3K4me3 ChIP-seq enrichment levels (1/3, 2/3, 3/3)
- Each track has its own subplot with labeled y-axis and units

### Sidebar Controls
- Grouped by category (Lab Data, Biopsies, Epigenetic, Uploaded)
- Per-category toggle (enable/disable all tracks in a category)
- Collapsible category sections
- **All / None** buttons for quick selection
- Per-track controls:
  - Enable/disable checkbox
  - Color picker (unique color per track by default)
  - Display type dropdown: Line+Dot, Dots, Bars, Area, Step
  - Drag handle for reordering

### Display Types
| Type | Plotly Mode | Description |
|---|---|---|
| Line+Dot | `lines+markers` | Default — connected line with data point markers |
| Dots | `markers` | Scatter plot, no connecting lines |
| Bars | `bar` | Vertical bar chart |
| Area | `fill: tozeroy` | Filled area under the curve |
| Step | `line.shape: hv` | Stepped line (horizontal-then-vertical) |

Event tracks (Biopsies) always render as diamond markers regardless of setting.

### Overlay System
Merge multiple continuous tracks into a single shared subplot for comparison:

1. Hover over tracks in the sidebar to reveal the **ovl** checkbox
2. Check 2 or more continuous tracks
3. Click **Create Overlay** at the bottom of the sidebar
4. Tracks merge into one subplot with a shared y-axis and legend
5. Each track keeps its own color
6. Click the **x** on an overlay group to split it, or **Split All** to undo all overlays

### Date Range Filter
- **From / To** date inputs in the toolbar
- Converts calendar dates to day offsets relative to transplant
- **Apply** to filter, **Reset** to show full range

### Scroll Mode
- **Zoom** (default) — mouse wheel zooms the x-axis
- **Pan** — mouse wheel scrolls horizontally through the timeline

### Drag-to-Reorder
- Drag tracks via the **&#9776;** handle in the sidebar
- Both sidebar order and chart subplot order update immediately

### File Upload (Client-Side)
All uploads run entirely in the browser — no server required.

#### bedGraph Upload
- Click **+ bedGraph** in the toolbar or drag-and-drop `.bedGraph`/`.bg` files onto the chart area
- Files are parsed in-browser and added under an **Uploaded** category
- Each uploaded track gets a **LOCAL** badge
- Remove individual uploaded tracks with the **x** button

#### CSV Upload
- Click **+ CSV** or drag-and-drop a `.csv` file
- Uses [PapaParse](https://www.papaparse.com/) for client-side parsing
- Expected columns: `PatientID`, `Date`, `Label`, `Value`
- Date formats supported: `DD/MM/YYYY` and ISO `YYYY-MM-DD`
- New patients appear in the dropdown (with `(uploaded)` suffix if they don't already exist)
- Tracks are grouped by `Label` under the **Uploaded** section
- Reference date for new patients = their earliest recorded date

#### Drag-and-Drop
- Drag any `.bedGraph`, `.bg`, or `.csv` file onto the chart area
- A blue overlay zone appears to indicate the drop target
- Mixed drops supported (bedGraph + CSV in the same drop)

### Session Persistence
- State is **auto-saved** to `localStorage` on every change
- On reload, the session is restored with a toast notification
- **Save** button exports the full session as a downloadable JSON file
- **Load** button imports a previously exported session
- Saved state includes: selected patient, track order, enabled tracks, colors, display types, overlay groups, date range, scroll mode, and uploaded data
- Uploaded data is included if total size is under 5 MB

### Hover Tooltips
- Continuous tracks: track name, day offset, calendar date, value with units
- Event tracks: track name, day offset, calendar date

---

## Project Structure

```
nir_lab/
├── docs/                          GitHub Pages deployment
│   ├── index.html                 Single-file viewer application (~2100 lines)
│   ├── config.json                Patient + track configuration (generated)
│   ├── bedgraphs_by_label/        26 bedGraph data files
│   │   ├── ALANINE.AM.TRAN (ALT).bedGraph
│   │   ├── CREATININE.bedGraph
│   │   ├── Biopsy_value-0.1_number-1_of_1.bedGraph
│   │   ├── H3K4me3_value-1_number-1_of_3.bedGraph
│   │   └── ...
│   ├── patients.fasta.fai         Patient index (legacy, used for patient list)
│   └── .nojekyll                  Disables Jekyll processing on GitHub Pages
│
├── nir_lab/                       Full-stack application (React + FastAPI)
│   ├── backend/                   FastAPI server with SQLite database
│   │   ├── main.py                API endpoints
│   │   ├── models.py              SQLAlchemy ORM models
│   │   ├── database.py            Database connection
│   │   └── pipeline/              CSV ingestion and bedGraph export
│   ├── frontend/                  React + Vite + Tailwind frontend
│   │   ├── src/pages/             PatientList, PatientView, CompareView, etc.
│   │   └── src/components/        TimelineChart, TrackSelector, NotesPanel
│   ├── setup.bat                  Windows installation script
│   └── start_server.bat           Windows server launcher
│
├── forConfig.py                   Generates docs/config.json from source data
├── transplant_dates.csv           Patient metadata (not committed)
├── FilesGenerator-bedgraph.py     Original standalone pipeline script
└── README.md
```

---

## CDN Dependencies

The viewer loads these libraries from CDN (no build step required):

| Library | Version | Purpose |
|---|---|---|
| [Plotly.js](https://plotly.com/javascript/) | 2.35.0 | Interactive charts and subplots |
| [PapaParse](https://www.papaparse.com/) | 5.4.1 | Client-side CSV parsing for upload |
| [IBM Plex Mono](https://fonts.google.com/specimen/IBM+Plex+Mono) | — | Monospace font for data display |
| [Syne](https://fonts.google.com/specimen/Syne) | — | Heading font |

---

## Data Format

### config.json

Generated by `forConfig.py`. Defines patients, tracks, and categories:

```json
{
  "patients": [
    {
      "id": "TRN0818",
      "referenceDate": "2017-11-15",
      "referenceLabel": "Transplant",
      "metadata": { "organ": "liver", "birthYear": "1974" }
    }
  ],
  "tracks": [
    {
      "name": "ALANINE.AM.TRAN (ALT)",
      "file": "ALANINE.AM.TRAN (ALT).bedGraph",
      "category": "Lab Data",
      "unit": "U/L"
    }
  ],
  "categories": {
    "Lab Data":   { "type": "continuous", "color": "#4f8ef7" },
    "Biopsies":   { "type": "event",      "color": "#f59e0b" },
    "Epigenetic": { "type": "continuous", "color": "#7c3aed" }
  }
}
```

### bedGraph Files

Standard [bedGraph format](https://genome.ucsc.edu/goldenPath/help/bedgraph.html) repurposed for timeline data:

```
track type=bedGraph name="CREATININE" description="CREATININE" ...
TRN0818    42    43    1.2
TRN0818    85    86    1.1
TRN0590    10    11    0.9
```

| Column | Meaning |
|---|---|
| 1 | Patient ID (chromosome name in bedGraph terms) |
| 2 | Day offset start |
| 3 | Day offset end (start + 1) |
| 4 | Measured value |

### CSV Upload Format

For uploading new data via the browser:

| Column | Required | Description | Example |
|---|---|---|---|
| `PatientID` | Yes | Patient identifier | `TRN0818` |
| `Date` | Yes | Measurement date (DD/MM/YYYY or YYYY-MM-DD) | `15/11/2017` |
| `Label` | Yes | Measurement name (becomes track name) | `CREATININE` |
| `Value` | Yes | Numeric value | `1.2` |

---

## Regenerating config.json

When the source data changes (new patients or tracks):

```bash
cd /path/to/nir_lab
python forConfig.py
```

This reads `transplant_dates.csv` and scans `bedgraphs_by_label/` to produce `docs/config.json`.

**Source data:**
- `transplant_dates.csv` — no header; columns: PatientID, birthYear, organ, transplantDate (DD/MM/YYYY)
- `bedgraphs_by_label/` — one `.bedGraph` file per measurement label

**Track classification:**
| Filename pattern | Category | Track name |
|---|---|---|
| `Biopsy*` | Biopsies (event) | "Biopsy" |
| `H3K4me3*` | Epigenetic (continuous) | "H3K4me3 (N/M)" |
| Everything else | Lab Data (continuous) | Filename without `.bedGraph` |

**Unit mapping:** Common lab names are automatically mapped to units (ALT -> U/L, Creatinine -> mg/dL, HGB -> g/dL, etc.).

Patients with empty transplant dates are skipped (~165 of 386 rows).

---

## Deployment

### GitHub Pages (current)

The site is deployed automatically from the `docs/` folder on the `main` branch.

To update the deployed site:
1. Make changes to `docs/index.html` or regenerate `docs/config.json`
2. Commit and push to `main`
3. GitHub Pages rebuilds within 1-2 minutes

### Local Development

To test locally before deploying:

```bash
cd /path/to/nir_lab
python -m http.server 8000 -d docs
# Open http://localhost:8000
```

### Full-Stack Application

The `nir_lab/` subdirectory contains a separate full-stack version with a FastAPI backend
and React frontend. See the installation instructions in that directory for details on
running the server-based version with database support, clinical notes, and API access.

---

## Architecture

### Single-File Design

The entire viewer is a single `index.html` file with inline CSS and JavaScript.
This design choice enables:
- Zero build step — edit and deploy directly
- GitHub Pages hosting with no CI/CD pipeline
- Easy distribution — share one file
- Offline capability — works without internet after first load (libraries are cached)

### State Management

A central `state` object tracks all UI state:

```
state = {
  config              // from config.json (immutable after load)
  selectedPatientId   // current patient
  trackOrder          // array of track indices defining display order
  trackEnabled        // { idx: bool } — which tracks are visible
  trackColors         // { idx: '#hex' } — per-track color overrides
  trackDisplayTypes   // { idx: 'lines+markers'|'markers'|'bar'|'area'|'step' }
  overlayGroups       // [[idx, idx], ...] — groups of merged tracks
  dateRange           // { from: date, to: date } — x-axis filter
  scrollMode          // 'zoom' | 'pan'
  bedGraphCache       // { filename: [{patientId, day, value}] } — runtime only
  uploadedTracks      // in-browser uploaded track data
  uploadedPatients    // patients from CSV upload
}
```

State is auto-persisted to `localStorage` and can be exported/imported as JSON.

### Chart Rendering

Each render cycle:
1. Collects enabled tracks, separating continuous, event, and overlay groups
2. Fetches uncached bedGraph files via `fetch()`
3. Filters data for the selected patient and date range
4. Builds Plotly traces with per-track display type and color
5. Computes subplot domains (150px per continuous track, 80px per event row)
6. Renders with `Plotly.newPlot()` for clean subplot structure updates

---

## Track Units Reference

| Track | Unit |
|---|---|
| ALT, AST, ALK. PHOS., GGTP, LDH, DIASTASE | U/L |
| CREATININE, UREA, T.BILIRUBIN | mg/dL |
| ALBUMIN, HGB | g/dL |
| GLUCOSE | mg/dL |
| BILE ACIDS | umol/L |
| SODIUM, POTASSIUM | mEq/L |
| WBC, PLATELETS, NEUTROPHILE, LYMPHOCYTE | K/uL |
| CMV-PCR, EBV-PCR | copies/mL |
| INR | (dimensionless) |

---

## Privacy Note

- The bedGraph data files committed to this repository contain **de-identified patient IDs** (TRN0xxx format)
- No names, dates of birth, or other directly identifying information is included in the deployed data
- The `transplant_dates.csv` source file is **not committed** (excluded by `.gitignore`)
- Uploaded data via the browser stays in the user's browser (`localStorage`) and is never sent to any server

---

## License

Internal use — NIR Lab, Hebrew University / Hadassah Medical Center.
