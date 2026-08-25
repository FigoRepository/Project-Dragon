"""Plotly chart builders — ported visual language from the JSX dashboard (recharts)."""
import plotly.graph_objects as go

C = dict(
    brand="#2F6B48", brand_dark="#1F4A32", brand_light="#4C8A63",
    olive="#6E7C46", khaki="#C9C6A2", cream_muted="#B9C2AE",
    text="#1B241D", text_muted="#6B7568", text_faint="#98A08F",
    border="#E1E4D7", warning="#B9812C", critical="#B8433A", info="#3B6EA0",
    success="#2E8B57",
)

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=C["text_muted"], size=12),
    margin=dict(l=8, r=8, t=28, b=8),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
)


def pv_consumption_trend(dates, pv, consumption):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=pv, name="PV generation", mode="lines", fill="tozeroy",
                              line=dict(color=C["brand"], width=2), fillcolor="rgba(47,107,72,0.18)"))
    fig.add_trace(go.Scatter(x=dates, y=consumption, name="Consumption", mode="lines",
                              line=dict(color=C["warning"], width=2)))
    fig.update_layout(**BASE_LAYOUT, height=260)
    fig.update_yaxes(title=None, gridcolor=C["border"], zeroline=False)
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def ref_trend(dates, ref):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=ref, name="REF %", mode="lines",
                              line=dict(color=C["success"], width=2.4)))
    fig.update_layout(**BASE_LAYOUT, height=180, showlegend=False)
    fig.update_yaxes(range=[0, 100], gridcolor=C["border"])
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def waterfall_chart(steps):
    """steps: list of dicts {name, value, is_total, color, label_text}"""
    names = [s["name"] for s in steps]
    values = [s["value"] for s in steps]
    measures = ["absolute" if s["is_total"] else "relative" for s in steps]
    texts = [s["label_text"] for s in steps]

    fig = go.Figure(go.Waterfall(
        x=names, y=values, measure=measures, text=texts, textposition="outside",
        connector=dict(line=dict(color=C["text_faint"], width=1, dash="dot")),
        increasing=dict(marker=dict(color=C["khaki"])),
        decreasing=dict(marker=dict(color=C["khaki"])),
        totals=dict(marker=dict(color=C["olive"])),
    ))
    # recolor first/last bars distinctly (first = olive potential, last = dark green utilized)
    fig.data[0].totals.marker.color = C["olive"]
    fig.update_traces(textfont=dict(size=12, color=C["text"]))
    fig.update_layout(**BASE_LAYOUT, height=340, showlegend=False)
    fig.update_xaxes(tickfont=dict(size=10))
    fig.update_yaxes(title="kWh", gridcolor=C["border"])
    return fig


def energy_flow_chart(days, pv, bess, genset, max_energy, irradiation):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=pv, name="PV (kWh)", stackgroup="one", mode="none", fillcolor=C["cream_muted"]))
    fig.add_trace(go.Scatter(x=days, y=bess, name="BESS (kWh)", stackgroup="one", mode="none", fillcolor=C["brand_light"]))
    fig.add_trace(go.Scatter(x=days, y=genset, name="Genset (kWh)", stackgroup="one", mode="none", fillcolor=C["text"]))
    fig.add_trace(go.Scatter(x=days, y=max_energy, name="Max daily energy", mode="lines",
                              line=dict(color=C["warning"], dash="dash", width=1.6), yaxis="y1"))
    fig.add_trace(go.Scatter(x=days, y=irradiation, name="Irradiation (W/m2)", mode="lines",
                              line=dict(color=C["info"], width=1.6), yaxis="y2"))
    fig.update_layout(
        **BASE_LAYOUT, height=290,
        yaxis=dict(title="kWh", gridcolor=C["border"]),
        yaxis2=dict(title="W/m2", overlaying="y", side="right", showgrid=False),
    )
    return fig


