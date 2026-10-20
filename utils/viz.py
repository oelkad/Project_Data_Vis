"""Chart functions with one consistent visual style.

Design rules (see README › Accessibility):
* one primary hue (blue) for single series, orange only for a contrasting
  series or an emphasised mark, grey for context - pair validated for
  colour-blind separation;
* sequential maps/heatmaps use a single-hue blue ramp (light = low);
* never two y-axes; small multiples instead of busy legends;
* every axis labelled with its unit; hover tooltips on every mark;
* every chart is shown with an ``alt`` text and, optionally, a visible
  text description + a table view.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import constants as K
from utils.metrics import METRIC_UNITS, fmt_int

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}
SEQ_SCALE = [[i / (len(K.SEQ_BLUE) - 1), c] for i, c in enumerate(K.SEQ_BLUE)]
# Basemap of the point map (CARTO tiles, loaded by the browser). Set MAP_STYLE=white-bg to run offline.
MAP_STYLE = os.environ.get("MAP_STYLE", "carto-positron")


def style(fig: go.Figure, height: int = 380, legend: bool = True, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=12, r=16, t=48 if title else 16, b=8),
        title=dict(text=title, x=0, xanchor="left", font=dict(size=15, color=K.INK)) if title else None,
        font=dict(family=FONT, size=13, color=K.INK_2),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="white", bordercolor=K.GRID, font=dict(family=FONT, size=13, color=K.INK)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
    )
    fig.update_xaxes(showgrid=False, linecolor=K.GRID, ticks="outside", tickcolor=K.GRID, automargin=True,
                     title_font=dict(size=12, color=K.MUTED), zeroline=False, tickfont=dict(color=K.INK_2))
    fig.update_yaxes(gridcolor=K.GRID, gridwidth=1, linecolor=K.GRID, zeroline=False, automargin=True,
                     title_font=dict(size=12, color=K.MUTED), tickfont=dict(color=K.INK_2), title_standoff=8,
                     tickformat=",")
    return fig


def show(fig: go.Figure, alt: str, key: str | None = None, table: pd.DataFrame | None = None,
         on_select: str = "ignore", **kwargs):
    """Render a figure with alt text, optional visible description and table view."""
    event = st.plotly_chart(fig, theme=None, config=PLOT_CONFIG, alt=alt, key=key,
                            on_select=on_select, **kwargs)
    if st.session_state.get("describe_charts", True):
        st.caption(f"Chart description: {alt}")
    if table is not None:
        with st.expander("Table view of this chart"):
            st.dataframe(table, hide_index=True, alt=f"Data table for: {alt[:120]}")
    return event


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
def target_path(actual: pd.DataFrame) -> go.Figure:
    """Metropolitan deaths vs the straight path to the EU 2030 goal (-50 % vs 2019)."""
    base, target_year = K.METRO_KILLED_2019, K.EU_TARGET_YEAR
    target = base * K.EU_TARGET_FACTOR
    years = np.arange(2019, target_year + 1)
    path = base + (target - base) * (years - 2019) / (target_year - 2019)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=path, mode="lines", name="Path to the EU 2030 goal (−50% vs 2019)",
                             line=dict(color=K.INK_2, width=2, dash="dash"),
                             hovertemplate="%{x}: %{y:,.0f} deaths on the target path<extra></extra>"))
    fig.add_trace(go.Scatter(x=[2019], y=[base], mode="markers", name="2019 baseline (ONISR)",
                             marker=dict(size=10, color="white", line=dict(color=K.INK_2, width=2)),
                             hovertemplate="2019 baseline: %{y:,.0f} deaths (official)<extra></extra>"))
    fig.add_trace(go.Scatter(x=actual["year"], y=actual["killed"], mode="lines+markers",
                             name="Recorded deaths (this dataset)", line=dict(color=K.BLUE, width=3),
                             marker=dict(size=9, color=K.BLUE, line=dict(color="white", width=2)),
                             hovertemplate="%{x}: %{y:,.0f} people killed<extra></extra>"))
    last = actual.iloc[-1]
    path_last = float(np.interp(last["year"], years, path))
    fig.add_shape(type="line", x0=last["year"], x1=last["year"], y0=path_last, y1=last["killed"],
                  line=dict(color=K.ORANGE, width=3))
    fig.add_annotation(x=last["year"], y=(path_last + last["killed"]) / 2, xanchor="left", xshift=8,
                       text=f"<b>{last['killed'] - path_last:+,.0f}</b> deaths<br>above the path in {int(last['year'])}",
                       showarrow=False, font=dict(color=K.INK, size=13), align="left")
    fig.add_annotation(x=target_year, y=target, text=f"Goal: {target:,.0f}", showarrow=False, yshift=14,
                       font=dict(color=K.INK_2, size=12))
    fig.add_vrect(x0=2019.6, x1=2020.4, fillcolor=K.GREY, opacity=0.25, line_width=0,
                  annotation_text="COVID", annotation_position="top left",
                  annotation_font=dict(size=11, color=K.MUTED))
    fig.update_yaxes(title="People killed per year (metropolitan France)", rangemode="tozero")
    fig.update_xaxes(title=None, dtick=1)
    return style(fig, height=400)


def monthly_trend(m: pd.DataFrame) -> go.Figure:
    """Two aligned panels (no dual axis): accidents and deaths per month."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Injury accidents per month", "People killed per month"))
    fig.add_trace(go.Scatter(x=m["ym"], y=m["accidents"], mode="lines", line=dict(color=K.BLUE, width=2),
                             name="Injury accidents", hovertemplate="%{x|%b %Y}: %{y:,} accidents<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=m["ym"], y=m["killed"], mode="lines", line=dict(color=K.ORANGE, width=2),
                             name="People killed", hovertemplate="%{x|%b %Y}: %{y:,} killed<extra></extra>"),
                  row=2, col=1)
    lo, hi = m["ym"].min(), m["ym"].max()
    for start, end, label in K.LOCKDOWNS:
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        if e < lo or s > hi:
            continue
        for r in (1, 2):
            fig.add_vrect(x0=s, x1=e, fillcolor=K.GREY, opacity=0.3, line_width=0, row=r, col=1)
    fig.add_annotation(x=1, xref="paper", y=1.0, yref="paper", xanchor="right", yanchor="bottom",
                       text="<span style='color:#a8a69c'>■</span> grey bands = COVID lockdowns", showarrow=False,
                       font=dict(size=11, color=K.MUTED))
    for ann in fig.layout.annotations[:2]:
        ann.update(x=0, xanchor="left", font=dict(size=13, color=K.INK))
    fig.update_yaxes(rangemode="tozero")
    fig.update_yaxes(title="accidents", row=1, col=1)
    fig.update_yaxes(title="people killed", row=2, col=1)
    return style(fig, height=470, legend=False)


