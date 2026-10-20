"""3 · Comparisons, distributions and drill-downs: where, who, when."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from sections.common import current_filters, empty_guard, headline, scope_note
from utils import constants as K
from utils import viz
from utils.filters import Filters, get_data
from utils.filters import filtered
from utils.io import load_geojson
from utils.metrics import METRIC_UNITS, pct, summarize, totals

MIN_ACC_FOR_RATE = 100
PEOPLE = {"Pedestrian": "pedestrians", "Motorcycle >50cc": "motorcyclists", "Bicycle": "cyclists",
          "Car": "car occupants", "Moped ≤50cc": "moped riders", "E-scooter (EDP)": "e-scooter riders",
          "Van / truck / bus": "van, truck & bus occupants", "Other": "other road users"}  # departments below this are too small for a stable lethality ratio


@st.cache_data(show_spinner=False)
def geojson() -> dict:
    return load_geojson()


def dep_table(acc: pd.DataFrame) -> pd.DataFrame:
    d = summarize(acc, ["dep", "dep_name", "region"])
    rural = acc.assign(r=acc["area"].eq("Rural")).groupby("dep", observed=True)["r"].mean()
    d["rural_share"] = d["dep"].map(rural).astype(float)
    d["dep"] = d["dep"].astype(str)
    d["dep_name"] = d["dep_name"].astype(str)
    return d


# ---------------------------------------------------------------------------
# WHERE
# ---------------------------------------------------------------------------
BREAKDOWNS = {
    "Road type": ("catr", K.CATR),
    "Speed limit": ("vma", None),
    "Collision type": ("col", K.COL),
    "Intersection": ("int", K.INT),
}


def breakdown_table(acc: pd.DataFrame, col: str, labels: dict | None) -> pd.DataFrame:
    d = summarize(acc.dropna(subset=[col]), col)
    if labels is None:  # speed limit
        d = d[d["accidents"] >= 300]
        d["label"] = d[col].astype(int).astype(str) + " km/h"
    else:
        d["label"] = d[col].map(labels).fillna("Other")
    d = d.groupby("label", as_index=False)[["accidents", "killed"]].sum()
    d["share_acc"] = 100 * d["accidents"] / d["accidents"].sum()
    d["share_killed"] = 100 * d["killed"] / d["killed"].sum()
    d["lethality"] = 100 * d["killed"] / d["accidents"]
    small = d["share_acc"] < 0.5
    if small.sum() > 1:
        other = d[small][["accidents", "killed"]].sum()
        d = pd.concat([d[~small], pd.DataFrame([{"label": "Other (small groups)", **other.to_dict()}])])
        d["share_acc"] = 100 * d["accidents"] / d["accidents"].sum()
        d["share_killed"] = 100 * d["killed"] / d["killed"].sum()
        d["lethality"] = 100 * d["killed"] / d["accidents"]
    return d


def render_where(f: Filters, acc: pd.DataFrame) -> None:
    tot = totals(acc)
    by_area = summarize(acc, "area").set_index("area")
    if {"Rural", "Urban"} <= set(by_area.index):
        ru, ur = by_area.loc["Rural"], by_area.loc["Urban"]
        headline(f"Outside towns, <b>one injury accident in {100 / max(ru['lethality'], 0.01):.0f} kills someone</b>; "
                 f"in towns it is one in {100 / max(ur['lethality'], 0.01):.0f}. The deadliest departments are "
                 f"rural ones, not the ones with the most accidents.")
    else:
        headline(f"{tot['killed']:,} people killed in {tot['accidents']:,} accidents "
                 f"({tot['lethality']:.1f} per 100) in this selection.")

    dep = dep_table(acc)
    metric = f.metric
    unit = METRIC_UNITS[metric]
    metro = dep[~dep["dep"].isin(K.OVERSEAS_DEPS)]

    # ---- Map + scatter ----
    left, right = st.columns([1.05, 1])
    with left:
        st.markdown(f"**{f.metric_label} by department**")
        if metro.empty:
            st.info("The map covers metropolitan France; overseas territories are compared in the ranking below.")
        else:
            best = metro.sort_values(metric, ascending=False).iloc[0]
            event = viz.show(
                viz.choropleth(metro, geojson(), metric),
                alt=(f"Map of metropolitan France, departments shaded by {unit} (darker = higher). "
                     f"Highest: {best['dep_name']} ({best[metric]:,.{1 if metric == 'lethality' else 0}f} {unit}). "
                     + ("Lethality is highest across rural central and north-eastern departments and lowest "
                        "around Paris." if metric == "lethality" else
                        "Large urban departments stand out on counts.")),
                key="where_map", on_select="rerun", selection_mode="points")
            pts = (event or {}).get("selection", {}).get("points", []) if event else []
            if pts and pts[0].get("location"):
                st.session_state["drill_dep"] = pts[0]["location"]
            st.caption("Click a department to open it in the drill-down below. Overseas territories are "
                       "not drawn on the map but are in the ranking.")
    with right:
        st.markdown("**Many accidents ≠ deadly accidents**")
        d_sc = dep[dep["accidents"] >= 30]
        if len(d_sc) >= 3:
            national = 100 * dep["killed"].sum() / dep["accidents"].sum()
            labels = list(dict.fromkeys([d_sc.nlargest(1, "lethality")["dep"].iloc[0],
                                         d_sc.nlargest(1, "accidents")["dep"].iloc[0],
                                         d_sc.nlargest(1, "killed")["dep"].iloc[0]]))
            corr = d_sc[["lethality", "rural_share"]].corr().iloc[0, 1]
            viz.show(viz.dep_scatter(d_sc, national, labels),
                     alt=(f"Scatter plot, one bubble per department (bubble size = deaths, colour = share of rural "
                          f"accidents). X: number of accidents (log scale); Y: killed per 100 accidents. "
                          f"Departments with the most accidents have low lethality, while the most lethal are "
                          f"rural. Correlation between lethality and rural share: {corr:.2f}."),
                     key="where_scatter",
                     table=d_sc[["dep", "dep_name", "accidents", "killed", "lethality", "rural_share"]]
                     .round(3).sort_values("lethality", ascending=False))
            st.caption(f"Correlation between a department's lethality and its share of rural accidents: "
                       f"**r = {corr:.2f}** (association, not causation).")
        else:
            st.info("Select more departments to compare them.")

    # ---- Ranking ----
    st.subheader(f"Ranking: {f.metric_label.lower()}")
    c1, c2, _ = st.columns([1, 2, 2])
    side = c1.segmented_control("Show", ["Highest", "Lowest"], default="Highest", key="rank_side", required=True)
    n = c2.slider("Number of departments", 5, 20, 10, key="rank_n")
    rank = dep[dep["accidents"] >= MIN_ACC_FOR_RATE] if metric == "lethality" else dep
    if rank.empty:
        st.info("Not enough accidents in this selection for a ranking.")
    else:
        top = side == "Highest"
        rk = rank.sort_values(metric, ascending=not top).head(n)
        national = (100 * dep["killed"].sum() / dep["accidents"].sum()) if metric == "lethality" \
            else dep[metric].mean()
        viz.show(viz.ranking_bar(rk, metric, national, top),
                 alt=(f"Horizontal bar chart of the {len(rk)} departments with the {side.lower()} {unit}: "
                      + ", ".join(f"{r.dep_name} {getattr(r, metric):,.{1 if metric == 'lethality' else 0}f}"
                                  for r in rk.head(5).itertuples())
                      + (f". Dotted line: average {national:,.1f}." if national else "")),
                 key="where_rank",
                 table=rk[["dep", "dep_name", "region", "accidents", "killed", "lethality"]].round(2))
        note = (f"Departments with fewer than {MIN_ACC_FOR_RATE} accidents over the period are left out: "
                "their ratio is too unstable." if metric == "lethality"
                else "The dotted line is the average department of the selection.")
        st.caption(note + " Counts are not population-adjusted — big departments naturally rank high.")

    # ---- Breakdown ----
    st.subheader("Which roads? Share of accidents vs share of deaths")
    dim = st.segmented_control("Break down by", list(BREAKDOWNS), default="Road type", key="where_dim",
                               required=True)
    col, labels = BREAKDOWNS[dim]
    bd = breakdown_table(acc, col, labels)
    worst = bd.sort_values("lethality", ascending=False).iloc[0]
    over = bd.assign(r=bd["share_killed"] / bd["share_acc"]).sort_values("r", ascending=False).iloc[0]
    viz.show(viz.share_bars(bd, "label", dim.lower()),
             alt=(f"Grouped horizontal bars comparing, for each {dim.lower()}, its share of injury accidents (blue) "
                  f"and its share of deaths (orange). {over['label']} is the most over-represented: "
                  f"{over['share_acc']:.0f}% of accidents but {over['share_killed']:.0f}% of deaths. "
                  f"Highest lethality: {worst['label']} ({worst['lethality']:.1f} killed per 100 accidents)."),
             key="where_breakdown",
             table=bd[["label", "accidents", "killed", "share_acc", "share_killed", "lethality"]].round(2))
    if dim == "Speed limit":
        st.caption("80 km/h roads are mostly two-way rural roads (limit lowered from 90 in 2018). Their high toll "
                   "reflects the type of road, traffic and exposure — this chart does not measure the effect of "
                   "the limit itself.")

    # ---- Correlation matrix ----
    render_correlations(acc)

    # ---- Drill-down ----
    st.subheader("Drill down into one department")
    options = dep.sort_values("killed", ascending=False)["dep"].tolist()
    names = dict(zip(dep["dep"], dep["dep_name"]))
    if st.session_state.get("drill_dep") not in options:
        st.session_state["drill_dep"] = options[0]
    code = st.selectbox("Department", options, key="drill_dep", format_func=lambda c: f"{c} – {names.get(c, c)}")
    a_dep = acc[acc["dep"].astype(str) == code]
    s = totals(a_dep)
    ref = 100 * tot["killed"] / tot["accidents"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Injury accidents", f"{s['accidents']:,}", border=True)
    k2.metric("People killed", f"{s['killed']:,}", border=True)
    k3.metric("Killed per 100 accidents", f"{s['lethality']:.1f}", f"{s['lethality'] - ref:+.1f} vs selection",
              delta_color="inverse", border=True)
    k4.metric("Accidents on rural roads", f"{100 * a_dep['area'].eq('Rural').mean():.0f}%", border=True)

    pts = a_dep[a_dep["geo_ok"]].copy()
    fatal = pts[pts["fatal"]]
    other = pts[~pts["fatal"]]
    if len(other) > 4000:
        other = other.sample(4000, random_state=K.SEED)
    pts = pd.concat([other, fatal])
    if pts.empty:
        st.info("No geolocated accident for this department and filters.")
        return
    pts["date_str"] = pts["date"].dt.strftime("%d %b %Y") + " " + pts["hour"].astype(str) + "h"
    pts["road"] = pts["catr"].map(K.CATR).fillna("road type unknown")
    pts["area"] = pts["area"].astype(str)
    lat_span = pts["lat"].quantile(0.98) - pts["lat"].quantile(0.02)
    lon_span = pts["lon"].quantile(0.98) - pts["lon"].quantile(0.02)
    span = max(lat_span, lon_span * 0.7, 0.05)
    zoom = float(np.clip(np.log2(180 / span) - 0.6, 4, 12))
    viz.show(viz.points_map(pts, (pts["lat"].median(), pts["lon"].median()), zoom),
             alt=(f"Street map of {names.get(code, code)} with one dot per accident: {len(fatal):,} fatal accidents "
                  f"in orange, other accidents in light blue"
                  + (" (random sample of 4,000)" if len(a_dep) - len(fatal) > 4000 else "") +
                  ". Use it to spot roads where fatal accidents repeat."),
             key="where_points")
    st.caption(f"Fatal accidents: all shown. Non-fatal: up to 4,000 drawn at random (seed {K.SEED}) to keep the map "
               "fast. Points whose GPS falls outside the department are excluded (0.01 %).")


# ---------------------------------------------------------------------------
# Correlation matrix (one row per department)
# ---------------------------------------------------------------------------
CORR_LABELS = {
    "leth": "Lethality",
    "log_acc": "Accidents (log)",
    "rural": "% rural",
    "unlit": "% night, unlit",
    "night": "% night (all)",
    "vma80": "% on 80 km/h roads",
    "obst": "% fixed obstacle",
    "lone": "% single vehicle",
    "wkend": "% weekend",
    "moto": "% motorcycle",
    "ped": "% pedestrian",
}
CORR_DEFS = {
    "Lethality": "people killed per 100 injury accidents",
    "Accidents (log)": "number of injury accidents in the department (log10)",
    "% rural": "accidents outside built-up areas",
    "% night, unlit": "accidents at night on a road without street lighting",
    "% night (all)": "accidents at night, lit or unlit",
    "% on 80 km/h roads": "accidents where the speed limit is 80 km/h",
    "% fixed obstacle": "accidents where a vehicle hit a fixed obstacle (tree, pole, wall, ditch…)",
    "% single vehicle": "accidents with one vehicle and nobody else involved (loss of control)",
    "% weekend": "accidents on Saturday or Sunday",
    "% motorcycle": "accidents involving a motorcycle >50 cc",
    "% pedestrian": "accidents involving a pedestrian",
}

CORR_PHRASES = {
    "Accidents (log)": "accidents overall", "% rural": "accidents on rural roads",
    "% night, unlit": "accidents on unlit roads at night", "% night (all)": "night-time accidents",
    "% on 80 km/h roads": "accidents on 80 km/h roads", "% fixed obstacle": "crashes into fixed obstacles",
    "% single vehicle": "single-vehicle crashes", "% weekend": "weekend accidents",
    "% motorcycle": "accidents involving a motorcycle", "% pedestrian": "accidents involving a pedestrian",
}


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def department_features(acc: pd.DataFrame, min_acc: int = MIN_ACC_FOR_RATE) -> pd.DataFrame:
    """One row per department: lethality and the share of accidents with each characteristic (%)."""
    a = acc.assign(
        rural=acc["area"].eq("Rural"),
        unlit=acc["lum"].isin([3, 4]),
        vma80=acc["vma"].eq(80).where(acc["vma"].notna()).astype("float"),
        ped=acc["n_ped"] > 0,
        lone=acc["single_vehicle"] & (acc["n_ped"] == 0),
    )
    g = a.groupby("dep", observed=True)
    n = g.size()
    feats = pd.DataFrame({
        "leth": 100 * g["n_killed"].sum() / n,
        "log_acc": np.log10(n),
        "rural": 100 * g["rural"].mean(),
        "unlit": 100 * g["unlit"].mean(),
        "night": 100 * g["night"].mean(),
        "vma80": 100 * g["vma80"].mean(),
        "obst": 100 * g["hit_fixed_obstacle"].mean(),
        "lone": 100 * g["lone"].mean(),
        "wkend": 100 * g["weekend"].mean(),
        "moto": 100 * g["has_moto"].mean(),
        "ped": 100 * g["ped"].mean(),
    })
    feats = feats[n >= min_acc].astype(float)
    # A column that does not vary (e.g. % rural when only rural roads are selected) has no correlation
    return feats.loc[:, feats.std() > 1e-9]


def render_correlations(acc: pd.DataFrame) -> None:
    st.subheader("What goes together with deadly accidents? Correlations between departments")
    feats = department_features(acc)
    if len(feats) < 10 or "leth" not in feats:
        st.info(f"The correlation matrix needs at least 10 departments with {MIN_ACC_FOR_RATE}+ accidents. "
                "Widen the selection in the sidebar.")
        return
    method = st.segmented_control(
        "Correlation", ["Pearson", "Spearman"], default="Pearson", key="corr_method", required=True,
        help="Pearson measures a straight-line relationship; Spearman uses ranks and is less sensitive to "
             "outlier departments.")
    corr = feats.corr(method=method.lower())
    order = ["leth"] + corr["leth"].drop("leth").sort_values(ascending=False).index.tolist()
    corr = corr.loc[order, order].rename(index=CORR_LABELS, columns=CORR_LABELS)
    with_leth = corr["Lethality"].drop("Lethality")
    pos = with_leth[with_leth > 0.3].head(3)
    neg = with_leth[with_leth < -0.3].sort_values().head(2)

    left, right = st.columns([3, 2])
    with left:
        viz.show(
            viz.corr_heatmap(corr),
            alt=(f"Correlation matrix ({method}) between {len(corr)} department-level indicators, computed on "
                 f"{len(feats)} departments. Blue = positive, red = negative. Strongest links with lethality: "
                 + ", ".join(f"{k} (r = {v:+.2f})" for k, v in pd.concat([pos, neg]).items()) + "."),
            key="where_corr", table=corr.round(2).reset_index().rename(columns={"index": "indicator"}))
    with right:
        st.markdown(f"**Read the first column** — how each indicator moves with lethality across "
                    f"**{len(feats)} departments**:")
        if len(pos):
            st.markdown("Deadlier departments have a **higher share** of " + _join(
                [f"{CORR_PHRASES[k]} (r = {v:+.2f})" for k, v in pos.items()]) + ".")
        if len(neg):
            st.markdown("They have " + _join(
                [("**fewer** " if k == "Accidents (log)" else "a **lower share** of ") + f"{CORR_PHRASES[k]} "
                 f"(r = {v:+.2f})" for k, v in neg.items()]) + ".")
        st.markdown("These rural factors are also strongly linked **to each other** (look at the dark blue block): "
                    "rural roads, 80 km/h limits, darkness and roadside obstacles come together. The matrix cannot "
                    "say which one matters most on its own.")
        st.caption(f"{method} correlation. Departments with fewer than {MIN_ACC_FOR_RATE} accidents are left out. "
                   "Correlation is not causation, and a link between departments does not prove the same link for "
                   "individual accidents. Small departments look deadlier partly because minor accidents are less "
                   "often reported by the police there.")
    with st.expander("Definitions of the indicators"):
        st.markdown("\n".join(f"- **{k}**: {CORR_DEFS[k]}" for k in corr.index))


# ---------------------------------------------------------------------------
# WHO
# ---------------------------------------------------------------------------
def render_who(f: Filters, acc: pd.DataFrame, users: pd.DataFrame) -> None:
    killed = users[users["killed"]]
    if killed.empty:
        st.info("No death in this selection.")
        return
    by_mode = pd.DataFrame({"killed": killed.groupby("mode", observed=True).size(),
                            "involved": users.groupby("mode", observed=True).size()}).fillna(0).reset_index()
    by_mode = by_mode[by_mode["involved"] > 0]
    by_mode["per1000"] = 1000 * by_mode["killed"] / by_mode["involved"]
    by_mode["share"] = 100 * by_mode["killed"] / by_mode["killed"].sum()
    car_rate = by_mode.loc[by_mode["mode"] == "Car", "per1000"]
    car_rate = float(car_rate.iloc[0]) if len(car_rate) else np.nan
    reliable = by_mode[by_mode["involved"] >= 200]
    top = reliable.sort_values("per1000", ascending=False).head(3)
    if not np.isnan(car_rate) and len(top):
        names = [PEOPLE.get(m, m) for m in top["mode"]]
        who = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
        headline(f"Car occupants are {by_mode.loc[by_mode['mode'] == 'Car', 'share'].iloc[0]:.0f}% of the dead, "
                 f"but once involved in an accident, <b>{who}</b> die "
                 f"{top['per1000'].min() / car_rate:.1f}–{top['per1000'].max() / car_rate:.1f}× as often as "
                 f"car occupants.")
    a, b = st.columns(2)
    with a:
        st.markdown("**How many die?** People killed, by road user")
        viz.show(viz.hbar(by_mode, "mode", "killed", "people killed"),
                 alt="Horizontal bar chart of people killed by road-user type: " +
                     ", ".join(f"{r.mode} {int(r.killed):,} ({r.share:.0f}%)" for r in
                               by_mode.sort_values("killed", ascending=False).itertuples()) + ".",
                 key="who_count")
    with b:
        st.markdown("**How exposed are they?** Killed per 1,000 people involved in an accident")
        hi = list(reliable[reliable["per1000"] >= 1.5 * car_rate]["mode"]) if not np.isnan(car_rate) else []
        viz.show(viz.hbar(reliable, "mode", "per1000", "killed per 1,000 involved", fmt=".1f", highlight=hi),
                 alt="Horizontal bar chart of deaths per 1,000 people involved in an injury accident: " +
                     ", ".join(f"{r.mode} {r.per1000:.1f}" for r in
                               reliable.sort_values("per1000", ascending=False).itertuples()) +
                     ". Orange bars are at least 1.5 times the rate of car occupants.",
                 key="who_rate",
                 table=by_mode[["mode", "involved", "killed", "share", "per1000"]].round(2)
                 .sort_values("killed", ascending=False))
        st.caption("Orange = at least 1.5× the car-occupant rate. Modes with fewer than 200 people involved are "
                   "hidden. This is a rate *once an accident happens*, not a risk per km travelled (no exposure "
                   "data in the source).")

    st.markdown("**Two age peaks: young adults and the over-75s**")
    left, right = st.columns([3, 2])
    pyr = killed.groupby(["age_band", "sexe"], observed=False).size().rename("killed").reset_index()
    pyr = pyr[pyr["sexe"].isin([1, 2])]
    with left:
        age_tot = killed.groupby("age_band", observed=False).size()
        viz.show(viz.age_pyramid(pyr),
                 alt=("Population-pyramid bar chart of people killed by age band, men on the left (blue), women on "
                      "the right (orange). Men largely dominate every band. Largest bands: " +
                      ", ".join(f"{i} ({v:,})" for i, v in age_tot.sort_values(ascending=False).head(3).items()) + "."),
                 key="who_pyramid",
                 table=pyr.pivot_table(index="age_band", columns="sexe", values="killed", observed=False)
                 .rename(columns={1: "men", 2: "women"}).reset_index())
    with right:
        men = 100 * killed["sexe"].eq(1).sum() / max(killed["sexe"].isin([1, 2]).sum(), 1)
        k_old = killed[killed["age_band"] == "75+"]
        k_young = killed[killed["age_band"] == "18–24"]
        old_ped = pct((k_old["mode"] == "Pedestrian").sum(), len(k_old))
        young_car = pct((k_young["mode"] == "Car").sum(), len(k_young))
        st.markdown(
            f"- **{men:.0f}%** of the people killed are men.\n"
            f"- **18–24-year-olds**: {len(k_young):,} deaths, {young_car:.0f}% of them in a car (inexperience, "
            f"night driving and speed are the factors usually cited — not measured here).\n"
            f"- **75 and over**: {len(k_old):,} deaths; **{old_ped:.0f}%** were pedestrians — older bodies are "
            f"more fragile, so a low-speed urban impact can be fatal.\n"
            "- Age is unknown for some people who fled the scene (recorded since 2021).")

    if f.years[1] > f.years[0]:
        st.markdown("**Trends by road user** — each panel has its own scale")
        sm = killed.groupby(["year", "mode"], observed=True).size().rename("killed").reset_index()
        full = pd.MultiIndex.from_product([range(f.years[0], f.years[1] + 1), sm["mode"].unique()],
                                          names=["year", "mode"])
        sm = sm.set_index(["year", "mode"]).reindex(full, fill_value=0).reset_index()
        edp = sm[sm["mode"] == "E-scooter (EDP)"].set_index("year")["killed"]
        edp_txt = (f" E-scooter deaths went from {edp.iloc[0]} to {edp.iloc[-1]}." if len(edp) > 1 else "")
        viz.show(viz.mode_small_multiples(sm),
                 alt=("Small multiples, one line chart per road-user type, showing people killed per year. "
                      "Most lines are flat after 2021." + edp_txt),
                 key="who_multiples",
                 table=sm.pivot(index="year", columns="mode", values="killed").reset_index())
        st.caption("E-scooters (EDP) are the fastest-growing group from a low base; their involvement in accidents "
                   "roughly tripled since 2020 as rental and private scooters spread.")


# ---------------------------------------------------------------------------
# WHEN
# ---------------------------------------------------------------------------
def render_when(f: Filters, acc: pd.DataFrame, users: pd.DataFrame) -> None:
    a = acc.dropna(subset=["hour"]).copy()
    a["hour"] = a["hour"].astype(int)
    wk_night = a[a["weekend"] & (a["hour"] < 6)]
    wd_day = a[(~a["weekend"]) & a["hour"].between(7, 19)]
    if len(wk_night) >= 50 and len(wd_day) >= 50:
        ln = 100 * wk_night["n_killed"].sum() / len(wk_night)
        ld = 100 * wd_day["n_killed"].sum() / len(wd_day)
        headline(f"Most accidents happen at rush hour, but the deadliest are at night: on weekend nights "
                 f"(Sat–Sun, midnight–6 a.m.) <b>{ln:.1f} people die per 100 accidents</b>, "
                 f"{ln / ld:.1f}× the weekday-daytime rate ({ld:.1f}).")
    view = st.segmented_control("Colour the grid by", ["Injury accidents", "People killed",
                                                       "Killed per 100 accidents"],
                                default="Killed per 100 accidents", key="when_metric", required=True)
    g = a.groupby(["weekday", "hour"]).agg(accidents=("acc_id", "size"), killed=("n_killed", "sum")).reset_index()
    g["lethality"] = np.where(g["accidents"] >= 30, 100 * g["killed"] / g["accidents"], np.nan)
    col = {"Injury accidents": "accidents", "People killed": "killed", "Killed per 100 accidents": "lethality"}[view]
    pv = g.pivot(index="weekday", columns="hour", values=col).reindex(index=range(7), columns=range(24))
    pv.index = K.WEEKDAYS
    mx = g.loc[g[col].idxmax()] if g[col].notna().any() else None
    viz.show(viz.heatmap(pv, {"accidents": "accidents", "killed": "killed", "lethality": "killed / 100 acc."}[col],
                         ".1f" if col == "lethality" else ",.0f"),
             alt=(f"Heatmap, days of the week in rows and hours in columns, coloured by {view.lower()}. "
                  + (f"Peak: {K.WEEKDAYS[int(mx['weekday'])]} at {int(mx['hour'])}h ({mx[col]:,.1f}). " if mx is not None else "")
                  + ("Accidents concentrate on weekday evening rush hours (5–7 p.m.); lethality is highest "
                     "between 1 and 6 a.m., especially at weekends." )),
             key="when_heat", table=pv.round(1).rename(columns=lambda h: f"{h:02d}h").rename_axis("day")
             .reset_index())
    st.caption("Cells with fewer than 30 accidents are left blank for the lethality view (ratio too noisy).")

    left, right = st.columns([3, 2])
    lt = summarize(a[a["light_group"] != "Unknown"], "light_group")
    lt["label"] = lt["light_group"].astype(str)
    lt["share_acc"] = 100 * lt["accidents"] / lt["accidents"].sum()
    lt["share_killed"] = 100 * lt["killed"] / lt["killed"].sum()
    unlit = lt[lt["label"] == "Night – unlit"]
    with left:
        st.markdown("**Darkness without street lights is the deadliest condition**")
        viz.show(viz.share_bars(lt, "label", "lighting"),
                 alt=("Grouped bars of the share of accidents and of deaths by lighting condition. " +
                      (f"Unlit night roads: {unlit['share_acc'].iloc[0]:.0f}% of accidents but "
                       f"{unlit['share_killed'].iloc[0]:.0f}% of deaths." if len(unlit) else "")),
                 key="when_light", table=lt[["label", "accidents", "killed", "share_acc", "share_killed",
                                             "lethality"]].round(2))
    with right:
        if len(unlit):
            u0 = unlit.iloc[0]
            st.markdown(
                f"Roads **without street lighting at night** host {u0['share_acc']:.0f}% of injury accidents "
                f"but **{u0['share_killed']:.0f}% of deaths**: {u0['lethality']:.1f} killed per 100 accidents.\n\n"
                "Unlit night roads are mostly rural roads, so darkness, speed and the road environment add up. "
                "Lit urban streets at night are far less deadly.")

    st.markdown("**Motorcyclists die in summer; pedestrians and car occupants in the dark months**")
    k = users[users["killed"]].merge(acc[["acc_id", "month"]], on="acc_id")
    sea = k.groupby(["mode", "month"], observed=True).size().rename("killed").reset_index()
    sea["month_name"] = sea["month"].map(lambda m: K.MONTHS[int(m) - 1])
    moto = sea[sea["mode"] == "Motorcycle >50cc"].set_index("month")["killed"]
    txt = (f" Motorcyclist deaths peak in {K.MONTHS[int(moto.idxmax()) - 1]} at "
           f"{moto.max() / max(moto.min(), 1):.1f}× their winter low." if len(moto) == 12 else "")
    viz.show(viz.seasonality(sea),
             alt="Four small bar charts of people killed by month for car occupants, motorcyclists, "
                 "pedestrians and cyclists, each with its own scale." + txt,
             key="when_season", table=sea.pivot(index="month", columns="mode", values="killed").reset_index())
    st.caption("Each panel has its own scale. Pedestrian deaths rise in autumn–winter, when it is dark at commuting "
               "time; motorcyclist and cyclist deaths follow the riding season.")


def render() -> None:
    f = current_filters()
    acc, users = filtered(f)
    st.title("Where, who, when")
    scope_note(f)
    if empty_guard(acc):
        return
    where, who, when = st.tabs(["📍 Where", "👥 Who", "🕒 When"])
    with where:
        render_where(f, acc)
    with who:
        render_who(f, acc, users)
    with when:
        render_when(f, acc, users)
