"""
Aggregation and derived-metric calculations for the Client Report.
Formulas follow the Akartha O&M Dashboard Calculation Matrix.
"""
import numpy as np
import pandas as pd
from utils import fmt_id

DIESEL_ENERGY_DENSITY_KWH_PER_L = 3.2  # used only where a genset-only baseline is needed
CO2_KG_PER_TREE_PER_YEAR = 21
CARBON_PRICE_IDR_PER_KG = 70


def company_slice(df: pd.DataFrame, company: str) -> pd.DataFrame:
    return df[df["company"] == company].copy()


def safe_sum(df, col):
    return float(df[col].fillna(0).sum()) if col in df.columns else 0.0


def safe_wavg(df, value_col, weight_col):
    w = df[weight_col].fillna(0)
    v = df[value_col].fillna(0)
    total_w = w.sum()
    if total_w <= 0:
        return float(v.mean()) if len(v) else 0.0
    return float((v * w).sum() / total_w)


def compute_client_kpis(df_company: pd.DataFrame) -> dict:
    """Core + sustainability KPIs for one company's site slice."""
    listrik = safe_sum(df_company, "load_actual_kwh")
    load_target = safe_sum(df_company, "load_target_kwh")
    ref_pct = safe_wavg(df_company, "re_penetr_pct", "load_actual_kwh")
    aeb_l = safe_sum(df_company, "fuel_act_aeb_l")
    client_l = safe_sum(df_company, "fuel_act_client_l")
    jumlah_solar = aeb_l + client_l

    availability_pct = (listrik / load_target * 100) if load_target > 0 else np.nan

    co2_kg = safe_sum(df_company, "env_co2_kg")
    co2_ton = co2_kg / 1000
    trees_equiv = co2_kg / CO2_KG_PER_TREE_PER_YEAR

    target_fuel = safe_sum(df_company, "fuel_target_aeb_l") + safe_sum(df_company, "fuel_target_client_l")
    diesel_savings_l = max(0.0, target_fuel - jumlah_solar)

    return {
        "listrik_tersalurkan_kwh": listrik,
        "load_target_kwh": load_target,
        "ref_pct": ref_pct,
        "jumlah_solar_l": jumlah_solar,
        "availability_pct": availability_pct,
        "aeb_l": aeb_l,
        "client_l": client_l,
        "co2_avoided_ton": co2_ton,
        "trees_equivalent": trees_equiv,
        "diesel_savings_l": diesel_savings_l,
        "n_sites": len(df_company),
    }


def pct_delta(current, previous):
    if previous is None or previous == 0 or previous != previous:  # NaN-safe
        return None
    if current is None or current != current:
        return None
    return (current - previous) / previous * 100


def build_deltas(current_kpis: dict, previous_kpis: dict | None) -> dict:
    if not previous_kpis:
        return {k: None for k in current_kpis}
    keys = ["listrik_tersalurkan_kwh", "ref_pct", "jumlah_solar_l", "availability_pct",
            "co2_avoided_ton", "trees_equivalent", "diesel_savings_l"]
    return {k: pct_delta(current_kpis.get(k), previous_kpis.get(k)) for k in keys}


def energy_mix_by_site(df_company: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """Renewable (PV+BESS-served) vs. Genset energy per site, for the mix chart."""
    d = df_company.copy()
    d["genset_kwh"] = d["gen_production_kwh"].fillna(0)
    d["renewable_kwh"] = (d["load_actual_kwh"].fillna(0) - d["genset_kwh"]).clip(lower=0)
    d["label"] = d["estate"] + " \u00b7 " + d["site"]
    d = d.sort_values("load_actual_kwh", ascending=False).head(top_n)
    return d[["label", "renewable_kwh", "genset_kwh"]]


def key_achievements_text(kpis: dict, deltas: dict, month_label: str, year_label: str) -> list[str]:
    def arrow_word(d):
        if d is None:
            return "tercatat"
        return "meningkat" if d >= 0 else "menurun"

    items = []
    d_listrik = deltas.get("listrik_tersalurkan_kwh")
    listrik_txt = f"Penggunaan energi selama bulan {month_label} {year_label} sebesar {fmt_id(kpis['listrik_tersalurkan_kwh'])} kWh"
    if d_listrik is not None:
        listrik_txt += f" ({arrow_word(d_listrik)} {fmt_id(abs(d_listrik), 1)}% dibanding bulan lalu)."
    else:
        listrik_txt += "."
    items.append(listrik_txt)

    d_solar = deltas.get("jumlah_solar_l")
    if kpis["jumlah_solar_l"] == 0:
        items.append(f"Tidak terdapat penggunaan solar selama bulan {month_label} {year_label}, dengan konsumsi solar tercatat sebesar 0 Liter.")
    else:
        solar_txt = f"Konsumsi solar selama bulan {month_label} {year_label} tercatat sebesar {fmt_id(kpis['jumlah_solar_l'])} Liter"
        if d_solar is not None:
            solar_txt += f" ({arrow_word(d_solar)} {fmt_id(abs(d_solar), 1)}% dibanding bulan lalu)."
        else:
            solar_txt += "."
        items.append(solar_txt)

    d_ref = deltas.get("ref_pct")
    ref_txt = f"Sebesar {fmt_id(kpis['ref_pct'], 2)}% energi pada bulan {month_label} {year_label} berasal dari PLTS"
    if d_ref is not None:
        ref_txt += f" ({arrow_word(d_ref)} {fmt_id(abs(d_ref), 2)}% dibanding bulan sebelumnya)."
    else:
        ref_txt += "."
    items.append(ref_txt)

    if kpis["availability_pct"] == kpis["availability_pct"]:  # not NaN
        items.append(
            f"Ketersediaan sistem (Availability) tercatat sebesar {fmt_id(kpis['availability_pct'], 2)}% "
            f"dari target penyaluran beban, dengan {kpis['n_sites']} site aktif dalam laporan ini."
        )

    items.append(
        f"Kontribusi lingkungan: {fmt_id(kpis['co2_avoided_ton'], 1)} ton CO2 berhasil dihindari, "
        f"setara dengan {fmt_id(kpis['trees_equivalent'])} pohon, dengan penghematan solar sebesar "
        f"{fmt_id(kpis['diesel_savings_l'])} Liter dibanding baseline."
    )
    return items