def area_year_bars(df: pd.DataFrame, value: str = "killed") -> go.Figure:
    fig = go.Figure()
    for area in ["Urban", "Rural"]:
        d = df[df["area"] == area]
        fig.add_trace(go.Bar(x=d["year"], y=d[value], name=f"{area} roads", marker_color=K.AREA_COLORS[area],
                             customdata=d[["share"]],
                             hovertemplate=f"{area} · %{{x}}: %{{y:,}} {METRIC_UNITS.get(value, value)}"
                                           " (%{customdata[0]:.0f}% of the year)<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_xaxes(title=None, dtick=1)
    fig.update_yaxes(title=METRIC_UNITS.get(value, value))
    return style(fig, height=340)


# ---------------------------------------------------------------------------
# Where
# ---------------------------------------------------------------------------
METRIC_TITLES = {"killed": "People killed", "lethality": "Killed per 100 accidents",
                 "accidents": "Injury accidents", "ksi": "Killed or hospitalised"}


def choropleth(dep: pd.DataFrame, geo: dict, metric: str) -> go.Figure:
    """Department map. MapLibre 'white-bg' style: no external tiles needed."""
    fig = go.Figure(go.Choroplethmap(
        geojson=geo, locations=dep["dep"], featureidkey="properties.code", z=dep[metric],
        colorscale=SEQ_SCALE, marker=dict(line=dict(color="white", width=0.8), opacity=0.95),
        customdata=dep[["dep_name", "accidents", "killed", "lethality"]],
        hovertemplate="<b>%{customdata[0]}</b> (%{location})<br>%{customdata[1]:,} injury accidents"
                      "<br>%{customdata[2]:,} people killed<br>%{customdata[3]:.1f} killed per 100 accidents"
                      "<extra></extra>",
        colorbar=dict(title=dict(text=METRIC_TITLES[metric], side="right"), thickness=12, len=0.75,
                      outlinewidth=0, tickformat=",")))
    fig.update_layout(map=dict(style="white-bg", center=dict(lat=46.45, lon=2.7), zoom=4.05))
    fig = style(fig, height=540, legend=False)
    fig.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    return fig


def dep_scatter(dep: pd.DataFrame, national: float, label_codes: list[str]) -> go.Figure:
    d = dep.copy()
    d["rural_pct"] = 100 * d["rural_share"]
    fig = go.Figure(go.Scatter(
        x=d["accidents"], y=d["lethality"], mode="markers",
        marker=dict(size=np.sqrt(d["killed"].clip(lower=1)) * 2.2, sizemode="diameter", color=d["rural_pct"],
                    colorscale=SEQ_SCALE, cmin=0, cmax=100, line=dict(color="white", width=1.5), opacity=0.9,
                    colorbar=dict(title=dict(text="% of accidents<br>on rural roads", side="right"),
                                  thickness=12, len=0.8, outlinewidth=0)),
        customdata=d[["dep_name", "killed", "rural_pct", "dep"]],
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[3]})<br>%{x:,} injury accidents<br>"
                      "%{y:.1f} killed per 100 accidents<br>%{customdata[1]:,} killed · "
                      "%{customdata[2]:.0f}% rural<extra></extra>"))
    fig.add_hline(y=national, line=dict(color=K.MUTED, width=1.5, dash="dot"),
                  annotation_text=f"Average {national:.1f}", annotation_position="top right",
                  annotation_font=dict(color=K.INK_2, size=11))
    for _, r in d[d["dep"].isin(label_codes)].iterrows():
        fig.add_annotation(x=np.log10(r["accidents"]), y=r["lethality"], text=r["dep_name"], showarrow=False,
                           yshift=14, font=dict(size=11, color=K.INK))
    fig.update_xaxes(type="log", title="Injury accidents over the period (log scale)", showgrid=True,
                     gridcolor=K.GRID)
    fig.update_yaxes(title="People killed per 100 injury accidents", rangemode="tozero")
    return style(fig, height=470, legend=False)


