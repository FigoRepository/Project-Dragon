import streamlit as st
import pandas as pd
from datetime import date

from data_loader import load_db_workbook, DataLoadError
from column_map import COLUMN_MAP, GROUP_ORDER, DEFAULT_TABULAR_KEYS
from report_calcs import (
    company_slice, compute_client_kpis, build_deltas, energy_mix_by_site,
    key_achievements_text,
)
from charts import solar_split_pie, energy_mix_bar
from pdf_export import build_client_report_pdf
from utils import fmt_id, fmt_pct

MONTH_NAMES_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                  "Agustus", "September", "Oktober", "November", "Desember"]

st.set_page_config(page_title="Akartha O&M BI Dashboard", layout="wide", page_icon=None)

BRAND_DARK = "#153327"
BRAND = "#2F6B48"
BRAND_LIGHT = "#4C8A63"
CREAM = "#E9E6C9"
CREAM_MUTED = "#B9C2AE"
KHAKI = "#C9C6A2"
TEXT = "#1B241D"
TEXT_MUTED = "#6B7568"
BORDER = "#CDD3BF"

# Comprehensive, self-contained CSS: forces the Akartha light theme regardless
# of the viewer's browser/Streamlit Cloud dark-mode preference, since relying
# on .streamlit/config.toml alone is fragile (it's easy for a hidden folder to
# not make it into a GitHub push). Everything needed to render correctly lives
# in this one injected stylesheet.
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

  html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main,
  .stApp {{
    background-color: #F4F5EF !important;
    color: {TEXT} !important;
    font-family: 'Inter', sans-serif !important;
  }}
  [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}
  [data-testid="stToolbar"] {{ right: 8px; }}

  h1, h2, h3, .akartha-header h1, .section-title, .page-title {{
    font-family: 'Space Grotesk', sans-serif !important;
  }}
  [data-testid="stAppViewContainer"] h1,
  [data-testid="stAppViewContainer"] h2,
  [data-testid="stAppViewContainer"] h3,
  [data-testid="stAppViewContainer"] p,
  [data-testid="stAppViewContainer"] span,
  [data-testid="stAppViewContainer"] label,
  [data-testid="stAppViewContainer"] .stMarkdown,
  [data-testid="stAppViewContainer"] .stCaption {{
    color: {TEXT} !important;
  }}

  /* Sidebar: force the Akartha dark-green brand regardless of theme */
  [data-testid="stSidebar"] {{
    background-color: {BRAND_DARK} !important;
    border-right: 1px solid #0E2119;
  }}
  [data-testid="stSidebar"] * {{ color: {CREAM} !important; }}
  [data-testid="stSidebar"] .stRadio label span {{ color: {CREAM} !important; font-weight: 600; }}
  [data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div:first-child {{ border-color: {CREAM_MUTED} !important; }}
  [data-testid="stSidebar"] hr {{ border-color: #2A5A42 !important; }}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
    background-color: #1D4433 !important; border: 1px dashed #3C6A52 !important; border-radius: 8px;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {{ color: {CREAM_MUTED} !important; }}
  [data-testid="stSidebar"] button {{
    background-color: #1D4433 !important; color: {CREAM} !important; border: 1px solid #3C6A52 !important;
  }}
  [data-testid="stSidebar"] [data-testid="stAlert"] {{ background-color: #1D4433 !important; border-radius: 8px; }}
  .nav-soon {{
    display: flex; align-items: center; gap: 8px; padding: 7px 4px; font-size: 13px;
    color: {CREAM_MUTED} !important; opacity: 0.75;
  }}
  .nav-soon .dot {{ width: 6px; height: 6px; border-radius: 50%; background: {CREAM_MUTED}; flex-shrink: 0; }}
  .nav-badge {{
    font-size: 9px; font-weight: 700; border: 1px solid {CREAM_MUTED}; border-radius: 999px;
    padding: 1px 7px; margin-left: auto; letter-spacing: 0.3px;
  }}

  .page-title {{ font-size: 26px; font-weight: 700; color: {BRAND_DARK}; margin: 4px 0 18px; }}

  .akartha-header {{
    background: {BRAND_DARK}; border-radius: 14px 14px 0 0; padding: 20px 26px;
    color: white; margin-bottom: 0;
  }}
  .akartha-header h1 {{ font-size: 22px; margin: 0 0 6px 0; color: white !important; font-weight: 700; }}
  .akartha-header .sub {{ color: {CREAM} !important; font-size: 13px; }}
  .akartha-header .sub b {{ color: white !important; }}

  .akartha-card {{
    background: white; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 14px 16px; height: 100%; position: relative;
  }}
  .akartha-card .icon {{
    position: absolute; top: 12px; right: 12px; width: 26px; height: 26px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center; font-size: 13px; color: white; font-weight: 700;
  }}
  .akartha-card .label {{ font-size: 11.5px; font-weight: 700; color: {BRAND_DARK} !important; letter-spacing: 0.2px; padding-right: 26px; }}
  .akartha-card .value {{ font-size: 21px; font-weight: 700; color: {TEXT} !important; margin: 6px 0 4px; line-height: 1.25; word-break: break-word; font-family: 'Space Grotesk', sans-serif; }}
  .akartha-card .delta-up {{ color: #1F6A3F !important; font-size: 12px; font-weight: 600; }}
  .akartha-card .delta-down {{ color: #8C2E26 !important; font-size: 12px; font-weight: 600; }}
  .akartha-card .delta-na {{ color: {TEXT_MUTED} !important; font-size: 12px; }}

  .section-title {{ font-size: 15px; font-weight: 700; color: {BRAND_DARK} !important; margin: 6px 0 2px; }}
  .section-rule {{ border-bottom: 2px solid {TEXT}; opacity: 0.14; margin-bottom: 10px; }}
  .achv-item {{ display: flex; gap: 8px; font-size: 13px; color: {TEXT} !important; margin-bottom: 9px; line-height: 1.5; }}
  .achv-num {{ font-weight: 700; color: {BRAND_DARK} !important; flex-shrink: 0; }}
  .badge-warn {{ background: #FBF1DF; color: #935B0F !important; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }}
  .badge-crit {{ background: #FBE9E6; color: #8C2E26 !important; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }}
  .issue-row {{ display: flex; gap: 8px; align-items: flex-start; font-size: 12.5px; margin-bottom: 10px; color: {TEXT} !important; }}

  [data-testid="stTabs"] button[role="tab"] {{ font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: {TEXT_MUTED} !important; }}
  [data-testid="stTabs"] button[aria-selected="true"] {{ color: {BRAND} !important; }}
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background-color: {BRAND} !important; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "df_current" not in st.session_state:
    st.session_state.df_current = None
    st.session_state.meta_current = None
    st.session_state.df_previous = None
    st.session_state.meta_previous = None

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"<div style='display:flex;align-items:center;gap:10px;'>"
                f"<div style='width:34px;height:34px;border-radius:8px;background:#1D4433;"
                f"display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-family:Space Grotesk,sans-serif;'>A</div>"
                f"<div><b>Akartha</b><br><span style='font-size:11px;opacity:0.75;'>Energy · O&amp;M BI (MVP)</span></div></div>",
                unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("Navigate", ["Reports"], index=0, label_visibility="collapsed")
    for coming_soon in ["Portfolio", "Sites", "Issues", "Sustainability"]:
        st.markdown(
            f'<div class="nav-soon"><span class="dot"></span>{coming_soon}<span class="nav-badge">SOON</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**Data source**")
    current_file = st.file_uploader("Current month DB export (.xlsx)", type=["xlsx"], key="current_upl")
    previous_file = st.file_uploader("Previous month DB export (.xlsx) — optional, for MoM comparison", type=["xlsx"], key="previous_upl")

    if current_file is not None:
        try:
            df_cur, meta_cur = load_db_workbook(current_file)
            st.session_state.df_current = df_cur
            st.session_state.meta_current = meta_cur
            st.success(f"Loaded {meta_cur['n_sites']} sites, {meta_cur['n_companies']} companies.")
        except DataLoadError as e:
            st.error(str(e))
            st.session_state.df_current = None

    if previous_file is not None:
        try:
            df_prev, meta_prev = load_db_workbook(previous_file)
            st.session_state.df_previous = df_prev
            st.session_state.meta_previous = meta_prev
            st.info(f"Previous month loaded: {meta_prev['n_sites']} sites.")
        except DataLoadError as e:
            st.error(str(e))
            st.session_state.df_previous = None

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.markdown('<div class="page-title">Reports</div>', unsafe_allow_html=True)

df = st.session_state.df_current
if df is None:
    st.info(
        "Upload a **Current month DB export (.xlsx)** in the sidebar to get started. "
        "The file must have the same 'DB' sheet structure as the AEB monthly data export "
        "(No, Project, Holding, Company, Estate, Site, PV, BESS, INV ... through Environmental Performance)."
    )
    st.stop()

tab_client, tab_tabular = st.tabs(["Client Report", "Tabular Report"])

# ===========================================================================
# CLIENT REPORT
# ===========================================================================
with tab_client:
    companies = sorted(df["company"].unique().tolist())
    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        company = st.selectbox("Client (Company)", companies)
    period_date = st.session_state.meta_current.get("period_date")
    default_month_idx = (period_date.month - 1) if period_date else date.today().month - 1
    default_year = str(period_date.year) if period_date else str(date.today().year)
    with col_sel2:
        month_label = st.selectbox("Bulan", MONTH_NAMES_ID, index=default_month_idx)
    with col_sel3:
        year_label = st.selectbox("Tahun", [str(y) for y in range(2024, 2028)], index=[str(y) for y in range(2024, 2028)].index(default_year) if default_year in [str(y) for y in range(2024, 2028)] else 2)

    df_company = company_slice(df, company)
    kpis = compute_client_kpis(df_company)

    previous_kpis = None
    if st.session_state.df_previous is not None:
        df_company_prev = company_slice(st.session_state.df_previous, company)
        if len(df_company_prev):
            previous_kpis = compute_client_kpis(df_company_prev)
    deltas = build_deltas(kpis, previous_kpis)

    # ---- Header banner ----
    st.markdown(f"""
    <div class="akartha-header">
      <h1>Monthly Performance Report</h1>
      <div class="sub">Bulan: <b>{month_label}</b> &nbsp;&nbsp; Tahun: <b>{year_label}</b> &nbsp;&nbsp; Client: <b>{company}</b></div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">Matriks Ketercapaian</div><div class="section-rule"></div>', unsafe_allow_html=True)

        def render_card(col, label, value, delta, invert=False, icon="\u25cf", icon_bg=BRAND):
            if delta is None:
                delta_html = '<span class="delta-na">vs. bulan lalu: n/a</span>'
            else:
                good = (delta <= 0) if invert else (delta >= 0)
                cls = "delta-up" if good else "delta-down"
                arrow = "\u25b2" if delta >= 0 else "\u25bc"
                delta_html = f'<span class="{cls}">{arrow} {fmt_id(abs(delta), 1)}% vs. bulan lalu</span>'
            col.markdown(f"""
            <div class="akartha-card">
              <div class="icon" style="background:{icon_bg};">{icon}</div>
              <div class="label">{label}</div>
              <div class="value">{value}</div>
              {delta_html}
            </div>
            """, unsafe_allow_html=True)

        mix_df = energy_mix_by_site(df_company)

        # ---- Row 1: 4 KPI cards + donut chart, matching the reference layout ----
        r1 = st.columns([1, 1, 1, 1, 1.3])
        render_card(r1[0], "LISTRIK TERSALURKAN", f"{fmt_id(kpis['listrik_tersalurkan_kwh'])} kWh", deltas.get("listrik_tersalurkan_kwh"), icon="\u26a1", icon_bg=BRAND)
        render_card(r1[1], "PERSENTASE ENERGI BERSIH", fmt_pct(kpis['ref_pct'], 2), deltas.get("ref_pct"), icon="\u2600", icon_bg=BRAND_LIGHT)
        render_card(r1[2], "JUMLAH SOLAR", f"{fmt_id(kpis['jumlah_solar_l'])} Liter", deltas.get("jumlah_solar_l"), invert=True, icon="\u26fd", icon_bg="#B9812C")
        render_card(r1[3], "AVAILABILITY", fmt_pct(kpis['availability_pct'], 2), deltas.get("availability_pct"), icon="\u2713", icon_bg="#1F6A3F")
        with r1[4]:
            with st.container(border=True):
                st.image(solar_split_pie(kpis["aeb_l"], kpis["client_l"]), use_container_width=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # ---- Row 2: energy mix chart (left) + achievements & critical issue (right) ----
        col_chart, col_side = st.columns([1.7, 1])
        with col_chart:
            with st.container(border=True):
                if len(mix_df):
                    st.image(energy_mix_bar(mix_df), use_container_width=True)
                else:
                    st.info("No site-level data available for this company to build the energy mix chart.")
        with col_side:
            st.markdown('<div class="section-title">Key Achievements</div><div class="section-rule"></div>', unsafe_allow_html=True)
            achievements = key_achievements_text(kpis, deltas, month_label, year_label)
            for i, item in enumerate(achievements, start=1):
                st.markdown(f'<div class="achv-item"><span class="achv-num">{i}.</span><span>{item}</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title" style="margin-top:14px;">Critical Issue</div><div class="section-rule"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:12px;color:#6B7568;margin-bottom:6px;">Issue tracking is not yet wired to this MVP\'s data source.</div>'
                '<div style="font-size:13px;color:#6B7568;">-- &nbsp; -- &nbsp; --</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Sustainability Impact</div><div class="section-rule"></div>', unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        render_card(s1, "CO2 AVOIDED", f"{fmt_id(kpis['co2_avoided_ton'], 1)} T CO2", deltas.get("co2_avoided_ton") if previous_kpis else None, icon="\u2601", icon_bg=BRAND)
        render_card(s2, "EQUIVALENT TREES PLANTED", f"{fmt_id(kpis['trees_equivalent'])} Trees", deltas.get("trees_equivalent") if previous_kpis else None, icon="T", icon_bg=BRAND_LIGHT)
        render_card(s3, "DIESEL SAVINGS", f"{fmt_id(kpis['diesel_savings_l'])} Liter", deltas.get("diesel_savings_l") if previous_kpis else None, icon="\u26fd", icon_bg="#B9812C")

    # ---- PDF export ----
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    pdf_bytes = build_client_report_pdf(
        company=company, month_label=month_label, year_label=year_label,
        kpis=kpis, deltas=deltas, sust_deltas=deltas if previous_kpis else {},
        pie_png=solar_split_pie(kpis["aeb_l"], kpis["client_l"]),
        bar_png=energy_mix_bar(mix_df) if len(mix_df) else solar_split_pie(1, 1),
        achievements=key_achievements_text(kpis, deltas, month_label, year_label),
        critical_issues=[],
    )
    st.download_button(
        "Download PDF Report",
        data=pdf_bytes,
        file_name=f"AEB_Client_Report_{company.replace(' ', '_')}_{month_label}_{year_label}.pdf",
        mime="application/pdf",
        type="primary",
    )

# ===========================================================================
# TABULAR REPORT
# ===========================================================================
with tab_tabular:
    st.markdown('<div class="section-title">Tabular Report</div><div class="section-rule"></div>', unsafe_allow_html=True)

    fcol1, fcol2, fcol3 = st.columns([1, 1, 1.4])
    with fcol1:
        f_projects = st.multiselect("Project", sorted(df["project"].unique().tolist()), default=sorted(df["project"].unique().tolist()))
    with fcol2:
        f_companies = st.multiselect("Company", sorted(df["company"].unique().tolist()), default=sorted(df["company"].unique().tolist()))
    with fcol3:
        f_search = st.text_input("Search site / estate", "")

    with st.expander("Choose columns to display", expanded=False):
        selected_keys = []
        cols_per_row = 3
        for group in GROUP_ORDER:
            group_cols = [c for c in COLUMN_MAP if c[3] == group]
            st.markdown(f"**{group}**")
            row_cols = st.columns(cols_per_row)
            for i, (idx, key, label, grp, unit) in enumerate(group_cols):
                default_checked = key in DEFAULT_TABULAR_KEYS
                unit_str = f" ({unit})" if unit else ""
                checked = row_cols[i % cols_per_row].checkbox(f"{label}{unit_str}", value=default_checked, key=f"col_{key}")
                if checked:
                    selected_keys.append(key)

    filtered = df[df["project"].isin(f_projects) & df["company"].isin(f_companies)]
    if f_search:
        mask = filtered["site"].str.contains(f_search, case=False, na=False) | filtered["estate"].str.contains(f_search, case=False, na=False)
        filtered = filtered[mask]

    label_map = {key: label for (_i, key, label, _g, _u) in COLUMN_MAP}
    display_cols = [k for k in selected_keys if k in filtered.columns]
    display_df = filtered[display_cols].copy()
    for c in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[c]):
            display_df[c] = display_df[c].round(2)
    display_df = display_df.rename(columns=label_map)

    st.caption(f"{len(filtered)} sites \u00b7 {len(display_cols)} columns selected")
    st.dataframe(display_df, use_container_width=True, height=480)

    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("Export CSV", data=csv_bytes, file_name="akartha_tabular_report.csv", mime="text/csv")
