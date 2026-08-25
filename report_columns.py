"""Column catalog for the Tabular Report, grouped for the column picker."""

COLUMN_GROUPS = [
    ("Identity & Capacity", [
        ("no", "No", None), ("project", "Project", None), ("holding", "Holding", None),
        ("company", "Company", None), ("estate", "Estate", None), ("site", "Site / Afdeling", None),
        ("pv_kwp", "PV", "kWp"), ("bess_kwh", "BESS", "kWh"), ("inv_kva", "INV", "kVA"),
        ("act_cod", "Act. COD", None), ("opt_days", "Opt. Days", "days"), ("opt_month", "Opt. Month", "months"),
    ]),
    ("Cost", [
        ("load_per_day", "Load", "kWh/day"), ("cost_per_month_idr", "Cost", "IDR/month"),
        ("total_cost_idr", "Total Cost", "IDR"), ("target_coe_idr", "Target COE", "IDR/kWh"),
        ("actual_coe_idr", "Actual COE", "IDR/kWh"),
    ]),
    ("Load Supplied", [
        ("load_target_kwh", "Target", "kWh"), ("load_actual_kwh", "Actual", "kWh"), ("load_diff_pct", "Diff", "%"),
    ]),
    ("PV Energy Production", [
        ("pv_target_kwh", "Target", "kWh"), ("pv_actual_kwh", "Actual", "kWh"),
        ("pv_excess_pct", "Excess", "%"), ("re_penetr_pct", "RE Penetr.", "%"),
    ]),
    ("Specific Yield", [
        ("spec_yield_target", "Target", "kWh/kWp/day"), ("spec_yield_actual", "Actual", "kWh/kWp"),
        ("spec_yield_diff_pct", "Diff", "%"),
    ]),
    ("PV Module Losses", [
        ("pvmod_target_kwh", "Target", "kWh"), ("pvmod_actual_kwh", "Actual", "kWh"),
        ("pvmod_temp", "Temp.", "kWh"), ("pvmod_soil", "Soil", "kWh"), ("pvmod_shading", "Shading", "kWh"),
    ]),
    ("Inverter Losses", [
        ("inv_target_kwh", "Target", "kWh"), ("inv_actual_kwh", "Actual", "kWh"),
        ("inv_conversion", "Conversion", "kWh"), ("inv_mppt", "MPPT", "kWh"), ("inv_standby", "Stand by", "kWh"),
    ]),
    ("Battery Performance", [
        ("batt_dod", "DoD", "%"), ("batt_soh", "SoH", "%"), ("batt_max_soc", "Max SoC", "%"),
        ("batt_min_soc", "Min SoC", "%"), ("batt_cycle", "Cycle", "times"),
    ]),
    ("Distribution Losses", [
        ("dist_target_kwh", "Target", "kWh"), ("dist_actual_kwh", "Actual", "kWh"),
        ("dist_cable", "Cable DC/AC", "kWh"), ("dist_transformer", "Transformer", "kWh"),
    ]),
    ("Genset Performance", [
        ("gen_production_kwh", "Production", "kWh"), ("gen_fuel_lph", "Fuel", "L/h"),
        ("gen_spec_fuel_lpkwh", "Spec. Fuel", "L/kWh"), ("gen_loading_pct", "Loading", "%"),
        ("gen_opt_hour", "Opt. Hour", "hour"), ("gen_start_stop", "Start-Stop", "times"),
        ("gen_maintenance", "Maintenance", "times"),
    ]),
    ("Fuel Savings", [
        ("fuel_target_aeb_l", "Target AEB", "L"), ("fuel_act_aeb_l", "Act. AEB", "L"),
        ("fuel_target_client_l", "Target Client", "L"), ("fuel_act_client_l", "Act. Client", "L"),
    ]),
    ("Power Quality", [
        ("pq_frequency_hz", "Frequency", "Hz"), ("pq_voltage_v", "Voltage", "V"),
        ("pq_vfluct_v", "V Fluct.", "V"), ("pq_pf", "PF", None),
    ]),
    ("Environmental Performance (Reduction)", [
        ("env_co2_kg", "CO2", "kg CO2"), ("env_nox_kg", "NOx", "kg NOx"), ("env_sox_kg", "SOx", "kg SOx"),
        ("env_pm_kg", "PM", "kg PM2.5"), ("env_ccredit_idr", "C Credit", "IDR"),
    ]),
]

LABEL_MAP = {key: label for _g, cols in COLUMN_GROUPS for key, label, _u in cols}
DEFAULT_KEYS = ["project", "company", "estate", "site", "pv_kwp", "bess_kwh",
                "load_actual_kwh", "re_penetr_pct", "gen_production_kwh",
                "fuel_act_aeb_l", "fuel_act_client_l", "env_co2_kg"]