def ranking_bar(dep: pd.DataFrame, metric: str, national: float | None, top: bool) -> go.Figure:
    d = dep.sort_values(metric, ascending=not top)
    d = d.iloc[::-1]
    fmt = ".1f" if metric == "lethality" else ",.0f"
    fig = go.Figure(go.Bar(
        y=d["dep_name"] + " (" + d["dep"].astype(str) + ")", x=d[metric], orientation="h",
        marker_color=K.BLUE if top else K.GREY, marker_line_width=0,
        text=d[metric].map(lambda v: f"{v:{fmt}}"), textposition="outside", cliponaxis=False,
        textfont=dict(color=K.INK_2, size=12),
        customdata=d[["accidents", "killed", "lethality"]],
        hovertemplate="<b>%{y}</b><br>%{customdata[0]:,} accidents · %{customdata[1]:,} killed · "
                      "%{customdata[2]:.1f} per 100<extra></extra>"))
    if national is not None:
        fig.add_vline(x=national, line=dict(color=K.ORANGE, width=2, dash="dot"),
                      annotation_text=f"Average {national:{fmt}}", annotation_position="top",
                      annotation_font=dict(color=K.INK_2, size=11))
    fig.update_xaxes(title=METRIC_TITLES[metric], showgrid=True, gridcolor=K.GRID)
    fig.update_yaxes(title=None, showgrid=False)
    return style(fig, height=max(260, 34 * len(d) + 70), legend=False)


