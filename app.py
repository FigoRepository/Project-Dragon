import streamlit as st
import pandas as pd
from datetime import date, timedelta

from data_model import (
    SITES, SITES_BY_ID, ISSUES, PROJECTS, COMPANIES, TODAY, RANGE_OPTIONS,
    compute_range_indices, REPORT_MONTH_LABEL,
)
from charts_plotly import (
    pv_consumption_trend, ref_trend, waterfall_chart, energy_flow_chart, genset_share_bar,
    soc_trend_chart, soh_monthly_chart, diesel_runtime_fuel_chart, specific_fuel_chart,
    availability_trend_chart, solar_split_donut, energy_mix_bar,
)
from report_columns import COLUMN_GROUPS, LABEL_MAP, DEFAULT_KEYS
from report_calcs_mock import company_sites, compute_client_kpis, key_achievements_text, sustainability_savings
from utils import fmt_id, fmt_pct

st.set_page_config(page_title="Akartha O&M BI Dashboard", layout="wide", page_icon=None)

BRAND_DARK = "#153327"
BRAND = "#2F6B48"
BRAND_LIGHT = "#4C8A63"
CREAM = "#E9E6C9"
CREAM_MUTED = "#B9C2AE"
TEXT = "#1B241D"
TEXT_MUTED = "#6B7568"
BORDER = "#CDD3BF"
SUCCESS = "#2E8B57"
WARNING = "#B9812C"
CRITICAL = "#B8433A"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

  html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main, .stApp {{
    background-color: #F4F5EF !important; color: {TEXT} !important; font-family: 'Inter', sans-serif !important;
  }}
  [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0) !important; }}

  h1, h2, h3, .page-title, .section-title {{ font-family: 'Space Grotesk', sans-serif !important; }}
  [data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2, [data-testid="stAppViewContainer"] h3,
  [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] span, [data-testid="stAppViewContainer"] label,
  [data-testid="stAppViewContainer"] .stMarkdown, [data-testid="stAppViewContainer"] .stCaption {{ color: {TEXT} !important; }}

  [data-testid="stSidebar"] {{ background-color: {BRAND_DARK} !important; border-right: 1px solid #0E2119; }}
  [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] div,
  [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3, [data-testid="stSidebar"] li, [data-testid="stSidebar"] a {{ color: {CREAM} !important; }}
  [data-testid="stSidebar"] hr {{ border-color: #2A5A42 !important; }}
  [data-testid="stSidebar"] button {{
    background-color: transparent !important; color: {CREAM} !important; border: none !important;
    text-align: left !important; font-weight: 600 !important; padding: 8px 10px !important;
  }}
  [data-testid="stSidebar"] button:hover {{ background-color: #1D4433 !important; border-radius: 8px !important; }}
  [data-testid="stSidebar"] button p {{ text-align: left !important; }}
  .nav-active button {{ background-color: #1D4433 !important; border-radius: 8px !important; }}
  .sidebar-capsule {{ background: #1D4433; border-radius: 10px; padding: 12px; margin-top: 10px; }}

  .page-title {{ font-size: 24px; font-weight: 700; color: {BRAND_DARK}; margin: 0 0 4px; }}
  .page-breadcrumb {{ font-size: 11.5px; color: {TEXT_MUTED} !important; margin-bottom: 14px; }}

  .akartha-card {{ background: white; border: 1px solid {BORDER}; border-radius: 10px; padding: 14px 16px; height: 100%; position: relative; }}
  .akartha-card .icon {{ position: absolute; top: 12px; right: 12px; width: 26px; height: 26px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 13px; color: white; font-weight: 700; }}
  .akartha-card .label {{ font-size: 11.5px; font-weight: 700; color: {TEXT_MUTED} !important; letter-spacing: 0.2px; padding-right: 26px; }}
  .akartha-card .value {{ font-size: 22px; font-weight: 700; color: {TEXT} !important; margin: 5px 0 3px; line-height: 1.25; word-break: break-word; font-family: 'Space Grotesk', sans-serif; }}
  .akartha-card .unit {{ font-size: 12px; font-weight: 500; color: {TEXT_MUTED} !important; }}
  .akartha-card .delta-up {{ color: #1F6A3F !important; font-size: 12px; font-weight: 600; }}
  .akartha-card .delta-down {{ color: #8C2E26 !important; font-size: 12px; font-weight: 600; }}

  .section-title {{ font-size: 15px; font-weight: 700; color: {BRAND_DARK} !important; margin: 6px 0 2px; }}
  .section-sub {{ font-size: 12px; color: {TEXT_MUTED} !important; margin-bottom: 8px; }}
  .section-rule {{ border-bottom: 2px solid {TEXT}; opacity: 0.14; margin-bottom: 10px; }}
  .achv-item {{ display: flex; gap: 8px; font-size: 13px; color: {TEXT} !important; margin-bottom: 9px; line-height: 1.5; }}
  .achv-num {{ font-weight: 700; color: {BRAND_DARK} !important; flex-shrink: 0; }}

  .status-badge {{ display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 600; }}
  .status-normal {{ background: #E7F3EA; color: {SUCCESS} !important; }}
  .status-warning {{ background: #FBF1DF; color: {WARNING} !important; }}
  .status-critical {{ background: #FBE9E6; color: {CRITICAL} !important; }}
  .sev-critical {{ background: #FBE9E6; color: {CRITICAL} !important; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; }}
  .sev-warning {{ background: #FBF1DF; color: {WARNING} !important; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; }}
  .sev-info {{ background: #E9F0F8; color: #3B6EA0 !important; font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase; }}

  .akartha-header {{ background: {BRAND_DARK}; border-radius: 14px 14px 0 0; padding: 20px 26px; color: white; }}
  .akartha-header h1 {{ font-size: 22px; margin: 0 0 6px 0; color: white !important; font-weight: 700; }}
  .akartha-header .sub {{ color: {CREAM} !important; font-size: 13px; }}
  .akartha-header .sub b {{ color: white !important; }}

  [data-testid="stTabs"] button[role="tab"] {{ font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: {TEXT_MUTED} !important; }}
  [data-testid="stTabs"] button[aria-selected="true"] {{ color: {BRAND} !important; }}
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background-color: {BRAND} !important; }}
</style>
""", unsafe_allow_html=True)

MONTH_NAMES_ID = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                  "Agustus", "September", "Oktober", "November", "Desember"]


def fmt_en(n, decimals=0):
    if n is None:
        return "-"
    return f"{n:,.{decimals}f}"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = dict(
    page="portfolio", selected_site_id=None,
    gf_projects=list(PROJECTS), gf_search="",
    gf_date_mode="preset", gf_range_key="30d", gf_custom_start=None, gf_custom_end=None,
)
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def go(page, site_id=None):
    st.session_state.page = page
    if site_id is not None:
        st.session_state.selected_site_id = site_id
    st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;padding:4px 0 14px;'>"
        f"<div style='width:34px;height:34px;border-radius:8px;background:#1D4433;display:flex;"
        "align-items:center;justify-content:center;color:white;font-weight:700;font-family:Space Grotesk,sans-serif;'>A</div>"
        "<div><b>Akartha</b><br><span style='font-size:11px;opacity:0.75;'>Energy · O&amp;M BI</span></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    nav_items = [("portfolio", "Portfolio"), ("sites", "Sites"), ("issues", "Issues"),
                 ("sustainability", "Sustainability"), ("reports", "Reports")]
    for key, label in nav_items:
        active = st.session_state.page == key or (key == "sites" and st.session_state.page == "site_detail")
        cls = "nav-active" if active else ""
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            go(key)
        st.markdown("</div>", unsafe_allow_html=True)

    total_capacity = sum(s["capacity_kwp"] for s in SITES) / 1000
    open_issues = sum(1 for i in ISSUES if i["status"] != "Resolved")
    st.markdown(
        f"""<div class="sidebar-capsule">
            <div style="font-size:11px;font-weight:600;opacity:0.85;">Portfolio capacity</div>
            <div style="font-size:20px;font-weight:700;font-family:'Space Grotesk',sans-serif;">{fmt_en(total_capacity, 2)} <span style="font-size:12px;font-weight:500;">MWp</span></div>
            <div style="font-size:11px;opacity:0.75;margin-top:2px;">{len(SITES)} active sites · {open_issues} open issues</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def status_badge(status):
    cls = {"Normal": "status-normal", "Warning": "status-warning", "Critical": "status-critical"}.get(status, "status-normal")
    return f'<span class="status-badge {cls}">{status}</span>'


def severity_badge(sev):
    cls = {"Critical": "sev-critical", "Warning": "sev-warning", "Info": "sev-info"}.get(sev, "sev-info")
    return f'<span class="{cls}">{sev}</span>'


def kpi_card(col, label, value, unit="", delta=None, invert=False, icon="\u25cf", icon_bg=BRAND):
    delta_html = ""
    if delta is not None:
        good = (delta <= 0) if invert else (delta >= 0)
        cls = "delta-up" if good else "delta-down"
        arrow = "\u25b2" if delta >= 0 else "\u25bc"
        delta_html = f'<div class="{cls}">{arrow} {fmt_en(abs(delta), 1)}%</div>'
    col.markdown(f"""
    <div class="akartha-card">
      <div class="icon" style="background:{icon_bg};">{icon}</div>
      <div class="label">{label}</div>
      <div class="value">{value} <span class="unit">{unit}</span></div>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)


def filter_sites(projects, search):
    out = []
    for s in SITES:
        if s["project"] not in projects:
            continue
        if search:
            q = search.lower()
            if q not in s["name"].lower() and q not in s["company"].lower() and q not in s["code"].lower() and q not in s["estate"].lower():
                continue
        out.append(s)
    return out


def global_filter_bar(key_prefix):
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        search = st.text_input("Search sites, estates...", value=st.session_state.gf_search, key=f"{key_prefix}_search")
        st.session_state.gf_search = search
    with c2:
        projects = st.multiselect("Projects", PROJECTS, default=st.session_state.gf_projects, key=f"{key_prefix}_projects")
        st.session_state.gf_projects = projects
    with c3:
        mode = st.selectbox(
            "Date range", ["Last 7 days", "Last 14 days", "Last 30 days", "Month to date", "Custom range"],
            index=2, key=f"{key_prefix}_range",
        )
        if mode == "Custom range":
            st.session_state.gf_date_mode = "custom"
            cs, ce = st.columns(2)
            min_d = TODAY - timedelta(days=29)
            with cs:
                st.session_state.gf_custom_start = st.date_input("Start", value=TODAY - timedelta(days=29), min_value=min_d, max_value=TODAY, key=f"{key_prefix}_start")
            with ce:
                st.session_state.gf_custom_end = st.date_input("End", value=TODAY, min_value=min_d, max_value=TODAY, key=f"{key_prefix}_end")
        else:
            st.session_state.gf_date_mode = "preset"
            st.session_state.gf_range_key = {"Last 7 days": "7d", "Last 14 days": "14d", "Last 30 days": "30d", "Month to date": "mtd"}[mode]
    return projects, search


def portfolio_kpis(sites, start_idx, end_idx):
    n = len(sites) or 1
    idx_range = range(start_idx, end_idx + 1)
    total_capacity = sum(s["capacity_kwp"] for s in sites)
    total_pv = sum(sum(s["history"]["pv"][i] for i in idx_range) for s in sites)
    total_cons = sum(sum(s["history"]["consumption"][i] for i in idx_range) for s in sites)
    avg_ref = sum(s["ref_today"] for s in sites) / n
    avg_soc = sum(s["bess_soc"] for s in sites) / n
    total_diesel = sum(sum(s["history"]["diesel"][i] for i in idx_range) for s in sites)
    avg_avail = sum(s["availability_today"] for s in sites) / n
    site_ids = {s["id"] for s in sites}
    open_issues = sum(1 for i in ISSUES if i["status"] != "Resolved" and i["site_id"] in site_ids)
    return dict(total_capacity=total_capacity, total_pv=total_pv, total_cons=total_cons, avg_ref=avg_ref,
                avg_soc=avg_soc, total_diesel=total_diesel, avg_avail=avg_avail, open_issues=open_issues)


def build_trend(sites, idx_list):
    rows = []
    for idx in idx_list:
        date_label = SITES[0]["history"]["dates"][idx]
        pv = sum(s["history"]["pv"][idx] for s in sites)
        cons = sum(s["history"]["consumption"][idx] for s in sites)
        ref = sum(s["history"]["ref"][idx] for s in sites) / len(sites) if sites else 0
        rows.append(dict(date=date_label, pv=pv, consumption=cons, ref=ref))
    return rows


def issues_panel(issues_list, clickable=True, limit=None):
    shown = issues_list[:limit] if limit else issues_list
    if not shown:
        st.markdown('<div style="text-align:center;color:#6B7568;padding:20px 0;font-size:13px;">No issues match the current filters.</div>', unsafe_allow_html=True)
        return
    for i in shown:
        st.markdown(f"""
        <div style="padding:8px 2px 2px;border-bottom:1px solid {BORDER};">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:2px;flex-wrap:wrap;">
            <span style="font-weight:600;font-size:12.5px;">{i['site_name']}</span> {severity_badge(i['severity'])}
          </div>
          <div style="font-size:12.5px;color:{TEXT_MUTED};margin-bottom:3px;">{i['desc']}</div>
          <div style="font-size:11px;color:#98A08F;">{i['device']} · {i['date']} · <b>{i['status']}</b></div>
        </div>
        """, unsafe_allow_html=True)
        if clickable:
            if st.button("Open site detail \u2192", key=f"issue_open_{i['id']}", use_container_width=True):
                go("site_detail", i["site_id"])
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


def site_ranking_table(sites, key_prefix):
    rows = []
    for s in sites:
        rows.append({
            "Site": s["name"], "Company": s["company"], "Project": s["project"],
            "PV (kWp)": s["capacity_kwp"], "PV gen today (kWh)": s["pv_generation_today"],
            "REF %": s["ref_today"], "BESS SOC %": s["bess_soc"], "Diesel (L)": s["diesel_today"],
            "Availability %": round(s["availability_today"], 1), "Status": s["status"], "_id": s["id"],
        })
    df = pd.DataFrame(rows).sort_values("REF %", ascending=False).reset_index(drop=True)
    st.caption(f"{len(df)} sites · click a row to open its detail report")
    event = st.dataframe(
        df.drop(columns=["_id"]), use_container_width=True, height=420, hide_index=True,
        on_select="rerun", selection_mode="single-row", key=f"{key_prefix}_ranking",
    )
    sel = event.selection.rows if hasattr(event, "selection") else []
    if sel:
        go("site_detail", df.iloc[sel[0]]["_id"])


# ===========================================================================
# PORTFOLIO
# ===========================================================================
def render_portfolio():
    st.markdown('<div class="page-title">Portfolio overview</div><div class="page-breadcrumb">O&amp;M Business Intelligence</div>', unsafe_allow_html=True)
    projects, search = global_filter_bar("pf")
    sites = filter_sites(projects, search)
    start_idx, end_idx = compute_range_indices(st.session_state.gf_date_mode, st.session_state.gf_range_key,
                                                st.session_state.gf_custom_start, st.session_state.gf_custom_end)
    kpis = portfolio_kpis(sites, start_idx, end_idx)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    r1 = st.columns(4)
    kpi_card(r1[0], "FLEET PV CAPACITY", fmt_en(kpis["total_capacity"] / 1000, 2), "MWp", icon="\u26a1", icon_bg=BRAND)
    kpi_card(r1[1], "PV GENERATION", fmt_en(kpis["total_pv"] / 1000, 1), "MWh", delta=4.2, icon="\u2600", icon_bg=BRAND_LIGHT)
    kpi_card(r1[2], "ENERGY CONSUMPTION", fmt_en(kpis["total_cons"] / 1000, 1), "MWh", delta=1.8, invert=True, icon="\u2699", icon_bg="#3B6EA0")
    kpi_card(r1[3], "RENEWABLE ENERGY FACTOR", fmt_en(kpis["avg_ref"], 1), "%", delta=2.1, icon="\u2601", icon_bg=SUCCESS)
    r2 = st.columns(4)
    kpi_card(r2[0], "AVG. BESS STATE OF CHARGE", fmt_en(kpis["avg_soc"], 0), "%", icon="\u25a0", icon_bg=BRAND_LIGHT)
    kpi_card(r2[1], "DIESEL CONSUMPTION", fmt_en(kpis["total_diesel"], 0), "L", delta=-3.4, invert=True, icon="\u26fd", icon_bg=WARNING)
    kpi_card(r2[2], "FLEET AVAILABILITY", fmt_en(kpis["avg_avail"], 1), "%", delta=0.6, icon="\u2713", icon_bg=SUCCESS)
    kpi_card(r2[3], "OPEN CRITICAL ISSUES", str(kpis["open_issues"]), "issues", icon="!", icon_bg=CRITICAL)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    idx_list = list(range(start_idx, end_idx + 1))
    trend = build_trend(sites, idx_list)
    col_chart, col_issues = st.columns([2, 1])
    with col_chart:
        with st.container(border=True):
            st.markdown(f'<div class="section-title">PV generation vs. energy consumption</div><div class="section-sub">{len(sites)} sites · selected date range</div><div class="section-rule"></div>', unsafe_allow_html=True)
            if trend:
                dates = [r["date"] for r in trend]
                st.plotly_chart(pv_consumption_trend(dates, [r["pv"] for r in trend], [r["consumption"] for r in trend]), use_container_width=True, config={"displayModeBar": False})
    with col_issues:
        with st.container(border=True):
            site_ids = {s["id"] for s in sites}
            relevant = [i for i in ISSUES if i["site_id"] in site_ids]
            relevant.sort(key=lambda i: 0 if i["status"] != "Resolved" else 1)
            st.markdown(f'<div class="section-title">Critical operational issues</div><div class="section-sub">{sum(1 for i in relevant if i["status"]!="Resolved")} open across portfolio</div><div class="section-rule"></div>', unsafe_allow_html=True)
            issues_panel(relevant, limit=6)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        top_l, top_r = st.columns([3, 2])
        with top_l:
            st.markdown('<div class="section-title">Renewable energy factor trend</div><div class="section-sub">Portfolio average</div>', unsafe_allow_html=True)
        with top_r:
            local_range = st.radio("Local range", ["7D", "14D", "30D", "MTD"], index=2, horizontal=True, key="pf_ref_local", label_visibility="collapsed")
        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        days_map = {"7D": 7, "14D": 14, "30D": 30, "MTD": 19}
        local_days = days_map[local_range]
        local_idx = list(range(30 - local_days, 30))
        local_trend = build_trend(sites, local_idx)
        if local_trend:
            st.plotly_chart(ref_trend([r["date"] for r in local_trend], [r["ref"] for r in local_trend]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        site_ranking_table(sites, "pf")


# ===========================================================================
# SITES
# ===========================================================================
def render_sites():
    st.markdown('<div class="page-title">Sites</div><div class="page-breadcrumb">O&amp;M Business Intelligence</div>', unsafe_allow_html=True)
    projects, search = global_filter_bar("st")
    sites = filter_sites(projects, search)
    st.caption(f"{len(sites)} sites match the current filters")

    shown = sites[:60]
    for row_start in range(0, len(shown), 3):
        cols = st.columns(3)
        for j, s in enumerate(shown[row_start:row_start + 3]):
            with cols[j]:
                with st.container(border=True):
                    genset_txt = (fmt_en(s['genset_capacity_kva']) + ' kVA') if isinstance(s['genset_capacity_kva'], (int, float)) else 'N/A'
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                      <div>
                        <div style="font-weight:600;font-size:14px;">{s['name']}</div>
                        <div style="font-size:11.5px;color:{TEXT_MUTED};">{s['company']}</div>
                        <div style="font-size:11px;color:#98A08F;">{s['project']} · {s['code']}</div>
                      </div>
                      {status_badge(s['status'])}
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12.5px;">
                      <div><span style="color:#98A08F;">PV capacity</span><div style="font-weight:600;">{fmt_en(s['capacity_kwp'])} kWp</div></div>
                      <div><span style="color:#98A08F;">BESS capacity</span><div style="font-weight:600;">{fmt_en(s['bess_capacity_kwh'])} kWh</div></div>
                      <div><span style="color:#98A08F;">Genset</span><div style="font-weight:600;">{genset_txt}</div></div>
                      <div><span style="color:#98A08F;">REF today</span><div style="font-weight:600;">{fmt_en(s['ref_today'], 1)}%</div></div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("View detail", key=f"sitecard_{s['id']}", use_container_width=True):
                        go("site_detail", s["id"])
    if len(sites) > 60:
        st.caption(f"Showing 60 of {len(sites)} sites — narrow with search or project filters, or use the table below.")

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        site_ranking_table(sites, "sitespg")


# ===========================================================================
# SITE DETAIL
# ===========================================================================
def render_site_detail(site_id):
    site = SITES_BY_ID.get(site_id)
    if not site:
        st.error("Site not found.")
        return
    r = site["report"]

    if st.button("\u2190 Back to portfolio"):
        go("portfolio")

    genset_label = f"{fmt_en(site['genset_capacity_kva'])} kVA" if isinstance(site["genset_capacity_kva"], (int, float)) else (site["genset_capacity_kva"] or "N/A")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;">
      <div class="page-title" style="margin:0;">{site['name']}</div> {status_badge(site['status'])}
    </div>
    <div style="font-size:13px;color:{TEXT_MUTED};margin:4px 0 16px;">
      {site['company']} · {site['code']} · {site['project']} · PV {fmt_en(site['capacity_kwp'])} kWp ·
      BESS {fmt_en(site['bess_capacity_kwh'])} kWh · Genset {genset_label} · Report period {REPORT_MONTH_LABEL}
    </div>
    """, unsafe_allow_html=True)

    kc = st.columns(6)
    kpi_card(kc[0], "PV GEN. TODAY", fmt_en(site["pv_generation_today"]), "kWh", icon="\u2600", icon_bg=BRAND)
    kpi_card(kc[1], "CONSUMPTION TODAY", fmt_en(site["consumption_today"]), "kWh", icon="\u2699", icon_bg="#3B6EA0")
    kpi_card(kc[2], "REF TODAY", fmt_en(site["ref_today"], 1), "%", icon="\u2601", icon_bg=SUCCESS)
    kpi_card(kc[3], "BESS SOC", fmt_en(site["bess_soc"]), "%", icon="\u25a0", icon_bg=BRAND_LIGHT)
    kpi_card(kc[4], "DIESEL TODAY", fmt_en(site["diesel_today"], 1), "L", icon="\u26fd", icon_bg=WARNING)
    kpi_card(kc[5], "AVAILABILITY", fmt_en(site["availability_today"], 1), "%", icon="\u2713", icon_bg=SUCCESS)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ---- I. Energy Utilization ----
    with st.container(border=True):
        eu = r["energy_utilization"]
        st.markdown('<div class="section-title">I. Energy utilization</div><div class="section-sub">Emplasmen Utama (EU) · PV-BESS energy production utilization</div><div class="section-rule"></div>', unsafe_allow_html=True)
        col_tbl, col_chart = st.columns([1, 1.3])
        with col_tbl:
            metric_rows = pd.DataFrame([
                ["Potential PV generation (kWh)", fmt_en(eu["potential_pv_kwh"]), fmt_en(eu["potential_pv_target_kwh"])],
                ["PV curtailment (kWh)", "-" + fmt_en(eu["sys_loss_kwh"] + eu["mismatch_kwh"] + eu["curt_maint_kwh"]), "0"],
                ["Unplanned outage (hours)", fmt_en(eu["outage_hours"]), "0"],
                ["Unplanned outage (kWh)", fmt_en(eu["outage_kwh"]), "0"],
                ["Diesel generation (kWh)", fmt_en(eu["diesel_gen_kwh"]), "0"],
                ["BESS discharge energy (kWh)", fmt_en(eu["bess_discharge_kwh"]), "-"],
                ["Total load served (kWh)", fmt_en(eu["total_load_served_kwh"]), fmt_en(eu["total_load_target_kwh"])],
                ["Renewable energy fraction (%)", fmt_en(eu["ref_pct"], 1) + "%", "100%"],
            ], columns=["Metric", "Value", "Target"])
            st.dataframe(metric_rows, hide_index=True, use_container_width=True, height=320)
        with col_chart:
            steps = [
                dict(name="PV-BESS potential generation", value=eu["potential_pv_kwh"], is_total=True, label_text="100%"),
                dict(name="System losses", value=-eu["sys_loss_kwh"], is_total=False, label_text=f'-{eu["sys_loss_pct"]:.1f}%'),
                dict(name="Curtailment (maintenance)", value=-eu["curt_maint_kwh"], is_total=False, label_text=f'-{eu["curt_maint_pct"]:.1f}%'),
                dict(name="Supply-demand mismatch", value=-eu["mismatch_kwh"], is_total=False, label_text=f'-{eu["mismatch_pct"]:.1f}%'),
                dict(name="Unplanned outage", value=-eu["outage_kwh"], is_total=False, label_text=f'-{eu["outage_pct"]:.1f}%'),
                dict(name="PV-BESS utilized energy", value=eu["utilized_kwh"], is_total=True, label_text=f'{eu["utilized_pct"]:.1f}%'),
            ]
            st.plotly_chart(waterfall_chart(steps), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="section-title" style="margin-top:10px;">Key highlights</div>', unsafe_allow_html=True)
        highlights = [
            f"Potential PV generation reached {fmt_en(eu['potential_pv_kwh'])} kWh against a target of {fmt_en(eu['potential_pv_target_kwh'])} kWh.",
            f"System losses accounted for {eu['sys_loss_pct']:.1f}% of potential yield.",
            f"Supply-demand mismatch reached {eu['mismatch_pct']:.1f}%.",
            f"Renewable energy fraction closed the period at {eu['ref_pct']:.1f}%.",
        ]
        for idx, h in enumerate(highlights, start=1):
            st.markdown(f'<div class="achv-item"><span class="achv-num">{idx}.</span><span>{h}</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ---- II. Power Plant Generation ----
    with st.container(border=True):
        gen = r["generation"]
        st.markdown('<div class="section-title">II. Power plant generation</div><div class="section-sub">Daily energy flow to meet load demand vs. solar irradiation</div><div class="section-rule"></div>', unsafe_allow_html=True)
        st.plotly_chart(energy_flow_chart(gen["day_nums"], gen["pv_used_daily"], gen["bess_kwh_daily"], gen["genset_kwh_daily"],
                                           [gen["max_daily_energy"]] * 30, gen["irradiation_history"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="section-title" style="margin-top:6px;">PV-BESS vs. diesel generation (%)</div>', unsafe_allow_html=True)
        st.plotly_chart(genset_share_bar(gen["genset_share_pct"], gen["pv_bess_share_pct"]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ---- III. BESS Performance ----
    with st.container(border=True):
        bess = r["bess"]
        st.markdown('<div class="section-title">III. Battery energy storage system (BESS) performance</div><div class="section-rule"></div>', unsafe_allow_html=True)
        col_tbl, col_chart = st.columns([1, 1.3])
        with col_tbl:
            metric_rows = pd.DataFrame([
                ["Avg. depth of discharge (DoD)", f"{bess['avg_dod']}%", "\u226480%"],
                ["Max depth of discharge (DoD)", f"{bess['max_dod']}%", "\u226485%"],
                ["Min / max state of charge (SoC)", f"{bess['min_soc_overall']}% / {bess['max_soc_overall']}%", "15% / 95%"],
                ["State of health (SoH)", f"{bess['soh']:.1f}%", "\u226595.0%"],
                ["Full cycles complete", str(bess["full_cycles_complete"]), "\u226435"],
            ], columns=["Metric", "Value", "Threshold"])
            st.dataframe(metric_rows, hide_index=True, use_container_width=True, height=220)
        with col_chart:
            st.plotly_chart(soc_trend_chart(bess["day_nums"], bess["soc_min_daily"], bess["soc_max_daily"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="section-sub" style="margin-top:6px;">Battery state of health, {TODAY.year} (%)</div>', unsafe_allow_html=True)
        st.plotly_chart(soh_monthly_chart([m["month"] for m in bess["soh_monthly"]], [m["soh"] for m in bess["soh_monthly"]]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ---- IV. DG Operation ----
    with st.container(border=True):
        dg = r["diesel"]
        st.markdown('<div class="section-title">IV. Diesel genset (DG) operation</div><div class="section-rule"></div>', unsafe_allow_html=True)
        col_tbl, col_chart = st.columns([1, 1.3])
        with col_tbl:
            metric_rows = pd.DataFrame([
                ["Total run time (hours)", fmt_en(dg["total_run_time_hours"], 1), "60"],
                ["Fuel by AEB (L)", fmt_en(dg["fuel_by_aeb"]), "2,610"],
                ["Total fuel consumption (L)", fmt_en(dg["total_fuel_consumption"]), "0"],
                ["Avg. specific fuel consumption (L/hour)", fmt_en(dg["avg_specific_fuel_consumption"], 1), "15"],
                ["Number of starts", str(dg["number_of_starts"]), "31"],
            ], columns=["Metric", "Value", "Target"])
            st.dataframe(metric_rows, hide_index=True, use_container_width=True, height=220)
        with col_chart:
            st.plotly_chart(diesel_runtime_fuel_chart(dg["day_nums"], dg["diesel_runtime_daily"], site["history"]["diesel"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown('<div class="section-sub" style="margin-top:6px;">Specific fuel consumption (L/hour)</div>', unsafe_allow_html=True)
        st.plotly_chart(specific_fuel_chart(dg["day_nums"], dg["specific_fuel_daily"]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ---- V. System Reliability ----
    with st.container(border=True):
        rel = r["reliability"]
        st.markdown('<div class="section-title">V. System reliability</div><div class="section-rule"></div>', unsafe_allow_html=True)
        col_tbl, col_chart = st.columns([1, 1.3])
        with col_tbl:
            metric_rows = pd.DataFrame([
                ["System availability (%)", f"{rel['system_availability_pct']:.1f}%", "100%"],
                ["Alarm events", str(rel["alarm_events_count"]), "0"],
            ], columns=["Metric", "Value", "Target"])
            st.dataframe(metric_rows, hide_index=True, use_container_width=True, height=120)
        with col_chart:
            st.plotly_chart(availability_trend_chart(rel["day_nums"], rel["availability_daily"]), use_container_width=True, config={"displayModeBar": False})
        if rel["alarm_events_count"] == 0:
            st.markdown('<div class="achv-item"><span class="achv-num">1.</span><span>The PV-BESS and genset systems combined covered 100% of the site\'s electricity needs with no alarm events.</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="achv-item"><span class="achv-num">1.</span><span>The system recorded {rel["alarm_events_count"]} alarm event(s) this period, reducing availability to {rel["system_availability_pct"]:.1f}%.</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        site_issues = [i for i in ISSUES if i["site_id"] == site_id]
        st.markdown(f'<div class="section-title">Site issues</div><div class="section-sub">{sum(1 for i in site_issues if i["status"]!="Resolved")} open at this site</div><div class="section-rule"></div>', unsafe_allow_html=True)
        issues_panel(site_issues, clickable=False)


# ===========================================================================
# ISSUES
# ===========================================================================
def render_issues():
    st.markdown('<div class="page-title">Operational issues</div><div class="page-breadcrumb">O&amp;M Business Intelligence</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        severity = st.selectbox("Severity", ["All severities", "Critical", "Warning", "Info"])
    with c2:
        status = st.selectbox("Status", ["All statuses", "Open", "In Progress", "Resolved"])
    filtered = [i for i in ISSUES if (severity == "All severities" or i["severity"] == severity) and (status == "All statuses" or i["status"] == status)]
    with st.container(border=True):
        st.markdown(f'<div class="section-title">Issues</div><div class="section-sub">{len(filtered)} matching current filters</div><div class="section-rule"></div>', unsafe_allow_html=True)
        issues_panel(filtered)


# ===========================================================================
# SUSTAINABILITY
# ===========================================================================
def render_sustainability():
    st.markdown('<div class="page-title">Sustainability report</div><div class="page-breadcrumb">O&amp;M Business Intelligence</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        sel_projects = st.multiselect("Projects", PROJECTS, default=list(PROJECTS), key="sus_projects")
    avail_sites = [s for s in SITES if s["project"] in sel_projects]
    with c2:
        sel_site_names = st.multiselect("Sites", [s["name"] for s in avail_sites], default=[s["name"] for s in avail_sites], key="sus_sites")
    with c3:
        range_label = st.selectbox("Date range", ["Last 7 days", "Last 14 days", "Last 30 days", "Month to date"], index=2, key="sus_range")
    days_map = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30, "Month to date": 19}
    scale = days_map[range_label] / 30

    chosen = [s for s in avail_sites if s["name"] in sel_site_names]
    savings = sustainability_savings(chosen, scale)

    with st.container(border=True):
        st.markdown(f'<div class="section-title">Executive summary · Financial &amp; environmental impact</div><div class="section-sub">{len(chosen)} sites selected · {days_map[range_label]}-day period</div><div class="section-rule"></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="font-size:16px;">Monthly cost savings</div>', unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        kpi_card(s1, "FROM FUEL VOLUME", fmt_en(savings["fuel_saved_l"]), "L", delta=-14.0, icon="\u26fd", icon_bg=WARNING)
        kpi_card(s2, "FROM COST OF FUEL", "IDR " + fmt_en(savings["cost_saved_idr"]), "", delta=-14.0, icon="$", icon_bg=BRAND)
        kpi_card(s3, "FROM GENSET MAINTENANCE", "IDR " + fmt_en(savings["maintenance_saved_idr"]), "", icon="\u2699", icon_bg="#3B6EA0")

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="font-size:16px;">Contribution to environment and society</div>', unsafe_allow_html=True)
        e1, e2, e3 = st.columns(3)
        kpi_card(e1, "CO2 EMISSIONS AVOIDED", fmt_en(savings["co2_avoided_ton"], 1), "T CO2", delta=-14.0, icon="\u2601", icon_bg=SUCCESS)
        kpi_card(e2, "EQUIVALENT TREES PLANTED", fmt_en(savings["trees_equivalent"]), "Trees", delta=-14.0, icon="T", icon_bg=BRAND_LIGHT)
        kpi_card(e3, "FAMILIES POWERED BY RENEWABLES", fmt_en(savings["families"]), "Families", icon="\u2302", icon_bg=BRAND)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Key highlights</div>', unsafe_allow_html=True)
        items = [
            f"Fuel savings reached {fmt_en(savings['fuel_saved_l'])} liters compared to genset-only electricity use.",
            f"Cost savings from fuel amounted to IDR {fmt_en(savings['cost_saved_idr'])}, plus IDR {fmt_en(savings['maintenance_saved_idr'])} from reduced genset maintenance.",
            f"Avoided {fmt_en(savings['co2_avoided_ton'], 1)} tons of CO2 emissions, equivalent to {fmt_en(savings['trees_equivalent'])} trees planted.",
            f"Renewable energy successfully powered {fmt_en(savings['families'])} families, supporting the transition to clean energy.",
        ]
        for idx, it in enumerate(items, start=1):
            st.markdown(f'<div class="achv-item"><span class="achv-num">{idx}.</span><span>{it}</span></div>', unsafe_allow_html=True)


# ===========================================================================
# REPORTS
# ===========================================================================
def render_client_report():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        company = st.selectbox("Client (Company)", COMPANIES)
    with c2:
        month_label = st.selectbox("Bulan", MONTH_NAMES_ID, index=TODAY.month - 1)
    with c3:
        year_label = st.selectbox("Tahun", [str(y) for y in range(2024, 2028)], index=2)

    sites_c = company_sites(SITES, company)
    kpis = compute_client_kpis(sites_c)

    st.markdown(f"""
    <div class="akartha-header">
      <h1>Monthly Performance Report</h1>
      <div class="sub">Bulan: <b>{month_label}</b> &nbsp;&nbsp; Tahun: <b>{year_label}</b> &nbsp;&nbsp; Client: <b>{company.replace('PT ', '')}</b></div>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">Matriks Ketercapaian</div><div class="section-rule"></div>', unsafe_allow_html=True)
        r1 = st.columns([1, 1, 1, 1, 1.3])
        kpi_card(r1[0], "LISTRIK TERSALURKAN", fmt_id(kpis["listrik"]), "kWh", icon="\u26a1", icon_bg=BRAND)
        kpi_card(r1[1], "PERSENTASE ENERGI BERSIH", fmt_id(kpis["ref_pct"], 2), "%", icon="\u2600", icon_bg=BRAND_LIGHT)
        kpi_card(r1[2], "JUMLAH SOLAR", fmt_id(kpis["jumlah_solar"]), "Liter", icon="\u26fd", icon_bg=WARNING)
        kpi_card(r1[3], "AVAILABILITY", fmt_id(kpis["availability_pct"], 2), "%", icon="\u2713", icon_bg=SUCCESS)
        with r1[4]:
            with st.container(border=True):
                st.plotly_chart(solar_split_donut(kpis["aeb_l"], kpis["client_l"]), use_container_width=True, config={"displayModeBar": False})

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        col_chart, col_side = st.columns([1.7, 1])
        with col_chart:
            with st.container(border=True):
                mix = sorted(sites_c, key=lambda s: s["db"]["load_actual_kwh"], reverse=True)[:12]
                labels = [s["name"] for s in mix]
                renewable = [max(0, s["db"]["load_actual_kwh"] - s["db"]["gen_production_kwh"]) for s in mix]
                genset = [s["db"]["gen_production_kwh"] for s in mix]
                if labels:
                    st.plotly_chart(energy_mix_bar(labels, renewable, genset), use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("No sites for this company.")
        with col_side:
            st.markdown('<div class="section-title">Key Achievements</div><div class="section-rule"></div>', unsafe_allow_html=True)
            for idx, item in enumerate(key_achievements_text(kpis, month_label, year_label), start=1):
                st.markdown(f'<div class="achv-item"><span class="achv-num">{idx}.</span><span>{item}</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title" style="margin-top:12px;">Critical Issue</div><div class="section-rule"></div>', unsafe_allow_html=True)
            site_ids = {s["id"] for s in sites_c}
            open_issues = [i for i in ISSUES if i["site_id"] in site_ids and i["status"] != "Resolved"]
            if open_issues:
                for i in open_issues[:4]:
                    st.markdown(f'<div style="font-size:12.5px;margin-bottom:6px;">{severity_badge(i["severity"])} {i["site_name"]} — {i["desc"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#6B7568;font-size:13px;">-- &nbsp; -- &nbsp; --</div>', unsafe_allow_html=True)


def render_tabular_report():
    fcol1, fcol2, fcol3 = st.columns([1, 1, 1.4])
    with fcol1:
        f_projects = st.multiselect("Project", PROJECTS, default=list(PROJECTS), key="tab_proj")
    with fcol2:
        f_companies = st.multiselect("Company", COMPANIES, default=list(COMPANIES), key="tab_comp")
    with fcol3:
        f_search = st.text_input("Search site / estate", "", key="tab_search")

    with st.expander("Choose columns to display", expanded=False):
        selected_keys = []
        for group, cols in COLUMN_GROUPS:
            st.markdown(f"**{group}**")
            row_cols = st.columns(3)
            for i, (key, label, unit) in enumerate(cols):
                unit_str = f" ({unit})" if unit else ""
                checked = row_cols[i % 3].checkbox(f"{label}{unit_str}", value=key in DEFAULT_KEYS, key=f"col_{key}")
                if checked:
                    selected_keys.append(key)

    filtered = [s for s in SITES if s["project"] in f_projects and s["company"] in f_companies]
    if f_search:
        q = f_search.lower()
        filtered = [s for s in filtered if q in s["name"].lower() or q in s["estate"].lower()]

    rows = [s["db"] for s in filtered]
    df = pd.DataFrame(rows)
    display_cols = [k for k in selected_keys if k in df.columns]
    display_df = df[display_cols].copy() if display_cols else pd.DataFrame()
    for c in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[c]):
            display_df[c] = display_df[c].round(2)
    display_df = display_df.rename(columns=LABEL_MAP)

    st.caption(f"{len(filtered)} sites \u00b7 {len(display_cols)} columns selected")
    st.dataframe(display_df, use_container_width=True, height=480)
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("Export CSV", data=csv_bytes, file_name="akartha_tabular_report.csv", mime="text/csv")


def render_reports():
    st.markdown('<div class="page-title">Reports</div><div class="page-breadcrumb">O&amp;M Business Intelligence</div>', unsafe_allow_html=True)
    tab_client, tab_tabular = st.tabs(["Client Report", "Tabular Report"])
    with tab_client:
        render_client_report()
    with tab_tabular:
        render_tabular_report()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
page = st.session_state.page
if page == "portfolio":
    render_portfolio()
elif page == "sites":
    render_sites()
elif page == "site_detail":
    render_site_detail(st.session_state.selected_site_id)
elif page == "issues":
    render_issues()
elif page == "sustainability":
    render_sustainability()
elif page == "reports":
    render_reports()
else:
    render_portfolio()
