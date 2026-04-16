# M4 Estate Agent Dataset Tool

A lightweight single-page app for building a clean, structured dataset of estate agents along the M4 corridor.

## Features

- Add, edit, and delete estate agent records.
- Store data in browser `localStorage` (offline after first load).
- Sort and filter by town, service, status, and search terms.
- Duplicate detection based on business name + location + postcode + website.
- Data quality summary (record count, duplicates, missing contact fields).
- CSV export for Excel/Google Sheets/CRM imports.
- CSV import (supports records exported by this app).
- Editable target town list.
- Built-in M4 town JSON prompt generator.
- Optional direct OpenAI API call from browser to generate and import towns.

## Record fields

- Business name
- Location
- Postcode
- Phone
- Email
- Website
- Services (multi-select)
- Notes
- Research (AI enrichment result payload)
- Source URL
- Date captured
- Status

## Status workflow

- New
- Reviewed
- Contacted
- Follow-up
- Not suitable

## Tech stack

- HTML
- CSS
- Vanilla JavaScript (no frameworks)

## Local development

Open `index.html` directly in your browser, or use a simple static server:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Deploy to GitHub Pages

1. Push this repository to GitHub.
2. In repository settings, enable **Pages** and choose deployment from branch.
3. Select your default branch and root (`/`) folder.
4. Save and wait for deployment.


## Deploy backend API to Render (FastAPI)

This repo now includes a Render-ready FastAPI app:

- `app.py` - Render web API entrypoint
- `requirements.txt` - Python dependencies for Render builds
- `start.sh` - starts Uvicorn on Render's `PORT`

### Render setup

1. Create a **Web Service** in Render from this repository.
2. Use these commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
3. Set any required environment variables (for example `GOOGLE_MAPS_API_KEY`).
4. Deploy and test: `https://m4-automation-api.onrender.com/`

### Render Blueprint (recommended)

This repository includes a `render.yaml` blueprint so Render can be configured
from code and re-created consistently.

1. In Render, choose **New +** → **Blueprint**.
2. Select this repository/branch.
3. Confirm the generated web service settings:
   - Name: `m4-automation-api`
   - Region: `Ohio (US East)`
   - Build command: `pip install -r requirements.txt`
   - Start command: `bash start.sh`
   - Health check path: `/`
4. Add secret values when prompted:
   - `GOOGLE_MAPS_API_KEY` (required for Google Maps pulls)
   - `OPENAI_API_KEY` (required for AI enrichment endpoint)

### Connect GitHub Pages frontend to Render API

In `index.html`, set your deployed API endpoint before `app.js` loads:

```html
<script>
  window.M4_AUTOMATION_API_URL = "https://m4-automation-api.onrender.com/api/automation/run";
  window.M4_AI_ENRICHMENT_API_URL = "https://m4-automation-api.onrender.com/api/ai/enrich-record";
</script>
<script src="app.js"></script>
```

If you do not set this variable, the app defaults to the local bridge URL:
`http://localhost:8787/api/automation/run`.

For AI enrichment, the default endpoint is:
`https://m4-automation-api.onrender.com/api/ai/enrich-record`.

## AI record enrichment (single-row, structured JSON)

- Use the **AI Record Research** card to configure model/API key.
- Click **AI research** in any dataset row action to enrich one record at a time.
- The backend endpoint `/api/ai/enrich-record` returns strict JSON suitable for DB fields:
  - `business_name_cleaned`
  - `business_type`
  - `services_offered`
  - `business_summary`
  - `outreach_relevance`
  - `outreach_reason`
  - `manual_research_needed`
  - `ai_confidence`
  - `ai_generated`

The frontend stores this under `record.aiResearch` and tracks:
- `aiGenerated`
- `aiConfidence`
- `aiLastEnrichedAt`

## Data storage and privacy

- All records are stored locally in the browser (`localStorage`).
- No backend or external data sharing is used by default.
- OpenAI API keys entered in the UI are used only for the immediate request and are not persisted in `localStorage` or cookies.

## Limitations

- Data is device/browser specific unless exported.
- `localStorage` capacity is limited (typically ~5–10MB depending on browser).
- CSV import expects compatible headers for best results.
- Duplicate detection is simple and heuristic-based.

## Future roadmap

- Stronger duplicate scoring and matching.
- Bulk status updates.
- Import mapping UI for arbitrary CSVs.
- Optional backend sync and multi-user support.
- CRM integrations and enrichment pipeline.

## Automation layer (Google Maps + Rightmove)

A lightweight Python automation layer is included to help seed your dataset from:

- Google Maps Places Text Search API
- Rightmove search result pages

### Files

- `run_automation.py` - CLI entrypoint
- `automation_api.py` - local HTTP bridge for the web UI automation button
- `automation_layer/service.py` - orchestration + dedupe + CSV writer
- `automation_layer/providers/google_maps.py` - Google Maps pull
- `automation_layer/providers/rightmove.py` - Rightmove pull

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4
```

Set Google API key (required for `--town`):

```bash
export GOOGLE_MAPS_API_KEY="your_key_here"
```

### Example usage

```bash
python run_automation.py \
  --town Reading \
  --town Slough \
  --rightmove-url "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E87490" \
  --output outputs/m4_seed.csv
```

### Notes

- Respect source terms of service, robots rules, and API usage limits.
- Rightmove parsing is best-effort and may need adjustment if page structure changes.
- Records are deduplicated by `(business_name, location)`.

## Running automation from the web page button

The web UI can call the Python automation layer through a small local API bridge.

1. Start the static app:

```bash
python -m http.server 8080
```

2. In a second terminal, start the automation API:

```bash
python automation_api.py
```

3. Open `http://localhost:8080`, use **Automation Layer Runner**, and click
   **Run automation + import**.

The browser calls `http://localhost:8787/api/automation/run`, receives records,
and appends them to the local Dataset table.