def share_bars(df: pd.DataFrame, label_col: str, title_dim: str) -> go.Figure:
    """Share of accidents vs share of deaths for each category of a dimension."""
    d = df.sort_values("share_killed")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d[label_col], x=d["share_acc"], orientation="h", name="% of injury accidents",
                         marker_color=K.BLUE, customdata=d[["accidents", "lethality"]],
                         hovertemplate="<b>%{y}</b><br>%{x:.1f}% of accidents (%{customdata[0]:,})"
                                       "<br>%{customdata[1]:.1f} killed per 100 accidents<extra></extra>"))
    fig.add_trace(go.Bar(y=d[label_col], x=d["share_killed"], orientation="h", name="% of people killed",
                         marker_color=K.ORANGE, customdata=d[["killed", "lethality"]],
                         hovertemplate="<b>%{y}</b><br>%{x:.1f}% of deaths (%{customdata[0]:,})"
                                       "<br>%{customdata[1]:.1f} killed per 100 accidents<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.06)
    fig.update_xaxes(title=f"Share of the total, by {title_dim} (%)", showgrid=True, gridcolor=K.GRID,
                     ticksuffix="%")
    fig.update_yaxes(title=None)
    return style(fig, height=max(300, 52 * len(d) + 80))


def points_map(pts: pd.DataFrame, center: tuple[float, float], zoom: float) -> go.Figure:
    fig = go.Figure()
    other = pts[~pts["fatal"]]
    fatal = pts[pts["fatal"]]
    fig.add_trace(go.Scattermap(lat=other["lat"], lon=other["lon"], mode="markers", name="Non-fatal accident",
                                marker=dict(size=5, color=K.BLUE, opacity=0.45),
                                customdata=other[["date_str", "area", "n_hosp"]],
                                hovertemplate="%{customdata[0]} · %{customdata[1]}<br>%{customdata[2]} hospitalised"
                                              "<extra>Non-fatal</extra>"))
    fig.add_trace(go.Scattermap(lat=fatal["lat"], lon=fatal["lon"], mode="markers", name="Fatal accident",
                                marker=dict(size=8, color=K.ORANGE, opacity=0.9),
                                customdata=fatal[["date_str", "area", "n_killed", "road"]],
                                hovertemplate="<b>%{customdata[2]} killed</b><br>%{customdata[0]} · "
                                              "%{customdata[1]} · %{customdata[3]}<extra>Fatal</extra>"))
    fig.update_layout(map=dict(style=MAP_STYLE, center=dict(lat=center[0], lon=center[1]), zoom=zoom))
    fig = style(fig, height=520)
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    return fig


# ---------------------------------------------------------------------------
# Who
# ---------------------------------------------------------------------------
def hbar(d: pd.DataFrame, y: str, x: str, x_title: str, fmt: str = ",.0f", highlight: list[str] | None = None,
         hover_extra: str = "") -> go.Figure:
    d = d.sort_values(x)
    colors = [K.ORANGE if (highlight and v in highlight) else K.BLUE for v in d[y]]
    fig = go.Figure(go.Bar(y=d[y], x=d[x], orientation="h", marker_color=colors,
                           text=d[x].map(lambda v: f"{v:{fmt}}"), textposition="outside", cliponaxis=False,
                           textfont=dict(color=K.INK_2, size=12),
                           hovertemplate="<b>%{y}</b><br>%{x:" + fmt + "} " + x_title + hover_extra + "<extra></extra>"))
    fig.update_xaxes(title=x_title, showgrid=True, gridcolor=K.GRID)
    fig.update_yaxes(title=None)
    return style(fig, height=max(280, 40 * len(d) + 60), legend=False)


def age_pyramid(d: pd.DataFrame) -> go.Figure:
    """d: age_band, sexe (1/2), killed."""
    piv = d.pivot_table(index="age_band", columns="sexe", values="killed", aggfunc="sum", observed=False).fillna(0)
    piv = piv.reindex(K.AGE_LABELS).fillna(0)
    men = piv.get(1, pd.Series(0, index=piv.index))
    women = piv.get(2, pd.Series(0, index=piv.index))
    fig = go.Figure()
    fig.add_trace(go.Bar(y=piv.index, x=-men, orientation="h", name="Men", marker_color=K.BLUE,
                         customdata=men, hovertemplate="Men %{y}: %{customdata:,} killed<extra></extra>"))
    fig.add_trace(go.Bar(y=piv.index, x=women, orientation="h", name="Women", marker_color=K.ORANGE,
                         customdata=women, hovertemplate="Women %{y}: %{customdata:,} killed<extra></extra>"))
    mx = max(men.max(), women.max(), 1)
    raw = mx / 3
    mag = 10 ** np.floor(np.log10(raw)) if raw >= 1 else 1
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    ticks = np.arange(0, mx + step, step)
    fig.update_layout(barmode="overlay", bargap=0.15)
    fig.update_xaxes(title="People killed (men ← → women)", tickvals=np.concatenate([-ticks[::-1], ticks[1:]]),
                     ticktext=[f"{abs(v):,.0f}" for v in np.concatenate([-ticks[::-1], ticks[1:]])],
                     showgrid=True, gridcolor=K.GRID, zeroline=True, zerolinecolor=K.MUTED)
    fig.update_yaxes(title="Age band")
    return style(fig, height=380)


def mode_small_multiples(d: pd.DataFrame, value: str = "killed") -> go.Figure:
    """One mini line chart per road-user type, each with its own y scale."""
    modes = [m for m in K.MODE_ORDER if m in set(d["mode"])]
    fig = px.line(d, x="year", y=value, facet_col="mode", facet_col_wrap=4, markers=True,
                  category_orders={"mode": modes}, facet_row_spacing=0.18, facet_col_spacing=0.06)
    fig.update_traces(line=dict(color=K.BLUE, width=2), marker=dict(size=7, color=K.BLUE),
                      hovertemplate="%{x}: %{y:,} " + METRIC_UNITS.get(value, value) + "<extra></extra>")
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>",
                                               font=dict(size=12, color=K.INK)))
    fig.update_yaxes(matches=None, rangemode="tozero", title=None, showticklabels=True, nticks=4)
    fig.update_xaxes(title=None, dtick=1, tickformat="d", tickangle=0, tickfont=dict(size=10))
    return style(fig, height=430, legend=False)


