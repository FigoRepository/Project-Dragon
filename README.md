# Akartha O&M BI Dashboard — Streamlit (full port of the JSX mockup)

This is a full Python/Streamlit port of the original React/JSX dashboard mockup —
same 85-site mock data model, same five modules (Portfolio, Sites, Site Detail,
Issues, Sustainability, Reports), same Akartha branding — so it can be deployed
and shared with other users without needing a Node/React build pipeline.

This supersedes the earlier "Reports-only, real-Excel-upload" MVP. All data here
is generated (seeded/deterministic, so numbers are stable across reloads), the
same way the JSX version was. Wiring live data back in (via Excel upload or an
API) is a natural next step, but out of scope for this port.

## Pages

- **Portfolio** — fleet KPIs, PV vs. consumption trend, REF trend (with its own
  local date-range toggle), critical issues panel, sortable site ranking table.
  Global filters: multi-select Project, date range (presets + custom), search.
- **Sites** — card grid of all 85 sites + the same ranking table, filterable.
- **Site Detail** — the five-segment monthly report per site: Energy
  Utilization (waterfall chart), Power Plant Generation (daily energy flow +
  irradiation), BESS Performance (SoC trend + SoH), DG Operation (runtime/fuel),
  System Reliability (availability trend), plus site-linked issues. Reached by
  clicking any site card or any ranking-table / issues-panel row.
- **Issues** — severity/status-filterable list of all tracked issues.
- **Sustainability** — Project/Site/date-scoped fuel, cost, and environmental
  impact savings.
- **Reports** — Client Report (per-company consolidated monthly report,
  matching AEB's letterhead format, including a Listrik/REF%/Solar/Availability
  KPI row and the Solar Akartha vs. Solar Client donut) and Tabular Report (a
  grouped column picker over the full ~70-column data model, with CSV export).

## Run it locally

```bash
cd akartha_streamlit
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud — free)

1. Push this folder's contents to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. **New app** -> pick the repo/branch -> set **Main file path** to `app.py`.
   - If you upload this folder as a subfolder of your repo (e.g.
     `repo/akartha_streamlit/app.py`), set the main file path to
     `akartha_streamlit/app.py` instead.
4. Deploy. Make sure `requirements.txt` and `rows_data.json` are pushed too —
   `rows_data.json` holds the 85-site roster and is loaded at startup.

## File structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — sidebar nav, all 6 pages, session-state routing |
| `data_model.py` | Full port of the JSX data generator: seeded RNG, 85-site roster, per-site metrics, issues |
| `charts_plotly.py` | Plotly chart builders (trend, waterfall, energy flow, donut, bars) |
| `report_columns.py` | Column catalog for the Tabular Report picker |
| `report_calcs_mock.py` | Client Report & Sustainability KPI aggregation |
| `utils.py` | Indonesian-style number formatting (used in Client Report) |
| `rows_data.json` | The 85-row site roster (extracted from the original JSX `ROWS` array) |
| `.streamlit/config.toml` | Brand theme colors (backup only — the app's CSS forces the theme at runtime regardless) |

## Notes

- The sidebar/theme CSS is injected at runtime with `!important` overrides
  targeting Streamlit's actual DOM (`data-testid` attributes) rather than
  relying solely on `.streamlit/config.toml`, since that file is a hidden
  folder that's easy to accidentally leave out of a GitHub push, and
  Streamlit Cloud can otherwise fall back to a dark theme that makes text
  unreadable against this app's light background.
- All figures are deterministic (seeded RNG), so the same site always shows
  the same numbers across reloads and across users — useful for demos.
- The `SNE|EU` issue-prone key intentionally matches both the Alpha and Alpha
  Extension projects' Senyiur EU rows (same behavior as the JSX version), so
  you'll see that site flagged twice in the roster — this mirrors the source
  workbook, not a bug.
