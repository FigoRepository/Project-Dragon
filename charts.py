"""Matplotlib chart builders — shared between the Streamlit view and the PDF export
so the on-screen report and the downloaded PDF always match."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

BRAND_DARK = "#153327"
BRAND = "#2F6B48"
KHAKI = "#C9C6A2"
OLIVE = "#6E7C46"
TEXT = "#1B241D"
TEXT_MUTED = "#6B7568"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["text.color"] = TEXT
plt.rcParams["axes.edgecolor"] = "#CDD3BF"
plt.rcParams["axes.labelcolor"] = TEXT_MUTED
plt.rcParams["xtick.color"] = TEXT_MUTED
plt.rcParams["ytick.color"] = TEXT_MUTED


def _fig_to_png_bytes(fig, dpi=170):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


def solar_split_pie(aeb_l: float, client_l: float):
    fig, ax = plt.subplots(figsize=(4.2, 3.4))
    values = [max(aeb_l, 0.0001), max(client_l, 0.0001)]
    labels = ["Solar Akartha (AEB)", "Solar Client"]
    colors = [BRAND, KHAKI]
    wedges, _texts = ax.pie(
        values, colors=colors, startangle=90, counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
    )
    ax.set_title("Solar Akartha vs. Solar Client", fontsize=11, fontweight="bold", color=BRAND_DARK, pad=10)
    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=1, frameon=False, fontsize=9)
    ax.axis("equal")
    return _fig_to_png_bytes(fig)


def energy_mix_bar(df_mix):
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    labels = df_mix["label"].tolist()
    renewable = df_mix["renewable_kwh"].tolist()
    genset = df_mix["genset_kwh"].tolist()
    y = range(len(labels))
    ax.barh(y, renewable, color=KHAKI, label="PV + BESS (kWh)")
    ax.barh(y, genset, left=renewable, color=BRAND_DARK, label="Genset (kWh)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Energy delivered (kWh)", fontsize=9)
    ax.set_title("Energy Mix per Site (Renewable vs. Genset)", fontsize=11, fontweight="bold", color=BRAND_DARK, pad=10)
    ax.legend(loc="lower right", frameon=False, fontsize=8.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_png_bytes(fig)
