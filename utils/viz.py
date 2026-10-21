"""All the charts (Plotly), with one shared style.

Colour rules: blue = main series, orange = contrast/emphasis, grey = context; one-hue blue ramp for
maps and heatmaps; blue/red for the correlation matrix. No chart uses two y-axes.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import constants as K

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
SEQ_SCALE = [[i / (len(K.SEQ_BLUE) - 1), c] for i, c in enumerate(K.SEQ_BLUE)]
DIVERGING = [[0.0, "#9c2222"], [0.17, "#e34948"], [0.33, "#f5b5b4"], [0.5, "#f0efec"],
             [0.67, "#9ec5f4"], [0.83, "#3987e5"], [1.0, "#104281"]]
TITLES = {"killed": "People killed", "lethality": "Killed per 100 accidents", "accidents": "Injury accidents"}


def style(fig: go.Figure, height: int = 380, legend: bool = True) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=12, r=16, t=16, b=8), font=dict(family=FONT, size=13, color=K.INK_2),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=legend,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
                      hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=K.INK)))
    fig.update_xaxes(showgrid=False, linecolor=K.GRID, automargin=True, title_font=dict(size=12, color=K.MUTED))
    fig.update_yaxes(gridcolor=K.GRID, linecolor=K.GRID, automargin=True, tickformat=",",
                     title_font=dict(size=12, color=K.MUTED))
    return fig


def show(fig: go.Figure, **kwargs):
    return st.plotly_chart(fig, theme=None, config={"displaylogo": False}, **kwargs)


# --------------------------------------------------------------------------- Intro / overview
def target_path(actual: pd.DataFrame) -> go.Figure:
    """Recorded deaths vs the straight path to the EU 2030 goal (-50 % vs 2019)."""
    base, goal = K.METRO_KILLED_2019, K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    years = np.arange(2019, K.EU_TARGET_YEAR + 1)
    path = base + (goal - base) * (years - 2019) / (K.EU_TARGET_YEAR - 2019)
    fig = go.Figure()
    fig.add_scatter(x=years, y=path, mode="lines", name="Path to the EU 2030 goal (−50% vs 2019)",
                    line=dict(color=K.INK_2, width=2, dash="dash"))
    fig.add_scatter(x=[2019], y=[base], mode="markers", name="2019 baseline (ONISR)",
                    marker=dict(size=10, color="white", line=dict(color=K.INK_2, width=2)))
    fig.add_scatter(x=actual["year"], y=actual["killed"], mode="lines+markers", name="Recorded deaths",
                    line=dict(color=K.BLUE, width=3), marker=dict(size=9))
    last = actual.iloc[-1]
    on_path = float(np.interp(last["year"], years, path))
    fig.add_shape(type="line", x0=last["year"], x1=last["year"], y0=on_path, y1=last["killed"],
                  line=dict(color=K.ORANGE, width=3))
    fig.add_annotation(x=last["year"], y=(on_path + last["killed"]) / 2, xanchor="left", xshift=8, showarrow=False,
                       text=f"<b>{last['killed'] - on_path:+,.0f}</b> deaths<br>above the path in {int(last['year'])}")
    fig.add_annotation(x=K.EU_TARGET_YEAR, y=goal, text=f"Goal: {goal:,.0f}", showarrow=False, yshift=14)
    fig.add_vrect(x0=2019.6, x1=2020.4, fillcolor=K.GREY, opacity=0.25, line_width=0,
                  annotation_text="COVID", annotation_position="top left")
    fig.update_yaxes(title="People killed per year (metropolitan France)", rangemode="tozero")
    fig.update_xaxes(dtick=1)
    return style(fig, height=400)


def monthly_trend(m: pd.DataFrame) -> go.Figure:
    """Accidents and deaths per month in two aligned panels (no dual axis), lockdowns shaded."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("Injury accidents per month", "People killed per month"))
    fig.add_scatter(x=m["ym"], y=m["accidents"], line=dict(color=K.BLUE, width=2), row=1, col=1)
    fig.add_scatter(x=m["ym"], y=m["killed"], line=dict(color=K.ORANGE, width=2), row=2, col=1)
    for start, end in K.LOCKDOWNS:
        if pd.Timestamp(end) >= m["ym"].min() and pd.Timestamp(start) <= m["ym"].max():
            for row in (1, 2):
                fig.add_vrect(x0=start, x1=end, fillcolor=K.GREY, opacity=0.3, line_width=0, row=row, col=1)
    fig.add_annotation(x=1, y=1.0, xref="paper", yref="paper", xanchor="right", yanchor="bottom", showarrow=False,
                       text="grey bands = COVID lockdowns", font=dict(size=11, color=K.MUTED))
    fig.update_yaxes(rangemode="tozero")
    fig.for_each_annotation(lambda a: a.update(x=0, xanchor="left") if a.text.endswith("per month") else None)
    fig = style(fig, height=470, legend=False)
    fig.update_layout(margin=dict(t=30))
    return fig


