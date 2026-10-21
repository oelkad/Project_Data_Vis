"""3 · Where, who and when are accidents the deadliest (follows the filters)."""

import numpy as np
import pandas as pd
import streamlit as st

from sections.common import current_filters, headline, page_header
from utils import constants as K
from utils import viz
from utils.filters import Filters, filtered, summarize
from utils.io import load_geojson

MIN_ACC = 100  # departments with fewer accidents are left out of rates (too unstable)
BREAKDOWNS = {"Road type": ("catr", K.CATR), "Speed limit": ("vma", None),
              "Collision type": ("col", K.COL), "Intersection": ("int", K.INT)}
# indicators of the correlation matrix (one value per department)
CORR_LABELS = {"leth": "Lethality", "log_acc": "Accidents (log)", "rural": "% rural", "unlit": "% night, unlit",
               "night": "% night (all)", "vma80": "% on 80 km/h roads", "obst": "% fixed obstacle",
               "lone": "% single vehicle", "wkend": "% weekend", "moto": "% motorcycle", "ped": "% pedestrian"}
PEOPLE = {"Pedestrian": "pedestrians", "Motorcycle >50cc": "motorcyclists", "Bicycle": "cyclists",
          "Moped ≤50cc": "moped riders", "E-scooter (EDP)": "e-scooter riders", "Other": "other road users"}


@st.cache_data(show_spinner=False)
def geojson() -> dict:
    return load_geojson()


# --------------------------------------------------------------------------- Where
def department_table(acc: pd.DataFrame) -> pd.DataFrame:
    """Accidents, deaths, lethality and share of rural accidents per department."""
    d = summarize(acc, ["dep", "dep_name"])
    d["rural_share"] = d["dep"].map(acc.assign(r=acc["area"] == "Rural").groupby("dep", observed=True)["r"].mean())
    return d.astype({"dep": str, "dep_name": str, "rural_share": float})


def breakdown_table(acc: pd.DataFrame, col: str, labels: dict | None) -> pd.DataFrame:
    """Share of accidents vs share of deaths per category; categories under 0.5 % grouped as 'Other'."""
    d = summarize(acc.dropna(subset=[col]), col)
    d["label"] = d[col].map(labels) if labels else d[col].astype(int).astype(str) + " km/h"
    d.loc[100 * d["accidents"] / d["accidents"].sum() < 0.5, "label"] = "Other (small groups)"
    d = d.groupby("label", as_index=False)[["accidents", "killed"]].sum()
    d["share_acc"] = 100 * d["accidents"] / d["accidents"].sum()
    d["share_killed"] = 100 * d["killed"] / d["killed"].sum()
    return d


def correlation_matrix(acc: pd.DataFrame) -> pd.DataFrame | None:
    """Pearson correlation between department-level indicators (departments with MIN_ACC+ accidents)."""
    a = acc.assign(rural=acc["area"] == "Rural", unlit=acc["lum"].isin([3, 4]),
                   vma80=(acc["vma"] == 80).where(acc["vma"].notna()).astype(float), ped=acc["n_ped"] > 0)
    g = a.groupby("dep", observed=True)
    n = g.size()
    pct = lambda col: 100 * g[col].mean()  # noqa: E731
    d = pd.DataFrame({"leth": 100 * g["n_killed"].sum() / n, "log_acc": np.log10(n), "rural": pct("rural"),
                      "unlit": pct("unlit"), "night": pct("night"), "vma80": pct("vma80"),
                      "obst": pct("hit_fixed_obstacle"), "lone": pct("single_vehicle"), "wkend": pct("weekend"),
                      "moto": pct("has_moto"), "ped": pct("ped")})[n >= MIN_ACC].astype(float)
    d = d.loc[:, d.std() > 0]  # e.g. "% rural" is constant when only rural roads are selected
    if len(d) < 10 or "leth" not in d:
        return None
    corr = d.corr()
    order = ["leth"] + corr["leth"].drop("leth").sort_values(ascending=False).index.tolist()
    return corr.loc[order, order].rename(index=CORR_LABELS, columns=CORR_LABELS)


