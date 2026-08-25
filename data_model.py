"""
Python port of the Akartha O&M Dashboard's mock data model (originally the
React/JSX artifact). Same seeded-RNG algorithm, same 85-site roster, same
derived formulas — so figures are consistent with the earlier JSX version.
"""
import json
import math
from datetime import date, timedelta

with open("rows_data.json", encoding="utf-8") as f:
    ROWS = json.load(f)

PROJECTS = ["Alpha", "Alpha Extension", "Bravo", "Charlie", "Charlie Extension", "Delta", "Echo", "Foxtrot"]
ISSUE_PRONE_KEYS = {"MBE|EU eks MB2", "SNE|EU", "FLE|EU & 2", "AME|EU", "MT1|EU & 4, 5", "LYE|EU & 3", "SKE|EU"}
CRITICAL_KEY = "MBE|EU eks MB2"

TODAY = date(2026, 8, 19)
HOLDING_MAP = {"PT Sawit Sukses Sejahtera": "SGA"}


def get_holding(company):
    return HOLDING_MAP.get(company, "TPA")


def day_label(offset):
    d = TODAY - timedelta(days=offset)
    return d.strftime("%d %b")


REPORT_MONTH_LABEL = "August 2026"


class SeededRandom:
    """Exact port of the JS LCG used in the dashboard (Park-Miller minimal standard)."""
    def __init__(self, seed):
        s = seed % 2147483647
        if s <= 0:
            s += 2147483646
        self.s = s

    def __call__(self):
        self.s = (self.s * 16807) % 2147483647
        return (self.s - 1) / 2147483646


def gen_series(rng, base, variance, drift_amplitude=0, floor=0, ceil_val=math.inf):
    out = []
    for i in range(29, -1, -1):
        drift = math.sin((29 - i) / 4.5) * drift_amplitude
        noise = (rng() - 0.5) * variance
        level = base + drift + noise
        out.append(min(ceil_val, max(floor, round(level * 10) / 10)))
    return out