def area_year_bars(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for area, color in [("Urban", K.BLUE), ("Rural", K.ORANGE)]:
        d = df[df["area"] == area]
        fig.add_bar(x=d["year"], y=d["killed"], name=f"{area} roads", marker_color=color)
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(title="people killed")
    return style(fig, height=340)


# --------------------------------------------------------------------------- Where
def choropleth(dep: pd.DataFrame, geo: dict, metric: str) -> go.Figure:
    """Department map; the 'white-bg' style needs no external map tiles."""
    fig = go.Figure(go.Choroplethmap(
        geojson=geo, locations=dep["dep"], featureidkey="properties.code", z=dep[metric], colorscale=SEQ_SCALE,
        marker=dict(line=dict(color="white", width=0.8)), customdata=dep[["dep_name", "accidents", "killed", "lethality"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,} accidents · %{customdata[2]:,} killed"
                      "<br>%{customdata[3]:.1f} killed per 100 accidents<extra></extra>",
        colorbar=dict(title=dict(text=TITLES[metric], side="right"), thickness=12, len=0.75)))
    fig.update_layout(map=dict(style="white-bg", center=dict(lat=46.45, lon=2.7), zoom=4.05))
    fig = style(fig, height=540, legend=False)
    fig.update_layout(margin=dict(l=0, r=0, t=8, b=0))
    return fig


def dep_scatter(dep: pd.DataFrame, average: float) -> go.Figure:
    """One bubble per department: accidents (x, log) vs lethality (y), size = deaths, colour = % rural."""
    fig = go.Figure(go.Scatter(
        x=dep["accidents"], y=dep["lethality"], mode="markers", customdata=dep[["dep_name", "killed"]],
        marker=dict(size=np.sqrt(dep["killed"].clip(lower=1)) * 2.2, color=100 * dep["rural_share"],
                    colorscale=SEQ_SCALE, cmin=0, cmax=100, line=dict(color="white", width=1.5),
                    colorbar=dict(title=dict(text="% rural accidents", side="right"), thickness=12)),
        hovertemplate="<b>%{customdata[0]}</b><br>%{x:,} accidents · %{customdata[1]:,} killed"
                      "<br>%{y:.1f} killed per 100 accidents<extra></extra>"))
    fig.add_hline(y=average, line=dict(color=K.MUTED, dash="dot"), annotation_text=f"Average {average:.1f}")
    for _, r in dep.loc[[dep["lethality"].idxmax(), dep["accidents"].idxmax()]].iterrows():
        fig.add_annotation(x=np.log10(r["accidents"]), y=r["lethality"], text=r["dep_name"], showarrow=False, yshift=14)
    fig.update_xaxes(type="log", title="Injury accidents (log scale)", showgrid=True, gridcolor=K.GRID)
    fig.update_yaxes(title="Killed per 100 accidents", rangemode="tozero")
    return style(fig, height=470, legend=False)


def ranking_bar(dep: pd.DataFrame, metric: str, average: float) -> go.Figure:
    d = dep.iloc[::-1]
    fmt = ".1f" if metric == "lethality" else ",.0f"
    fig = go.Figure(go.Bar(y=d["dep_name"].astype(str), x=d[metric], orientation="h", marker_color=K.BLUE,
                           text=d[metric].map(lambda v: f"{v:{fmt}}"), textposition="outside", cliponaxis=False))
    fig.add_vline(x=average, line=dict(color=K.ORANGE, width=2, dash="dot"),
                  annotation_text=f"Average {average:{fmt}}", annotation_position="top")
    fig.update_xaxes(title=TITLES[metric], showgrid=True, gridcolor=K.GRID, range=[0, 1.12 * d[metric].max()])
    return style(fig, height=34 * len(d) + 80, legend=False)


def share_bars(d: pd.DataFrame, dimension: str) -> go.Figure:
    """For each category: its share of accidents vs its share of deaths."""
    d = d.sort_values("share_killed")
    fig = go.Figure()
    fig.add_bar(y=d["label"], x=d["share_acc"], orientation="h", name="% of injury accidents", marker_color=K.BLUE)
    fig.add_bar(y=d["label"], x=d["share_killed"], orientation="h", name="% of people killed", marker_color=K.ORANGE)
    fig.update_traces(hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
    fig.update_xaxes(title=f"Share of the total, by {dimension} (%)", ticksuffix="%", showgrid=True, gridcolor=K.GRID)
    return style(fig, height=52 * len(d) + 100)


def corr_heatmap(corr: pd.DataFrame) -> go.Figure:
    """Lower triangle of a correlation matrix, value written in each cell."""
    z = corr.to_numpy(dtype=float, copy=True)
    z[np.triu_indices(len(z))] = np.nan  # hide the diagonal and the mirrored half
    z, rows, cols = z[1:, :-1], list(corr.index[1:]), list(corr.columns[:-1])
    fig = go.Figure(go.Heatmap(z=z, x=cols, y=rows, zmin=-1, zmax=1, colorscale=DIVERGING, xgap=2, ygap=2,
                               hoverongaps=False, hovertemplate="%{y} × %{x}: r = %{z:+.2f}<extra></extra>",
                               colorbar=dict(title=dict(text="correlation r", side="right"), thickness=12)))
    for i, j in zip(*np.where(~np.isnan(z))):
        fig.add_annotation(x=cols[j], y=rows[i], text=f"{z[i, j]:.2f}", showarrow=False,
                           font=dict(size=11, color="white" if abs(z[i, j]) >= 0.55 else K.INK))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickangle=-40)
    return style(fig, height=44 * len(corr) + 120, legend=False)


def points_map(pts: pd.DataFrame) -> go.Figure:
    """Accidents of one department on a street map: fatal ones in orange."""
    fig = go.Figure()
    for fatal, name, color, size in [(False, "Non-fatal accident", K.BLUE, 5), (True, "Fatal accident", K.ORANGE, 8)]:
        d = pts[pts["fatal"] == fatal]
        fig.add_scattermap(lat=d["lat"], lon=d["lon"], mode="markers", name=name, text=d["label"],
                           marker=dict(size=size, color=color, opacity=0.9 if fatal else 0.45),
                           hovertemplate="%{text}<extra></extra>")
    fig.update_layout(map=dict(style="carto-positron", zoom=7.3,
                               center=dict(lat=pts["lat"].median(), lon=pts["lon"].median())))
    fig = style(fig, height=520)
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
    return fig


# --------------------------------------------------------------------------- Who
def hbar(d: pd.DataFrame, y: str, x: str, title: str, fmt: str = ",.0f", highlight=()) -> go.Figure:
    d = d.sort_values(x)
    fig = go.Figure(go.Bar(y=d[y], x=d[x], orientation="h", text=d[x].map(lambda v: f"{v:{fmt}}"),
                           textposition="outside", cliponaxis=False,
                           marker_color=[K.ORANGE if v in highlight else K.BLUE for v in d[y]]))
    fig.update_xaxes(title=title, showgrid=True, gridcolor=K.GRID, range=[0, 1.15 * d[x].max()])
    return style(fig, height=40 * len(d) + 60, legend=False)


def age_pyramid(killed: pd.DataFrame) -> go.Figure:
    counts = killed.groupby(["age_band", "sexe"], observed=False).size().unstack().reindex(K.AGE_LABELS).fillna(0)
    men, women = counts.get(1, 0 * counts.iloc[:, 0]), counts.get(2, 0 * counts.iloc[:, 0])
    fig = go.Figure()
    fig.add_bar(y=counts.index, x=-men, orientation="h", name="Men", marker_color=K.BLUE, customdata=men,
                hovertemplate="Men %{y}: %{customdata:,} killed<extra></extra>")
    fig.add_bar(y=counts.index, x=women, orientation="h", name="Women", marker_color=K.ORANGE, customdata=women,
                hovertemplate="Women %{y}: %{customdata:,} killed<extra></extra>")
    raw_step = max(men.max(), women.max(), 3) / 3
    mag = 10 ** np.floor(np.log10(raw_step))
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw_step)  # a "round" tick step
    ticks = np.arange(-3 * step, 3 * step + 1, step)
    fig.update_layout(barmode="overlay", bargap=0.15)
    fig.update_xaxes(title="People killed (men ← → women)", tickvals=ticks, ticktext=[f"{abs(t):,.0f}" for t in ticks])
    fig.update_yaxes(title="Age band")
    return style(fig, height=380)


def small_multiples(d: pd.DataFrame, x: str, y: str, kind: str = "line") -> go.Figure:
    """One small chart per road-user mode, each with its own y scale."""
    plot = px.line if kind == "line" else px.bar
    d = d.assign(mode=d["mode"].astype(str))  # only the modes present get a panel
    fig = plot(d, x=x, y=y, facet_col="mode", facet_col_wrap=4, facet_row_spacing=0.18, facet_col_spacing=0.06,
               category_orders={"mode": [m for m in K.MODE_ORDER if m in set(d["mode"])], "month_name": K.MONTHS})
    fig.update_traces(marker_color=K.BLUE, **({"line_color": K.BLUE, "mode": "lines+markers"} if kind == "line" else {}))
    fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>"))
    fig.update_yaxes(matches=None, showticklabels=True, title=None, rangemode="tozero")
    fig.update_xaxes(title=None, tickfont=dict(size=10), **({"dtick": 1} if kind == "line" else
                                                            {"tickvals": ["Jan", "Apr", "Jul", "Oct"]}))
    return style(fig, height=430 if d["mode"].nunique() > 4 else 300, legend=False)


# --------------------------------------------------------------------------- When
def heatmap(pv: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure(go.Heatmap(z=pv.values, x=[f"{h:02d}h" for h in pv.columns], y=pv.index, colorscale=SEQ_SCALE,
                               xgap=2, ygap=2, colorbar=dict(title=dict(text=title, side="right"), thickness=12),
                               hovertemplate="%{y} %{x}: %{z:,.1f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(title="Hour of the accident")
    return style(fig, height=330, legend=False)


# --------------------------------------------------------------------------- What-if
def waterfall(base_label: str, base: float, items: list[tuple[str, float]], goal: float) -> go.Figure:
    scenario = base - sum(v for _, v in items)
    fig = go.Figure(go.Waterfall(
        x=[base_label] + [name for name, _ in items] + ["Scenario"], y=[base] + [-v for _, v in items] + [0],
        measure=["absolute"] + ["relative"] * len(items) + ["total"], textposition="outside", cliponaxis=False,
        text=[f"{base:,.0f}"] + [f"−{v:,.0f}" for _, v in items] + [f"{scenario:,.0f}"],
        decreasing=dict(marker=dict(color=K.ORANGE)), totals=dict(marker=dict(color=K.BLUE)),
        connector=dict(line=dict(color=K.GRID))))
    fig.add_hline(y=goal, line=dict(color=K.INK, dash="dash", width=2))
    fig.add_annotation(x=0.5, xref="paper", y=goal, yanchor="bottom", yshift=4, showarrow=False,
                       text=f"EU 2030 goal ≈ {goal:,.0f}", bgcolor="rgba(252,252,251,0.9)")
    fig.update_yaxes(title="People killed per year (metropolitan France)", rangemode="tozero")
    return style(fig, height=430, legend=False)