def heatmap(pv: pd.DataFrame, value_title: str, fmt: str) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=pv.values, x=[f"{h:02d}h" for h in pv.columns], y=pv.index,
                               colorscale=SEQ_SCALE, xgap=2, ygap=2,
                               colorbar=dict(title=dict(text=value_title, side="right"), thickness=12,
                                             outlinewidth=0),
                               hovertemplate="%{y} %{x}: %{z:" + fmt + "} " + value_title + "<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title=None, showgrid=False)
    fig.update_xaxes(title="Hour of the accident", showgrid=False)
    return style(fig, height=330, legend=False)


def seasonality(d: pd.DataFrame) -> go.Figure:
    """Deaths by month for a few modes, small multiples with shared month axis."""
    modes = [m for m in ["Car", "Motorcycle >50cc", "Pedestrian", "Bicycle"] if m in set(d["mode"])]
    d = d[d["mode"].isin(modes)]
    fig = px.bar(d, x="month_name", y="killed", facet_col="mode", facet_col_wrap=4,
                 category_orders={"mode": modes, "month_name": K.MONTHS}, facet_col_spacing=0.06)
    fig.update_traces(marker_color=K.BLUE, hovertemplate="%{x}: %{y:,} killed<extra></extra>")
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>",
                                               font=dict(size=12, color=K.INK)))
    fig.update_yaxes(matches=None, title=None, showticklabels=True, nticks=4)
    fig.update_xaxes(title=None, tickangle=0, tickvals=["Jan", "Apr", "Jul", "Oct"], tickfont=dict(size=10))
    fig.update_layout(bargap=0.15)
    return style(fig, height=320, legend=False)