def slug_afd(s):
    import re
    s = s.lower().replace(",", "").replace("&", "-")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def build_site(row, index):
    project, company, estate, code, afdeling, genset_raw, pv_raw, bess_raw = row
    capacity_kwp = round(pv_raw)
    bess_capacity_kwh = round(bess_raw)
    genset_capacity_kva = genset_raw
    site_id = f"{code.lower()}-{slug_afd(afdeling)}-{index}"
    is_eu = afdeling.startswith("EU")
    name = f"{estate} · {afdeling}" if is_eu else f"{estate} · Afd. {afdeling}"

    rng = SeededRandom(index * 97 + 13)
    psh = 4.3 + rng() * 0.7
    pr = 0.72 + rng() * 0.14
    baseline_pv = capacity_kwp * psh * pr
    baseline_load = capacity_kwp * (0.35 + rng() * 0.25) * 20

    pv_history = gen_series(rng, baseline_pv, baseline_pv * 0.12, baseline_pv * 0.05, baseline_pv * 0.4)
    cons_history = gen_series(rng, baseline_load, baseline_load * 0.08, baseline_load * 0.03, baseline_load * 0.5)
    ref_history = [min(98, max(35, round((pv / c) * 1000) / 10)) for pv, c in zip(pv_history, cons_history)]
    diesel_history = []
    for i in range(30):
        shortfall = max(0, cons_history[i] - pv_history[i] * 0.9)
        diesel_history.append(round(shortfall * (0.24 + rng() * 0.04) * 10) / 10)

    key = f"{code}|{afdeling}"
    is_critical = key == CRITICAL_KEY
    avail_base = 87.4 if is_critical else 96.5 + rng() * 3
    avail_history = gen_series(rng, avail_base, 1.6, 0, 78, 100)

    soc_now = round(20 + rng() * 70)
    bess_states = ["Charging", "Discharging", "Standby"]
    bess_status = bess_states[math.floor(rng() * len(bess_states))]
    if is_critical:
        bess_status = "Fault"

    soc_profile = []
    for h in range(24):
        if 6 <= h <= 15:
            v = 25 + ((h - 6) / 9) * 65 + (rng() - 0.5) * 6
        elif 15 < h <= 22:
            v = 90 - ((h - 15) / 7) * 55 + (rng() - 0.5) * 6
        else:
            v = 30 + (rng() - 0.5) * 8
        soc_profile.append({"hour": f"{h:02d}:00", "soc": round(min(100, max(5, v)))})

    avail_last = avail_history[-1]
    has_open_issue = key in ISSUE_PRONE_KEYS
    critical_open_count = 2 if is_critical else (1 if has_open_issue else 0)
    status = "Normal"
    if avail_last < 90 or bess_status == "Fault":
        status = "Critical"
    elif avail_last < 95 or critical_open_count > 0:
        status = "Warning"

    day_nums = list(range(1, 31))

    potential_pv_kwh = round(capacity_kwp * 14 * 30 * (0.55 + rng() * 0.15))
    sys_loss_pct = round((4 + rng() * 4) * 10) / 10
    curt_maint_pct = round(rng() * 3 * 10) / 10 if rng() > 0.7 else 0
    mismatch_pct = round((8 + rng() * 14) * 10) / 10
    outage_pct = round((2 + rng() * 3) * 10) / 10 if is_critical else 0
    utilized_pct = round((100 - sys_loss_pct - curt_maint_pct - mismatch_pct - outage_pct) * 10) / 10
    sys_loss_kwh = round(potential_pv_kwh * sys_loss_pct / 100)
    curt_maint_kwh = round(potential_pv_kwh * curt_maint_pct / 100)
    mismatch_kwh = round(potential_pv_kwh * mismatch_pct / 100)
    outage_kwh = round(potential_pv_kwh * outage_pct / 100)
    outage_hours = round(outage_pct * 3) if outage_pct > 0 else 0
    utilized_kwh = round(potential_pv_kwh * utilized_pct / 100)
    diesel_gen_kwh = round(potential_pv_kwh * (0.04 + rng() * 0.1))
    bess_discharge_kwh = round(potential_pv_kwh * (0.28 + rng() * 0.15))
    total_load_served_kwh = utilized_kwh + diesel_gen_kwh
    total_load_target_kwh = round(potential_pv_kwh * 0.93)
    ref_pct = round((utilized_kwh / total_load_served_kwh) * 1000) / 10 if total_load_served_kwh else 0

    max_daily_energy = round(baseline_load * 1.15)
    irradiation_history = gen_series(rng, 1350, 320, 250, 500, 2100)
    genset_kwh_daily = [round(l * 2.8 * 10) / 10 for l in diesel_history]
    bess_kwh_daily = [max(0, round(min(c * 0.35, c - pv_history[i] * 0.7))) for i, c in enumerate(cons_history)]
    pv_used_daily = [max(0, round(min(pv, cons_history[i]))) for i, pv in enumerate(pv_history)]
    genset_total = sum(genset_kwh_daily)
    pv_bess_total = sum(bess_kwh_daily) + sum(pv_used_daily)
    genset_share_pct = round((genset_total / (genset_total + pv_bess_total)) * 1000) / 10 if (genset_total + pv_bess_total) else 0
    pv_bess_share_pct = round((100 - genset_share_pct) * 10) / 10

    soc_min_daily = gen_series(rng, 30, 8, 5, 10, 60)
    soc_max_daily = gen_series(rng, 90, 6, 0, 70, 100)
    avg_dod = round(sum(soc_max_daily) / 30 - sum(soc_min_daily) / 30)
    max_dod = round(max(mx - mn for mx, mn in zip(soc_max_daily, soc_min_daily)))
    min_soc_overall = round(min(soc_min_daily))
    max_soc_overall = round(max(soc_max_daily))
    soh = 91 if is_critical else round(96 + rng() * 4)
    full_cycles_complete = round(10 + rng() * 20)
    soh_monthly = [{"month": m, "soh": soh if i == 3 else min(100, soh + (3 - i))} for i, m in enumerate(["May", "Jun", "Jul", "Aug"])]

    run_days = sum(1 for v in diesel_history if v > 0)
    total_run_time_hours = round(run_days * (1.5 + rng() * 2) * 10) / 10
    fuel_by_aeb = round(sum(diesel_history))
    fuel_by_client = 0
    total_fuel_consumption = fuel_by_aeb + fuel_by_client
    avg_specific_fuel_consumption = round((total_fuel_consumption / max(1, total_run_time_hours)) * 10) / 10
    number_of_starts = run_days
    diesel_runtime_daily = [round((l / (avg_specific_fuel_consumption or 11)) * 10) / 10 if l > 0 else 0 for l in diesel_history]
    specific_fuel_daily = [round((diesel_history[i] / diesel_runtime_daily[i]) * 10) / 10 if diesel_runtime_daily[i] > 0 else 0 for i in range(30)]

    alarm_events_count = critical_open_count + (1 if is_critical else 0)
    event_log_days = [4, 5, 18] if is_critical else ([12] if has_open_issue else [])

    # ---- Full DB-style extended fields (mirrors the AEB Data Asset workbook) ----
    inv_kva = round(capacity_kwp * 0.83)
    opt_days = round(180 + rng() * 500)
    opt_month = round((opt_days / 30) * 10) / 10
    cod_years_ago = 0.5 + rng() * 2.5
    act_cod = TODAY - timedelta(days=round(cod_years_ago * 365))
    load_per_day = round(sum(cons_history) / 30)
    cost_per_kwh_idr = round(2400 + rng() * 2600)
    cost_per_month_idr = round(load_per_day * 30 * cost_per_kwh_idr)
    total_cost_idr = round(cost_per_month_idr * opt_month)
    target_coe_idr = round(7500 + rng() * 1200)
    actual_coe_idr = round(target_coe_idr * (0.95 + rng() * 0.12))
    usd_rate = 15500
    spec_yield_target = round((3.2 + rng() * 0.6) * 100) / 100
    spec_yield_actual = round((spec_yield_target * (0.85 + rng() * 0.25)) * 100) / 100
    pvmod_target_kwh = round(potential_pv_kwh * 0.06)
    pvmod_actual_kwh = sys_loss_kwh
    pvmod_temp = round(pvmod_actual_kwh * 0.55)
    pvmod_soil = round(pvmod_actual_kwh * 0.28)
    pvmod_shading = max(0, pvmod_actual_kwh - pvmod_temp - pvmod_soil)
    inv_target_kwh = round(potential_pv_kwh * 0.03)
    inv_actual_kwh = round(potential_pv_kwh * (0.02 + rng() * 0.02))
    inv_conversion = round(inv_actual_kwh * 0.6)
    inv_mppt = round(inv_actual_kwh * 0.3)
    inv_standby = max(0, inv_actual_kwh - inv_conversion - inv_mppt)
    dist_target_kwh = round(total_load_served_kwh * 0.02)
    dist_actual_kwh = round(total_load_served_kwh * (0.015 + rng() * 0.02))
    dist_cable = round(dist_actual_kwh * 0.65)
    dist_transformer = max(0, dist_actual_kwh - dist_cable)
    gen_maintenance_count = round(1 + rng() * 2)
    aeb_share_pct = 0.65 + rng() * 0.3
    target_aeb_l = round(total_fuel_consumption * 1.05 * aeb_share_pct)
    act_aeb_l = round(total_fuel_consumption * aeb_share_pct)
    target_client_l = round(total_fuel_consumption * 1.05 * (1 - aeb_share_pct))
    act_client_l = max(0, total_fuel_consumption - act_aeb_l)
    frequency_hz = round((49.8 + rng() * 0.4) * 100) / 100
    voltage_v = round(380 + rng() * 20)
    v_fluct_v = round((1 + rng() * 3) * 10) / 10
    power_factor = round((0.92 + rng() * 0.06) * 100) / 100
    renewable_kwh_for_env = total_load_served_kwh - diesel_gen_kwh
    co2_kg = round(renewable_kwh_for_env * 0.85)
    nox_kg = round(renewable_kwh_for_env * 0.00062 * 100) / 100
    sox_kg = round(renewable_kwh_for_env * 0.00108 * 100) / 100
    pm_kg = round(renewable_kwh_for_env * 0.00006 * 100) / 100
    c_credit_idr = round(co2_kg * 70)

    db = dict(
        no=index + 1, project=project, holding=get_holding(company), company=company, estate=estate, site=afdeling,
        pv_kwp=capacity_kwp, bess_kwh=bess_capacity_kwh, inv_kva=inv_kva, act_cod=act_cod, opt_days=opt_days, opt_month=opt_month,
        load_per_day=load_per_day, cost_per_month_idr=cost_per_month_idr, total_cost_idr=total_cost_idr,
        target_coe_idr=target_coe_idr, target_coe_usd=round((target_coe_idr / usd_rate) * 10000) / 10000,
        actual_coe_idr=actual_coe_idr, actual_coe_usd=round((actual_coe_idr / usd_rate) * 10000) / 10000,
        load_target_kwh=total_load_target_kwh, load_actual_kwh=total_load_served_kwh,
        load_diff_pct=round(((total_load_served_kwh - total_load_target_kwh) / total_load_target_kwh) * 1000) / 10 if total_load_target_kwh else 0,
        pv_target_kwh=round(potential_pv_kwh * 0.93), pv_actual_kwh=potential_pv_kwh,
        pv_excess_pct=round(((potential_pv_kwh - round(potential_pv_kwh * 0.93)) / round(potential_pv_kwh * 0.93)) * 1000) / 10 if potential_pv_kwh else 0,
        re_penetr_pct=ref_pct,
        spec_yield_target=spec_yield_target, spec_yield_actual=spec_yield_actual,
        spec_yield_diff_pct=round(((spec_yield_actual - spec_yield_target) / spec_yield_target) * 1000) / 10 if spec_yield_target else 0,
        pvmod_target_kwh=pvmod_target_kwh, pvmod_actual_kwh=pvmod_actual_kwh, pvmod_temp=pvmod_temp, pvmod_soil=pvmod_soil, pvmod_shading=pvmod_shading,
        inv_target_kwh=inv_target_kwh, inv_actual_kwh=inv_actual_kwh, inv_conversion=inv_conversion, inv_mppt=inv_mppt, inv_standby=inv_standby,
        batt_dod=avg_dod, batt_soh=soh, batt_max_soc=max_soc_overall, batt_min_soc=min_soc_overall, batt_cycle=full_cycles_complete,
        dist_target_kwh=dist_target_kwh, dist_actual_kwh=dist_actual_kwh, dist_cable=dist_cable, dist_transformer=dist_transformer,
        gen_production_kwh=diesel_gen_kwh, gen_fuel_lph=avg_specific_fuel_consumption,
        gen_spec_fuel_lpkwh=round((total_fuel_consumption / diesel_gen_kwh) * 100) / 100 if diesel_gen_kwh else 0,
        gen_loading_pct=genset_share_pct, gen_opt_hour=total_run_time_hours, gen_start_stop=number_of_starts, gen_maintenance=gen_maintenance_count,
        fuel_target_aeb_l=target_aeb_l, fuel_act_aeb_l=act_aeb_l, fuel_target_client_l=target_client_l, fuel_act_client_l=act_client_l,
        pq_frequency_hz=frequency_hz, pq_voltage_v=voltage_v, pq_vfluct_v=v_fluct_v, pq_pf=power_factor,
        env_co2_kg=co2_kg, env_nox_kg=nox_kg, env_sox_kg=sox_kg, env_pm_kg=pm_kg, env_ccredit_idr=c_credit_idr,
    )

    return dict(
        id=site_id, project=project, company=company, estate=estate, code=code, afdeling=afdeling, name=name,
        capacity_kwp=capacity_kwp, bess_capacity_kwh=bess_capacity_kwh, genset_capacity_kva=genset_capacity_kva,
        pv_generation_today=pv_history[-1], consumption_today=cons_history[-1], ref_today=ref_history[-1],
        diesel_today=diesel_history[-1], availability_today=avail_last, bess_soc=soc_now, bess_status=bess_status,
        bess_soc_profile=soc_profile, bess_soh=soh, critical_open_count=critical_open_count, status=status,
        history=dict(
            dates=[day_label(29 - i) for i in range(30)], day_nums=day_nums, pv=pv_history, consumption=cons_history,
            ref=ref_history, diesel=diesel_history, availability=avail_history,
        ),
        specific_yield=round((pv_history[-1] / capacity_kwp) * 100) / 100 if capacity_kwp else 0,
        performance_ratio=round(pr * 1000) / 10,
        report=dict(
            energy_utilization=dict(
                potential_pv_kwh=potential_pv_kwh, potential_pv_target_kwh=round(potential_pv_kwh * 0.93),
                sys_loss_pct=sys_loss_pct, curt_maint_pct=curt_maint_pct, mismatch_pct=mismatch_pct, outage_pct=outage_pct,
                sys_loss_kwh=sys_loss_kwh, curt_maint_kwh=curt_maint_kwh, mismatch_kwh=mismatch_kwh, outage_kwh=outage_kwh,
                outage_hours=outage_hours, utilized_pct=utilized_pct, utilized_kwh=utilized_kwh, diesel_gen_kwh=diesel_gen_kwh,
                bess_discharge_kwh=bess_discharge_kwh, total_load_served_kwh=total_load_served_kwh,
                total_load_target_kwh=total_load_target_kwh, ref_pct=ref_pct,
            ),
            generation=dict(
                day_nums=day_nums, max_daily_energy=max_daily_energy, irradiation_history=irradiation_history,
                genset_kwh_daily=genset_kwh_daily, bess_kwh_daily=bess_kwh_daily, pv_used_daily=pv_used_daily,
                genset_share_pct=genset_share_pct, pv_bess_share_pct=pv_bess_share_pct,
            ),
            bess=dict(
                avg_dod=avg_dod, max_dod=max_dod, min_soc_overall=min_soc_overall, max_soc_overall=max_soc_overall,
                soh=soh, full_cycles_complete=full_cycles_complete, soc_min_daily=soc_min_daily, soc_max_daily=soc_max_daily,
                soh_monthly=soh_monthly, day_nums=day_nums,
            ),
            diesel=dict(
                total_run_time_hours=total_run_time_hours, fuel_by_aeb=fuel_by_aeb, fuel_by_client=fuel_by_client,
                total_fuel_consumption=total_fuel_consumption, avg_specific_fuel_consumption=avg_specific_fuel_consumption,
                number_of_starts=number_of_starts, diesel_runtime_daily=diesel_runtime_daily, specific_fuel_daily=specific_fuel_daily,
                day_nums=day_nums,
            ),
            reliability=dict(
                system_availability_pct=avail_last, alarm_events_count=alarm_events_count, event_log_days=event_log_days,
                availability_daily=avail_history, day_nums=day_nums,
            ),
        ),
        db=db,
    )