def render_where(f: Filters, acc: pd.DataFrame) -> None:
    by_area = summarize(acc, "area").set_index("area")
    if {"Rural", "Urban"} <= set(by_area.index):
        headline(f"Outside towns, <b>one injury accident in {100 / by_area.loc['Rural', 'lethality']:.0f} kills "
                 f"someone</b>; in towns it is one in {100 / by_area.loc['Urban', 'lethality']:.0f}. The deadliest "
                 "departments are rural ones, not the ones with the most accidents.")
    dep = department_table(acc)
    average = 100 * dep["killed"].sum() / dep["accidents"].sum()

    left, right = st.columns([1.05, 1])
    with left:
        st.markdown(f"**{f.metric_label} by department**")
        metro = dep[~dep["dep"].isin(K.OVERSEAS_DEPS)]
        if not metro.empty:
            event = viz.show(viz.choropleth(metro, geojson(), f.metric), key="map", on_select="rerun",
                             selection_mode="points")
            points = event.selection.points if event else []
            if points and points[0].get("location"):
                st.session_state["drill_dep"] = points[0]["location"]
            st.caption("Click a department to open it in the drill-down below (overseas: see the ranking).")
    with right:
        st.markdown("**Many accidents ≠ deadly accidents**")
        big = dep[dep["accidents"] >= 30].reset_index(drop=True)
        if len(big) >= 3:
            viz.show(viz.dep_scatter(big, average))
            if big["rural_share"].std() > 0:
                r = big["lethality"].corr(big["rural_share"])
                st.caption(f"Correlation between lethality and share of rural accidents: **r = {r:.2f}** "
                           "(association, not causation).")

    st.subheader(f"Top 10 departments: {f.metric_label.lower()}")
    pool = dep[dep["accidents"] >= MIN_ACC] if f.metric == "lethality" else dep
    if not pool.empty:
        ref = average if f.metric == "lethality" else dep[f.metric].mean()
        viz.show(viz.ranking_bar(pool.nlargest(10, f.metric), f.metric, ref))
        st.caption(f"Lethality ranking: departments with {MIN_ACC}+ accidents only. Counts are not "
                   "population-adjusted, so big departments rank high.")

    st.subheader("Which roads? Share of accidents vs share of deaths")
    dim = st.segmented_control("Break down by", list(BREAKDOWNS), default="Road type", required=True)
    viz.show(viz.share_bars(breakdown_table(acc, *BREAKDOWNS[dim]), dim.lower()))
    if dim == "Speed limit":
        st.caption("80 km/h roads are mostly two-way rural roads: their toll reflects the type of road and traffic, "
                   "not the effect of the limit itself.")

    st.subheader("What goes together with deadly accidents? Correlations between departments")
    corr = correlation_matrix(acc)
    if corr is None:
        st.info(f"The matrix needs at least 10 departments with {MIN_ACC}+ accidents: widen the selection.")
    else:
        left, right = st.columns([3, 2])
        with left:
            viz.show(viz.corr_heatmap(corr))
        top = corr["Lethality"].drop("Lethality").sort_values()
        right.markdown(
            "**Read the first column**: how each indicator moves with lethality, department by department.\n\n"
            "Deadlier departments score **higher** on " + ", ".join(f"*{k}* ({v:+.2f})" for k, v in
                                                                   top[::-1].head(3).items()) +
            " and **lower** on " + ", ".join(f"*{k}* ({v:+.2f})" for k, v in top.head(2).items()) + ".\n\n"
            "The rural factors are also linked **to each other** (dark blue block): rural roads, 80 km/h limits, "
            "darkness and roadside obstacles come together, so the matrix cannot say which one matters most.")
        right.caption(f"Pearson correlation on departments with {MIN_ACC}+ accidents. Correlation is not "
                      "causation. Small departments look deadlier partly because minor accidents are less often "
                      "reported there.")

    st.subheader("Drill down into one department")
    names = dict(zip(dep["dep"], dep["dep_name"]))
    options = dep.sort_values("killed", ascending=False)["dep"].tolist()
    if st.session_state.get("drill_dep") not in options:
        st.session_state["drill_dep"] = options[0]
    code = st.selectbox("Department", options, key="drill_dep", format_func=lambda c: f"{c} – {names[c]}")
    one = acc[acc["dep"] == code]
    s = summarize(one)
    k = st.columns(4)
    k[0].metric("Injury accidents", f"{s['accidents']:,}", border=True)
    k[1].metric("People killed", f"{s['killed']:,}", border=True)
    k[2].metric("Killed per 100 accidents", f"{s['lethality']:.1f}", f"{s['lethality'] - average:+.1f} vs selection",
                delta_color="inverse", border=True)
    k[3].metric("Accidents on rural roads", f"{100 * (one['area'] == 'Rural').mean():.0f}%", border=True)
    pts = one[one["geo_ok"]]
    pts = pd.concat([pts[~pts["fatal"]].sample(min(4000, (~pts["fatal"]).sum()), random_state=K.SEED),
                     pts[pts["fatal"]]])
    if not pts.empty:
        pts = pts.assign(label=pts["date"].dt.strftime("%d %b %Y") + " · " + pts["area"].astype(str) + " · "
                         + pts["n_killed"].astype(str) + " killed")
        viz.show(viz.points_map(pts))
        st.caption("Every fatal accident is shown; non-fatal ones are a random sample of up to 4,000.")


