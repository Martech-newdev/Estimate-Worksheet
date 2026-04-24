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
- A customer suggestion dropdown: the Customer field on both tabs offers a
  datalist of customers seen in the saved worksheet library (most-recent
  first). Picking or typing an exact match auto-fills any blank Address Line
  1 / City-State-Zip / Contact / Contact Email from the most recent saved
  worksheet for that customer. Existing non-blank fields are never
  overwritten. Defaults dialog Customer continues to pre-fill new
  worksheets independently.

## Storage

- `localStorage["martech_worksheet_v1"]` — auto-saved snapshot of the
  currently-open (active) worksheet. Restored on page load.
- `localStorage["martech_worksheets_v1"]` — named worksheet library:
  `{ current: name|null, items: { name: { data, savedAt } } }`. Updated
  explicitly via the picker's Save / Save As / Delete buttons. Switching to a
  saved worksheet asks for confirmation if the active worksheet has unsaved
  changes relative to its baseline.
- `localStorage["martech_defaults_v1"]` — saved default values for the
  Estimator, Contact, Contact Email, Address Line 1, City/State/Zip,
  Default Markup, Customer, and Project Name meta fields, plus a
  `today_dates` toggle (pre-fills Quote Date / Date In with today's
  date), a `jobnum_tpl` template for Job Number (supports `{YYYY}`,
  `{YY}`, `{MM}`, `{DD}` date tokens and `{####}` for an
  auto-incrementing counter), and a `due_offset_days` integer that
  pre-fills Due Date as today + N days. Edited via the "Defaults..."
  button. Pre-fill on first load (when no auto-saved data exists) and
  after Clear Form on the active tab. Per-worksheet edits to those
  fields do not change the saved defaults. The Defaults dialog also
  shows a live read-only preview of the resolved Job Number under the
  template field, computed from the current template and the current
  "Next counter value" (today's date for date tokens). The preview
  never consumes the persisted counter and hides itself when the
  template is empty.
- `localStorage["martech_defaults_counter_v1"]` — integer counter
  consumed by the `{####}` token in the Job Number template. Increments
  each time a worksheet is pre-filled with a templated job number. The
  next value is shown and editable in the Defaults dialog; cleared to 1
  by Clear Defaults.

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