# ---------------------------------------------------------------------------
# What-if
# ---------------------------------------------------------------------------
def waterfall(base_label: str, base: float, items: list[tuple[str, float]], target: float) -> go.Figure:
    labels = [base_label] + [name for name, _ in items] + ["Scenario"]
    values = [base] + [-v for _, v in items] + [0]
    measures = ["absolute"] + ["relative"] * len(items) + ["total"]
    fig = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures, connector=dict(line=dict(color=K.GRID, width=1)),
        increasing=dict(marker=dict(color=K.ORANGE)), decreasing=dict(marker=dict(color=K.ORANGE)),
        totals=dict(marker=dict(color=K.BLUE)),
        text=[fmt_int(base)] + [f"−{v:,.0f}" for _, v in items] + [fmt_int(base - sum(v for _, v in items))],
        textposition="outside", cliponaxis=False, textfont=dict(color=K.INK_2),
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    fig.add_hline(y=target, line=dict(color=K.INK, dash="dash", width=2))
    fig.add_annotation(x=0.5, xref="paper", xanchor="center", y=target, yanchor="bottom", yshift=4,
                       text=f"EU 2030 goal ≈ {target:,.0f}", showarrow=False, bgcolor="rgba(252,252,251,0.9)",
                       font=dict(color=K.INK, size=12))
    fig.update_yaxes(title="People killed per year (metropolitan France)", rangemode="tozero")
    fig.update_xaxes(title=None, tickangle=0)
    return style(fig, height=430, legend=False)


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------
def missing_heatmap(pv: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=pv.values, x=[str(c) for c in pv.columns], y=pv.index, colorscale=SEQ_SCALE, zmin=0, zmax=100,
        xgap=2, ygap=2, text=np.where(np.nan_to_num(pv.values) >= 0.5,
                                   np.round(np.nan_to_num(pv.values)).astype(int).astype(str) + "%", ""),
        texttemplate="%{text}", textfont=dict(size=11),
        colorbar=dict(title=dict(text="% missing", side="right"), thickness=12, outlinewidth=0),
        hovertemplate="%{y} · %{x}: %{z:.2f}% not filled<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(title=None, side="top")
    return style(fig, height=max(260, 24 * len(pv) + 60), legend=False)


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------
# Diverging scale: red (negative) <- neutral grey (0) -> blue (positive)
DIVERGING = [[0.0, "#9c2222"], [0.17, "#e34948"], [0.33, "#f5b5b4"], [0.5, "#f0efec"],
             [0.67, "#9ec5f4"], [0.83, "#3987e5"], [1.0, "#104281"]]


def corr_heatmap(corr: pd.DataFrame) -> go.Figure:
    """Lower-triangle correlation matrix with the value written in each cell."""
    n = len(corr)
    z = corr.to_numpy(dtype=float).copy()
    z[np.triu_indices(n)] = np.nan          # hide the diagonal and the mirrored upper half
    z, rows, cols = z[1:, :-1], list(corr.index[1:]), list(corr.columns[:-1])
    fig = go.Figure(go.Heatmap(
        z=z, x=cols, y=rows, zmin=-1, zmax=1, colorscale=DIVERGING, xgap=2, ygap=2, hoverongaps=False,
        colorbar=dict(title=dict(text="correlation r", side="right"), thickness=12, outlinewidth=0,
                      tickvals=[-1, -0.5, 0, 0.5, 1]),
        hovertemplate="%{y} × %{x}<br>r = %{z:+.2f}<extra></extra>"))
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            v = z[i, j]
            if np.isnan(v):
                continue
            fig.add_annotation(x=c, y=r, text=f"{v:+.2f}".replace("+0.", ".").replace("-0.", "−."),
                               showarrow=False, font=dict(size=11, color="white" if abs(v) >= 0.55 else K.INK))
    fig.update_yaxes(autorange="reversed", showgrid=False, title=None)
    fig.update_xaxes(showgrid=False, title=None, tickangle=-40)
    return style(fig, height=max(380, 44 * n + 120), legend=False)