# --------------------------------------------------------------------------- Who
def render_who(f: Filters, users: pd.DataFrame) -> None:
    killed = users[users["killed"]]
    if killed.empty:
        st.info("No death in this selection.")
        return
    by_mode = pd.DataFrame({"killed": killed.groupby("mode", observed=True).size(),
                            "involved": users.groupby("mode", observed=True).size()}).fillna(0).reset_index()
    by_mode["per1000"] = 1000 * by_mode["killed"] / by_mode["involved"]
    rates = by_mode[by_mode["involved"] >= 200]
    car = by_mode.set_index("mode")["per1000"].get("Car", np.nan)
    exposed = rates[rates["per1000"] >= 1.5 * car]["mode"].tolist()
    if exposed:
        ratio = rates.set_index("mode").loc[exposed, "per1000"] / car
        headline(f"Car occupants are {100 * by_mode.set_index('mode')['killed'].get('Car', 0) / len(killed):.0f}% "
                 f"of the dead, but once involved in an accident, <b>{', '.join(PEOPLE[m] for m in exposed)}</b> "
                 f"die {ratio.min():.1f}–{ratio.max():.1f}× as often as car occupants.")
    left, right = st.columns(2)
    with left:
        st.markdown("**How many die?** People killed, by road user")
        viz.show(viz.hbar(by_mode, "mode", "killed", "people killed"))
    with right:
        st.markdown("**How exposed are they?** Killed per 1,000 people involved in an accident")
        viz.show(viz.hbar(rates, "mode", "per1000", "killed per 1,000 involved", ".1f", exposed))
        st.caption("Orange: at least 1.5× the car-occupant rate. A rate per accident, not per km travelled "
                   "(the data have no traffic volumes).")

    st.markdown("**Two age peaks: young adults and the over-75s**")
    left, right = st.columns([3, 2])
    with left:
        viz.show(viz.age_pyramid(killed))
    young, old = killed[killed["age_band"] == "18–24"], killed[killed["age_band"] == "75+"]
    right.markdown(
        f"- **{100 * (killed['sexe'] == 1).sum() / len(killed):.0f}%** of the people killed are men.\n"
        f"- **18–24-year-olds**: {len(young):,} deaths, {100 * (young['mode'] == 'Car').mean():.0f}% in a car.\n"
        f"- **75 and over**: {len(old):,} deaths, **{100 * (old['mode'] == 'Pedestrian').mean():.0f}%** of them "
        "pedestrians — a low-speed urban impact can be fatal at that age.")

    if f.years[0] < f.years[1]:
        st.markdown("**Trends by road user** — each panel has its own scale")
        trend = killed.groupby(["year", "mode"], observed=True).size().rename("killed").reset_index()
        viz.show(viz.small_multiples(trend, "year", "killed"))
        st.caption("E-scooters (EDP) are the fastest-growing group, from a low base.")


