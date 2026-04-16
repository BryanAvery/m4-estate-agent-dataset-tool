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