def genset_share_bar(genset_pct, pv_bess_pct):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[genset_pct], y=["Energy mix"], orientation="h", name="Genset",
                          marker_color=C["text"], text=[f"{genset_pct:.2f}%"], textposition="inside"))
    fig.add_trace(go.Bar(x=[pv_bess_pct], y=["Energy mix"], orientation="h", name="PV + BESS",
                          marker_color=C["brand"], text=[f"{pv_bess_pct:.2f}%"], textposition="inside"))
    layout = dict(BASE_LAYOUT)
    layout["margin"] = dict(l=8, r=8, t=8, b=8)
    fig.update_layout(**layout, barmode="stack", height=90, showlegend=True)
    fig.update_xaxes(visible=False, range=[0, 100])
    fig.update_yaxes(visible=False)
    return fig


def soc_trend_chart(days, min_soc, max_soc):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=max_soc, name="Max SoC", mode="lines", line=dict(color=C["text_faint"], width=1.6)))
    fig.add_trace(go.Scatter(x=days, y=min_soc, name="Min SoC", mode="lines", line=dict(color=C["text"], width=1.6)))
    fig.add_hline(y=15, line=dict(color=C["warning"], dash="dash", width=1))
    fig.add_hline(y=95, line=dict(color=C["success"], dash="dash", width=1))
    fig.update_layout(**BASE_LAYOUT, height=200)
    fig.update_yaxes(range=[0, 100], gridcolor=C["border"])
    return fig


def soh_monthly_chart(months, soh_values):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=soh_values, marker_color=C["brand_light"]))
    fig.add_hline(y=95, line=dict(color=C["warning"], dash="dash", width=1))
    fig.update_layout(**BASE_LAYOUT, height=170, showlegend=False)
    fig.update_yaxes(range=[90, 100], gridcolor=C["border"])
    return fig


def diesel_runtime_fuel_chart(days, runtime, fuel):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=days, y=runtime, name="Runtime (hrs)", marker_color=C["text"], yaxis="y1"))
    fig.add_trace(go.Scatter(x=days, y=fuel, name="Fuel (L)", mode="lines", line=dict(color=C["warning"], width=1.8), yaxis="y2"))
    fig.update_layout(**BASE_LAYOUT, height=190,
                       yaxis=dict(title="hrs", gridcolor=C["border"]),
                       yaxis2=dict(title="L", overlaying="y", side="right", showgrid=False))
    return fig


def specific_fuel_chart(days, sfc):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=days, y=sfc, marker_color=C["text"]))
    fig.add_hline(y=15, line=dict(color=C["warning"], dash="dash", width=1))
    fig.update_layout(**BASE_LAYOUT, height=170, showlegend=False)
    fig.update_yaxes(range=[0, 20], gridcolor=C["border"])
    return fig


def availability_trend_chart(days, availability):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=availability, mode="lines", line=dict(color=C["success"], width=2)))
    fig.update_layout(**BASE_LAYOUT, height=190, showlegend=False)
    fig.update_yaxes(range=[75, 100], gridcolor=C["border"])
    return fig


def solar_split_donut(aeb, client):
    fig = go.Figure(go.Pie(
        labels=["Solar Akartha (AEB)", "Solar Client"], values=[max(aeb, 0.0001), max(client, 0.0001)],
        hole=0.55, marker=dict(colors=[C["brand"], C["khaki"]]), textinfo="none",
    ))
    layout = dict(BASE_LAYOUT)
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    fig.update_layout(**layout, height=230, showlegend=True)
    return fig


def energy_mix_bar(labels, renewable, genset):
    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=renewable, name="PV + BESS (kWh)", orientation="h", marker_color=C["khaki"]))
    fig.add_trace(go.Bar(y=labels, x=genset, name="Genset (kWh)", orientation="h", marker_color=C["brand_dark"]))
    fig.update_layout(**BASE_LAYOUT, barmode="stack", height=max(220, 28 * len(labels)))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Energy delivered (kWh)", gridcolor=C["border"])
    return fig
