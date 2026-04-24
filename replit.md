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
  the suggestion list directly: each customer row shows its current name,
  address, contact, and how many saved worksheets reference it. The
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
  template is empty. The Due Date Offset field has a matching live
  read-only preview underneath it showing the resolved MM/DD/YYYY
  date (today + N days); it hides when the offset is empty/invalid.
- `localStorage["martech_defaults_counter_v1"]` — integer counter
  consumed by the `{####}` token in the Job Number template. Increments
  each time a worksheet is pre-filled with a templated job number. The
  next value is shown and editable in the Defaults dialog; cleared to 1
  by Clear Defaults.
- `localStorage["martech_imported_customers_v1"]` — JSON array of
  customers seeded via the Customers dialog's "Import Customers..."
  action: `[{ name, addr1, addr2, contact, contact_email, importedAt }, ...]`.
  Read alongside the worksheet-derived customers to populate the
  Customer suggestion dropdown and the Customers dialog. Names are
  case-insensitive unique; running the import again with the same name
  fills only blank fields (existing values are never overwritten).
  Editing/Merging/Deleting from the Customers dialog keeps this store
  in sync.
- `localStorage["martech_customer_exclusions_v1"]` — JSON array of
  lowercase customer names hidden from the Customer suggestion dropdown
  via the Customers dialog's Delete action. The Customers dialog still
  shows hidden entries (with a Restore button) as long as a saved
  worksheet still references them. Saving a worksheet whose Customer
  field matches an excluded name removes that name from the exclusion
  list automatically.

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
