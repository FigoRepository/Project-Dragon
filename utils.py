"""Shared formatting helpers — Indonesian-style number formatting (. thousands, , decimals)."""


def fmt_id(value, decimals=0):
    if value is None or value != value:  # None or NaN
        return "-"
    s = f"{value:,.{decimals}f}"
    s = s.replace(",", "\u2063").replace(".", ",").replace("\u2063", ".")
    return s


def fmt_pct(value, decimals=1):
    if value is None or value != value:
        return "-"
    return fmt_id(value, decimals) + "%"
