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
- A "Customers..." dialog (next to "Defaults..." on both tabs) for managing
  the suggestion list directly. A search/filter input at the top of the
  dialog narrows the visible rows in real time as the user types
  (case-insensitive match against the customer name and against the job
  number / project name / saved-worksheet name of any of the customer's
  worksheets); a "Clear" button and a "X of Y shown" count appear while
  the filter is active. Hidden customers are still searchable so they can
  be Restored, and an empty result shows a "no customers match" message.
  Each customer row shows its current name, address, contact, and how
  many saved worksheets reference it. The
  "Used in N saved worksheets" line is itself an expand toggle — clicking
  it reveals a list of those worksheets (job number, worksheet name,
  project name, relative save date, with the currently-loaded one tagged).
  Clicking a worksheet entry loads it (same dirty-prompt as the picker)
  and closes the dialog; the list is also shown for hidden customers so
  old worksheets can be cleaned up before un-hiding. Imported customers
  (see below) also appear here with a "Used in 0 saved worksheets" count
  until a worksheet references them. Each row supports
  Edit (rename + update the four contact fields across every matching
  saved worksheet, with merge confirmation when renaming into an existing
  customer), Merge (renames the customer to a chosen target across every
  matching saved worksheet, leaving each worksheet's address/contact
  untouched), and Delete (hides the customer from the suggestion dropdown
  via an exclusions list, with an optional checkbox to also wipe the name
  and contact info from every saved worksheet that uses it). Hidden
  customers stay visible in the dialog with a Restore button. Saving a
  worksheet whose Customer field matches an excluded name automatically
  un-excludes it. All edits update the dropdown and the active form
  immediately without a reload.
- An "Import Customers..." action inside the Customers dialog seeds the
  dropdown from a pasted list or a small CSV/TSV file. Expected columns
  (in order, or via a header row) are Name, Address Line 1,
  City/State/Zip, Contact, Contact Email. Tab vs. comma is auto-detected,
  quoted fields are supported, and lines starting with `#` are skipped.
  A live preview tags each row as New, Merge (case-insensitive name match
  with an existing customer fills only blank fields, never overwrites),
  or Skip (rows missing a name). Imported customers persist in their own
  localStorage key and the dropdown picks them up immediately. Edit /
  Merge / Delete on an imported customer keep the imported store in sync
  (rename re-keys the imported entry; merge drops the source imported
  entry; delete with the "also clear" checkbox permanently removes it).

## Storage

Storage is split into two layers:

**Per-user (browser localStorage)** — survives only on the same browser/profile:

- `localStorage["martech_worksheet_v1"]` — auto-saved snapshot of the
  currently-open (active) worksheet. Restored on page load.
- `localStorage["martech_worksheets_v1"]` — named worksheet library:
  `{ current: name|null, items: { name: { data, savedAt } } }`. Updated
  explicitly via the picker's Save / Save As / Delete buttons. Switching to a
  saved worksheet asks for confirmation if the active worksheet has unsaved
  changes relative to its baseline.

**Shared across all site visitors (Postgres `shared_kv` table, served via
`/api/store/<key>`)** — every visitor sees the same data:

- `defaults` — saved default values for the Estimator, Contact, Contact
  Email, Address Line 1, City/State/Zip, Default Markup, Customer, and
  Project Name meta fields, plus the `today_dates` toggle, the
  `jobnum_tpl` Job Number template (`{YYYY}`/`{YY}`/`{MM}`/`{DD}`/`{####}`
  tokens), and the `due_offset_days` integer (pre-fills Due Date as
  today + N days). Edited via the "Defaults..." button.
- `defaults_counter` — integer counter consumed by the `{####}` token in
  the Job Number template. Increments each time a worksheet is
  pre-filled with a templated job number.
- `imported_customers` — JSON array of customers seeded via the
  Customers dialog's "Import Customers..." action:
  `[{ name, addr1, addr2, contact, contact_email, importedAt }, ...]`.
- `customer_exclusions` — JSON array of lowercase customer names hidden
  from the Customer suggestion dropdown.

Reads of these four shared keys come from an in-memory cache populated
once at page load (`_sharedFetchAll()` issues a single `GET /api/store`
before `_initApp()` runs). Writes are fire-and-forget `PUT /api/store/<key>`
calls so the UI stays snappy; the cache is updated synchronously so the
calling code sees the new value immediately.

The legacy `localStorage["martech_defaults_v1"]`,
`martech_defaults_counter_v1`, `martech_imported_customers_v1`, and
`martech_customer_exclusions_v1` keys are no longer read or written by
the app — any old values left in a user's browser are silently ignored.

## Word Quote Generation

The "Generate Word Quote" button builds a `.docx` from the active worksheet
using the `docx@8` UMD library loaded from CDN. The generated document uses
real Word page-level decorations:

- **Page header** (repeats on every page): MarTech logo image, embedded from
  `assets/martech-logo.png` via `fetch()` + `D.ImageRun`.
- **Page footer** (repeats on every page): two-column company info layout
  with the street address + tel/fax line, the email + website line, and a
  centered "Contactor License: 684442" line, separated from the body by a
  thin top divider rule.
- **Body closing**: "Thank you for the opportunity…" plus the Ron Stephens
  signature block (name, title, email, main + cell phone).

Scope of Services items are renumbered sequentially (`1.0`, `2.0`, `3.0`, …)
in the order they appear on the worksheet, regardless of which worksheet
row they came from. Free labor rows are included when the description is
filled or hours are entered; fixed overhead rows (MOBILIZATION / DEMOB,
PROJECT MANAGEMENT, etc.) are included when hours or rate is entered.

The Attention line renders as `Name | email`, with the email as a clickable
`mailto:` hyperlink when both Contact and Contact Email are filled.

## Tech Stack

- **Frontend:** Pure HTML5, CSS3, vanilla JavaScript (no frameworks or build tools)
- **Fonts:** Barlow and Barlow Condensed via Google Fonts CDN
- **Single file:** `index.html` contains all HTML, CSS, and JS
- **Backend:** Flask (Python) + psycopg2 with a small `SimpleConnectionPool`
  pointed at the Replit-managed Postgres (`DATABASE_URL`).

## Running the App

The app is served by `server.py` (Flask, port 5000):

```
python3 server.py
```

The same process serves `index.html`, the `assets/` and
`attached_assets/` folders, and the JSON API for shared storage. All
HTML/JS responses are sent with `Cache-Control: no-store` so visitors
always get the latest deployed version.

## API

- `GET  /api/store` — returns all four shared keys
  (`defaults`, `defaults_counter`, `imported_customers`,
  `customer_exclusions`) in one response. Used by `_sharedFetchAll()` at
  page load.
- `GET  /api/store/<key>` — returns a single shared key.
- `PUT  /api/store/<key>` body `{"value": <json>}` — upserts the value.

The backing table is `shared_kv (key TEXT PRIMARY KEY, value JSONB,
updated_at TIMESTAMPTZ)`.

## Project Structure

```
index.html         # Entire frontend (HTML + CSS + JS)
server.py          # Flask backend: static files + /api/store
assets/            # Logo + other static assets
attached_assets/   # Reference docs, sample CSV, etc.
replit.md          # This file
```

## Deployment

The app now has a backend and a database, so the deployment target must
be **Reserved VM** or **Autoscale** (NOT Static). When publishing, pick
an "Autoscale" deployment with run command `python3 server.py` and the
existing `DATABASE_URL` secret will be inherited automatically.