SITES = [build_site(row, i) for i, row in enumerate(ROWS)]
SITES_BY_ID = {s["id"]: s for s in SITES}
COMPANIES = sorted(set(s["company"] for s in SITES))

ISSUE_SEEDS = [
    dict(code="MBE", afdeling="EU eks MB2", device="BESS Rack 1", category="BESS", severity="Critical", desc="Cell temperature deviation exceeds threshold in Rack 1, module 4", status="Open", days_ago=1),
    dict(code="MBE", afdeling="EU eks MB2", device="Inverter String B1", category="PV Array", severity="Critical", desc="Ground fault detected, string isolated automatically", status="In Progress", days_ago=2),
    dict(code="MBE", afdeling="EU eks MB2", device="Switchgear Room", category="Electrical", severity="Critical", desc="Arc-flash PPE stock below minimum at site store", status="Open", days_ago=1),
    dict(code="SNE", afdeling="EU", device="Genset Unit 1", category="Genset", severity="Warning", desc="Auto-transfer switch delayed engagement during grid outage", status="Open", days_ago=3),
    dict(code="FLE", afdeling="EU & 2", device="Inverter String A2", category="PV Array", severity="Warning", desc="DC input imbalance across MPPT channel 3", status="Open", days_ago=1),
    dict(code="AME", afdeling="EU", device="Weather Station", category="Electrical", severity="Info", desc="Irradiance sensor readings intermittent, cleaning scheduled", status="Open", days_ago=5),
    dict(code="SGE", afdeling="EU & 1", device="BESS Rack 2", category="BESS", severity="Warning", desc="Containment ventilation triggered by off-gas sensor, resolved after purge", status="Resolved", days_ago=6),
    dict(code="MT1", afdeling="EU & 4, 5", device="Step-up Transformer", category="Electrical", severity="Warning", desc="Oil temperature trending above baseline under peak load", status="In Progress", days_ago=2),
    dict(code="LYE", afdeling="EU & 3", device="Genset Unit 1", category="Genset", severity="Info", desc="Fuel filter due for replacement within 50 operating hours", status="Open", days_ago=4),
    dict(code="SKE", afdeling="EU", device="Inverter String A1", category="PV Array", severity="Warning", desc="Soiling loss estimate above 8 percent, wash crew requested", status="Open", days_ago=2),
    dict(code="KKE", afdeling="EU & 3", device="BESS Rack 1", category="BESS", severity="Info", desc="State of health degraded to 91 percent, within expected range", status="Resolved", days_ago=9),
    dict(code="SNE", afdeling="EU", device="Site Perimeter", category="Safety", severity="Warning", desc="Fall-arrest anchor point inspection overdue on array walkway", status="Open", days_ago=3),
]