# --------------------------------------------------------------------------- When
def render_when(acc: pd.DataFrame, users: pd.DataFrame) -> None:
    a = acc.dropna(subset=["hour"]).astype({"hour": int})
    night, day = a[a["weekend"] & (a["hour"] < 6)], a[~a["weekend"] & a["hour"].between(7, 19)]
    if len(night) >= 50:
        ln, ld = 100 * night["n_killed"].sum() / len(night), 100 * day["n_killed"].sum() / len(day)
        headline(f"Most accidents happen at rush hour, but the deadliest are at night: on weekend nights "
                 f"(Sat–Sun, midnight–6 a.m.) <b>{ln:.1f} people die per 100 accidents</b>, {ln / ld:.1f}× the "
                 f"weekday-daytime rate ({ld:.1f}).")
    view = st.segmented_control("Colour the grid by", ["Injury accidents", "People killed", "Killed per 100 accidents"],
                                default="Killed per 100 accidents", required=True)
    g = summarize(a, ["weekday", "hour"])
    g.loc[g["accidents"] < 30, "lethality"] = np.nan  # too few accidents for a stable ratio
    col = {"Injury accidents": "accidents", "People killed": "killed", "Killed per 100 accidents": "lethality"}[view]
    grid = g.pivot(index="weekday", columns="hour", values=col).reindex(index=range(7), columns=range(24))
    grid.index = K.WEEKDAYS
    viz.show(viz.heatmap(grid, view.lower()))

    left, right = st.columns([3, 2])
    light = summarize(a[a["light_group"] != "Unknown"], "light_group").rename(columns={"light_group": "label"})
    light["share_acc"] = 100 * light["accidents"] / light["accidents"].sum()
    light["share_killed"] = 100 * light["killed"] / light["killed"].sum()
    with left:
        st.markdown("**Darkness without street lights is the deadliest condition**")
        viz.show(viz.share_bars(light, "lighting"))
    unlit = light.set_index("label").reindex(["Night – unlit"]).iloc[0]
    if not np.isnan(unlit["accidents"]):
        right.markdown(f"Roads **without lighting at night** host {unlit['share_acc']:.0f}% of injury accidents but "
                       f"**{unlit['share_killed']:.0f}% of deaths**. They are mostly rural roads: darkness, speed and "
                       "the road environment add up.")

    st.markdown("**Motorcyclists die in summer; pedestrians and car occupants in the dark months**")
    k = users[users["killed"]].merge(acc[["acc_id", "month"]], on="acc_id")
    k = k[k["mode"].isin(["Car", "Motorcycle >50cc", "Pedestrian", "Bicycle"])]
    season = k.groupby(["mode", "month"], observed=True).size().rename("killed").reset_index()
    season["month_name"] = season["month"].map(lambda m: K.MONTHS[m - 1])
    viz.show(viz.small_multiples(season, "month_name", "killed", kind="bar"))


def render() -> None:
    f = current_filters()
    acc, users = filtered(f)
    if not page_header("Where, who, when", f, acc):
        return
    where, who, when = st.tabs(["📍 Where", "👥 Who", "🕒 When"])
    with where:
        render_where(f, acc)
    with who:
        render_who(f, users)
    with when:
        render_when(acc, users)
