# Akartha O&M BI Dashboard — Streamlit MVP

This is the first working MVP of the Akartha O&M Business Intelligence Dashboard,
rebuilt in Python/Streamlit so it can be deployed and shared with other users
(the earlier version was a React mockup with dummy data — this one reads your
real monthly Excel exports).

**Scope of this MVP:** the **Reports** module only (Client Report + Tabular
Report), as agreed as the first priority. Portfolio, Sites, Issues, and
Sustainability are stubbed in the sidebar as "coming soon" so the navigation
structure is ready for the next build phase.

## What it does

1. You upload the current month's `DB`-sheet Excel export (same structure as
   `AEB_Data_Asset_for_Pak_Imam.xlsx`) in the sidebar. Optionally upload the
   previous month's file too, to unlock month-over-month deltas.
2. **Client Report** tab: pick a Company, see the consolidated monthly report —
   KPI cards (Listrik Tersalurkan, Persentase Energi Bersih, Jumlah Solar,
   **Availability**), an energy-mix-per-site chart, the Solar Akartha vs.
   Solar Client pie chart, a **Sustainability Impact** row (CO2 Avoided,
   Equivalent Trees Planted, Diesel Savings), auto-written Key Achievements,
   and a **Download PDF Report** button that renders the same report to a
   clean, letterhead-style PDF.
3. **Tabular Report** tab: pick which of the ~70 source columns to show,
   filter by Project/Company/search, preview the table, export to CSV.

## Run it locally

```bash
cd akartha_streamlit
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## Deploy so other people can use it (Streamlit Community Cloud — free)

1. Push this folder to a **GitHub repository** (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.
3. Click **New app**, pick the repository/branch, and set the main file path
   to `app.py`.
4. Deploy. Streamlit Cloud installs `requirements.txt` automatically and
   gives you a shareable `*.streamlit.app` URL — no server management needed.
5. Anyone with the link can open the app and upload their own monthly Excel
   file; nothing is stored server-side beyond the current session.

If AEB prefers internal hosting instead (e.g. behind the company VPN), the
same app runs unchanged on any server with Python 3.10+ via
`streamlit run app.py --server.port <port> --server.address 0.0.0.0`, or in a
Docker container using the same `requirements.txt`.

## File structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — sidebar, Client Report, Tabular Report |
| `data_loader.py` | Reads & validates the uploaded `DB` sheet into a DataFrame |
| `column_map.py` | Column catalog (index → key → label → group → unit), shared by the loader and the Tabular Report column picker |
| `report_calcs.py` | KPI aggregation, month-over-month deltas, Key Achievements text |
| `charts.py` | Matplotlib charts (pie, energy-mix bar), shared by the on-screen view and the PDF |
| `pdf_export.py` | Builds the downloadable PDF report (ReportLab) |
| `utils.py` | Indonesian-style number formatting |
| `.streamlit/config.toml` | Brand theme colors |

## Data assumptions / things to confirm before wider rollout

- **Availability (%)** is not an explicit column in the source workbook (no
  uptime/outage-hours field exists in the `DB` sheet). It is computed as
  `Load Supplied Actual ÷ Load Supplied Target × 100` — a load-achievement
  proxy for availability, not a true logged-uptime figure. Swap this formula
  once a dedicated outage-hours field is added to the export.
- **Diesel Savings** = `(Target AEB + Target Client) − (Actual AEB + Actual
  Client)` fuel litres, floored at 0. A month where actual diesel usage
  exceeds the plan (e.g. due to lower-than-planned availability) will
  correctly show 0 savings rather than a negative number.
- The uploaded workbook's **percentage-formatted cells are stored as
  fractions (0–1) in Excel**; the loader multiplies every `%`-unit column by
  100 on load. If a future export changes this convention, update
  `PCT_KEYS` handling in `data_loader.py`.
- **Critical Issue** section is a placeholder ("--") in this MVP — it isn't
  wired to a real issue tracker yet. Wiring it up (e.g. to the
  `Project_Operations_Issue_List` workbook) is a good next increment.
- The loader validates the sheet against a handful of expected header
  positions (Company, Load Supplied Target, Genset Production, CO2) and
  raises a clear error if an uploaded file doesn't match the expected `DB`
  sheet layout, rather than silently mis-reading columns.