def _find_site(code, afdeling):
    for s in SITES:
        if s["code"] == code and s["afdeling"] == afdeling:
            return s
    return SITES[0]


ISSUES = []
for i, it in enumerate(ISSUE_SEEDS):
    site = _find_site(it["code"], it["afdeling"])
    d = TODAY - timedelta(days=it["days_ago"])
    ISSUES.append(dict(
        id=f"ISS-{i + 1:03d}", site_id=site["id"], site_name=site["name"],
        device=it["device"], category=it["category"], severity=it["severity"], desc=it["desc"],
        status=it["status"], date=d.strftime("%d %b %Y"),
    ))

RANGE_OPTIONS = [
    {"key": "7d", "label": "Last 7 days", "days": 7},
    {"key": "14d", "label": "Last 14 days", "days": 14},
    {"key": "30d", "label": "Last 30 days", "days": 30},
    {"key": "mtd", "label": "Month to date", "days": 19},
]


def compute_range_indices(date_mode, range_key, custom_start=None, custom_end=None):
    total = 30
    if date_mode == "custom" and custom_start and custom_end:
        start_idx = total - 1 - (TODAY - custom_start).days
        end_idx = total - 1 - (TODAY - custom_end).days
        start_idx = max(0, min(total - 1, start_idx))
        end_idx = max(0, min(total - 1, end_idx))
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        return start_idx, end_idx
    days = next((r["days"] for r in RANGE_OPTIONS if r["key"] == range_key), 30)
    return total - days, total - 1
