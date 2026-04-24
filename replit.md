# Job Estimate Worksheet

A static web application for generating job estimates for MarTech (Mechanical Analysis and Repair) based in Lodi, CA.

## Overview

Single-page tool for creating professional job estimates with:
- 1-page version (18 rows) and 2-page version (63 rows)
- Real-time labor and material cost calculations
- Customizable markup rates
- Print-ready layout for PDF export or physical printing
- A worksheet library: save the current worksheet under a name and switch
  between saved jobs without losing in-progress work. Browser auto-save still
  protects the unsaved active worksheet between visits.

## Storage

- `localStorage["martech_worksheet_v1"]` — auto-saved snapshot of the
  currently-open (active) worksheet. Restored on page load.
- `localStorage["martech_worksheets_v1"]` — named worksheet library:
  `{ current: name|null, items: { name: { data, savedAt } } }`. Updated
  explicitly via the picker's Save / Save As / Delete buttons. Switching to a
  saved worksheet asks for confirmation if the active worksheet has unsaved
  changes relative to its baseline.
- `localStorage["martech_defaults_v1"]` — saved default values for the
  Estimator, Contact, Contact Email, Address Line 1, City/State/Zip, and
  Default Markup meta fields, plus a `today_dates` toggle that pre-fills
  Quote Date / Date In with today's date. Edited via the "Defaults..."
  button. Pre-fill on first load (when no auto-saved data exists) and after
  Clear Form on the active tab. Per-worksheet edits to those fields do not
  change the saved defaults.

## Tech Stack

- **Frontend:** Pure HTML5, CSS3, vanilla JavaScript (no frameworks or build tools)
- **Fonts:** Barlow and Barlow Condensed via Google Fonts CDN
- **Single file:** `index.html` contains all HTML, CSS, and JS

## Running the App

The app is served via Python's built-in HTTP server:

```
python3 -m http.server 5000
```

## Project Structure

```
index.html    # Entire application (HTML + CSS + JS)
replit.md     # This file
```

## Deployment

Configured as a static site deployment with `publicDir: "."`.
