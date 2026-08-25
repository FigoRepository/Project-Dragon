"""Aggregation & derived-metric calculations for Client Report / Sustainability,
operating on the mock data model (data_model.SITES)."""
from utils import fmt_id

CO2_KG_PER_TREE_PER_YEAR = 21
DIESEL_PRICE_IDR = 16000
MAINTENANCE_RATE_IDR_PER_HOUR = 150000
FAMILY_MONTHLY_KWH = 150


def company_sites(sites, company):
    return [s for s in sites if s["company"] == company]


def sum_field(sites, path):
    total = 0
    for s in sites:
        d = s["db"]
        total += d.get(path, 0) or 0
    return total


def compute_client_kpis(sites_subset):
    if not sites_subset:
        return dict(listrik=0, load_target=0, ref_pct=0, jumlah_solar=0, availability_pct=0,
                    aeb_l=0, client_l=0, co2_ton=0, trees=0, diesel_savings_l=0, n_sites=0)
    listrik = sum_field(sites_subset, "load_actual_kwh")
    load_target = sum_field(sites_subset, "load_target_kwh")
    weighted_ref = sum(s["db"]["re_penetr_pct"] * s["db"]["load_actual_kwh"] for s in sites_subset)
    ref_pct = weighted_ref / listrik if listrik > 0 else (sum(s["db"]["re_penetr_pct"] for s in sites_subset) / len(sites_subset))
    aeb_l = sum_field(sites_subset, "fuel_act_aeb_l")
    client_l = sum_field(sites_subset, "fuel_act_client_l")
    jumlah_solar = aeb_l + client_l
    availability_pct = (listrik / load_target * 100) if load_target > 0 else 0
    co2_kg = sum_field(sites_subset, "env_co2_kg")
    co2_ton = co2_kg / 1000
    trees = co2_kg / CO2_KG_PER_TREE_PER_YEAR
    target_fuel = sum_field(sites_subset, "fuel_target_aeb_l") + sum_field(sites_subset, "fuel_target_client_l")
    diesel_savings_l = max(0.0, target_fuel - jumlah_solar)
    return dict(
        listrik=listrik, load_target=load_target, ref_pct=ref_pct, jumlah_solar=jumlah_solar,
        availability_pct=availability_pct, aeb_l=aeb_l, client_l=client_l, co2_ton=co2_ton,
        trees=trees, diesel_savings_l=diesel_savings_l, n_sites=len(sites_subset),
    )


def key_achievements_text(kpis, month_label, year_label):
    items = [
        f"Penggunaan energi selama bulan {month_label} {year_label} sebesar {fmt_id(kpis['listrik'])} kWh, "
        f"dikonsolidasikan dari {kpis['n_sites']} site aktif.",
    ]
    if kpis["jumlah_solar"] == 0:
        items.append(f"Tidak terdapat penggunaan solar selama bulan {month_label} {year_label}.")
    else:
        items.append(f"Konsumsi solar selama bulan {month_label} {year_label} tercatat sebesar {fmt_id(kpis['jumlah_solar'])} Liter.")
    items.append(f"Sebesar {fmt_id(kpis['ref_pct'], 2)}% energi pada bulan {month_label} {year_label} berasal dari PLTS.")
    items.append(f"Ketersediaan sistem (Availability) tercatat sebesar {fmt_id(kpis['availability_pct'], 2)}% dari target penyaluran beban.")
    items.append(
        f"Kontribusi lingkungan: {fmt_id(kpis['co2_ton'], 1)} ton CO2 berhasil dihindari, setara dengan "
        f"{fmt_id(kpis['trees'])} pohon, dengan penghematan solar sebesar {fmt_id(kpis['diesel_savings_l'])} Liter."
    )
    return items


def sustainability_savings(sites_subset, scale=1.0):
    fuel_saved_l = max(0.0, (sum_field(sites_subset, "fuel_target_aeb_l") + sum_field(sites_subset, "fuel_target_client_l"))
                        - (sum_field(sites_subset, "fuel_act_aeb_l") + sum_field(sites_subset, "fuel_act_client_l"))) * scale
    cost_saved_idr = fuel_saved_l * DIESEL_PRICE_IDR
    baseline_run_hours = sum(s["report"]["diesel"]["total_run_time_hours"] * 1.2 for s in sites_subset)
    actual_run_hours = sum(s["report"]["diesel"]["total_run_time_hours"] for s in sites_subset)
    hours_saved = max(0.0, baseline_run_hours - actual_run_hours) * scale
    maintenance_saved_idr = hours_saved * MAINTENANCE_RATE_IDR_PER_HOUR
    co2_avoided_kg = sum_field(sites_subset, "env_co2_kg") * scale
    trees_equiv = co2_avoided_kg / CO2_KG_PER_TREE_PER_YEAR
    renewable_kwh = sum(s["report"]["energy_utilization"]["total_load_served_kwh"] - s["report"]["energy_utilization"]["diesel_gen_kwh"] for s in sites_subset)
    families = (renewable_kwh * scale) / FAMILY_MONTHLY_KWH
    return dict(
        fuel_saved_l=fuel_saved_l, cost_saved_idr=cost_saved_idr, maintenance_saved_idr=maintenance_saved_idr,
        co2_avoided_ton=co2_avoided_kg / 1000, trees_equivalent=trees_equiv, families=families,
    )
