# Job Estimate Worksheet

A static web application for generating job estimates for MarTech (Mechanical Analysis and Repair) based in Lodi, CA.

## Overview

Single-page tool for creating professional job estimates with:
- 1-page version (18 rows) and 2-page version (63 rows)
- Real-time labor and material cost calculations
- Customizable markup rates
- Print-ready layout for PDF export or physical printing

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
