"""2 · KPIs tied to the filters and the high-level trends."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import current_filters, empty_guard, headline, scope_note
from utils import viz
from utils.filters import filtered, filtered_all_years
from utils.metrics import METRIC_HELP, pct, summarize, totals


def _delta(cur: float, prev: float | None, pct_mode: bool = True) -> str | None:
    if prev is None or pd.isna(prev) or prev == 0:
        return None
    return f"{100 * (cur - prev) / prev:+.1f}% vs prev. year" if pct_mode else f"{cur - prev:+.1f} pts vs prev. year"


def render() -> None:
    f = current_filters()
    acc, users = filtered(f)
    st.title("The big picture")
    scope_note(f)
    if empty_guard(acc):
        return

    tot = totals(acc)
    acc_all, _ = filtered_all_years(f)
    yearly = summarize(acc_all, "year").set_index("year")
    last = f.years[1]
    cur = yearly.loc[last] if last in yearly.index else None
    prev = yearly.loc[last - 1] if (last - 1) in yearly.index else None
    n_years = f.years[1] - f.years[0] + 1
    rural = acc[acc["area"] == "Rural"]["n_killed"].sum()
    rural_share = pct(rural, tot["killed"])

    headline(f"Over {f.describe().split(' · ')[0]}, <b>{tot['killed']:,} people were killed</b> in "
             f"{tot['accidents']:,} injury accidents: <b>{tot['lethality']:.1f} deaths for every 100 accidents</b>"
             + (f", and {rural_share:.0f}% of these deaths happened on rural roads." if f.area == "All" else "."))

    # ---------------- KPI header (tied to filters) ----------------
    st.markdown(f"##### Key figures — {n_years}-year total; arrows compare **{last}** with {last - 1}")
    c = st.columns(5)
    pv = lambda col: None if prev is None else prev[col]  # noqa: E731
    cv = lambda col: None if cur is None else cur[col]  # noqa: E731
    c[0].metric("Injury accidents", f"{tot['accidents']:,}",
                _delta(cv("accidents"), pv("accidents")) if cur is not None else None,
                delta_color="inverse", border=True, help=METRIC_HELP["accidents"])
    c[1].metric("People killed", f"{tot['killed']:,}", _delta(cv("killed"), pv("killed")) if cur is not None else None,
                delta_color="inverse", border=True, help=METRIC_HELP["killed"])
    c[2].metric("Hospitalised", f"{tot['hosp']:,}", _delta(cv("hosp"), pv("hosp")) if cur is not None else None,
                delta_color="inverse", border=True,
                help="Hospitalised more than 24 h. No longer labelled as an official statistic since 2019: use with care.")
    c[3].metric("Deaths / 100 acc.", f"{tot['lethality']:.1f}",
                _delta(cv("lethality"), pv("lethality"), pct_mode=False) if cur is not None else None,
                delta_color="inverse", border=True, help="People killed per 100 injury accidents. " + METRIC_HELP["lethality"])
    c[4].metric("Deaths on rural roads", f"{rural_share:.0f}%", border=True,
                help="Accidents outside built-up areas (hors agglomération).")

    # ---------------- Monthly trend ----------------
    st.subheader("Month by month: lockdowns, then a plateau")
    m = summarize(acc, "ym")
    k_first = yearly["killed"].get(2021)
    k_last = yearly["killed"].get(2024)
    trend_txt = (f"Deaths went from {k_first:,} in 2021 to {k_last:,} in 2024 under the current filters"
                 if k_first is not None and k_last is not None else "")
    peak = m.loc[m["killed"].idxmax()]
    viz.show(viz.monthly_trend(m),
             alt=(f"Two aligned line charts, one point per month from {m['ym'].min():%B %Y} to {m['ym'].max():%B %Y}. "
                  f"Top: injury accidents, bottom: people killed. Grey bands mark the three COVID lockdowns, "
                  f"when both lines dropped sharply. The deadliest month is {peak['ym']:%B %Y} "
                  f"with {peak['killed']:,} deaths. {trend_txt}."),
             key="ov_monthly",
             table=m.assign(month=m["ym"].dt.strftime("%Y-%m"))[["month", "accidents", "killed", "hosp", "lethality"]]
             .round(2))
    st.caption("Summer peaks are driven by motorcyclists and holiday traffic; the 2020 dips are lockdowns, "
               "not progress. Source: BAAC 2020–2024.")

    # ---------------- Urban vs rural by year ----------------
    if f.area == "All":
        st.subheader("Two thirds of deaths happen outside towns")
        ya = summarize(acc, ["year", "area"])
        ya = ya[ya["area"].isin(["Urban", "Rural"])]
        ya["share"] = 100 * ya["killed"] / ya.groupby("year")["killed"].transform("sum")
        left, right = st.columns([3, 2])
        with left:
            viz.show(viz.area_year_bars(ya),
                     alt=("Grouped bar chart of people killed per year on urban and rural roads. Rural roads "
                          "(orange) account for " + ", ".join(f"{int(r.year)}: {r.share:.0f}%" for r in
                                                              ya[ya.area == 'Rural'].itertuples()) + " of deaths."),
                     key="ov_area", table=ya[["year", "area", "accidents", "killed", "lethality"]].round(2))
        with right:
            by_area = summarize(acc, "area").set_index("area")
            if {"Urban", "Rural"} <= set(by_area.index):
                ru, ur = by_area.loc["Rural"], by_area.loc["Urban"]
                st.markdown(
                    f"**Rural roads** carry **{pct(ru['accidents'], tot['accidents']):.0f}%** of injury accidents "
                    f"but **{pct(ru['killed'], tot['killed']):.0f}%** of deaths.\n\n"
                    f"Once an accident happens outside a town, it kills "
                    f"**{ru['lethality']:.1f}** people per 100 accidents, against **{ur['lethality']:.1f}** in "
                    f"towns: **{ru['lethality'] / ur['lethality']:.1f}× deadlier**.\n\n"
                    "Likely reasons (not measured in this dataset): higher speeds on two-way roads with no "
                    "separation between directions, trees and ditches close to the road, darker roads at night "
                    "and longer emergency response times. The data show an *association*; section 3 looks at "
                    "it road by road.")
    else:
        st.info("Select **All** in *Road environment* to compare urban and rural roads.")
