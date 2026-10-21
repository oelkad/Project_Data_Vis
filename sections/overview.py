"""2 · Key figures and trends (follow the filters)."""

import streamlit as st

from sections.common import current_filters, headline, page_header
from utils import viz
from utils.filters import filtered, summarize


def render() -> None:
    f = current_filters()
    acc, _ = filtered(f)
    if not page_header("The big picture", f, acc):
        return
    tot = summarize(acc)
    yearly = summarize(filtered(f, all_years=True)[0], "year").set_index("year")
    rural_share = 100 * acc.loc[acc["area"] == "Rural", "n_killed"].sum() / max(tot["killed"], 1)
    headline(f"Over {f.describe().split(' · ')[0]}, <b>{tot['killed']:,} people were killed</b> in "
             f"{tot['accidents']:,} injury accidents: <b>{tot['lethality']:.1f} deaths for every 100 accidents</b>"
             + (f", and {rural_share:.0f}% of these deaths happened on rural roads." if f.area == "All" else "."))

    # KPI row: totals over the selected years; arrows compare the last selected year with the one before
    last = f.years[1]
    st.markdown(f"##### Key figures — arrows compare **{last}** with {last - 1}")

    def delta(col, points=False):
        if last - 1 not in yearly.index:
            return None
        cur, prev = yearly.loc[last, col], yearly.loc[last - 1, col]
        return f"{cur - prev:+.1f} pts" if points else f"{100 * (cur - prev) / prev:+.1f}%"

    c = st.columns(5)
    c[0].metric("Injury accidents", f"{tot['accidents']:,}", delta("accidents"), delta_color="inverse", border=True)
    c[1].metric("People killed", f"{tot['killed']:,}", delta("killed"), delta_color="inverse", border=True)
    c[2].metric("Hospitalised", f"{tot['hosp']:,}", delta("hosp"), delta_color="inverse", border=True,
                help="Hospitalised more than 24 h (no longer an official statistic since 2019).")
    c[3].metric("Deaths / 100 acc.", f"{tot['lethality']:.1f}", delta("lethality", points=True),
                delta_color="inverse", border=True)
    c[4].metric("Deaths on rural roads", f"{rural_share:.0f}%", border=True)

    st.subheader("Month by month: lockdowns, then a plateau")
    viz.show(viz.monthly_trend(summarize(acc, "ym")))
    st.caption("The 2020 dips are lockdowns, not progress. Summer peaks follow motorcyclists and holiday traffic.")

    if f.area != "All":
        return
    st.subheader("Two thirds of deaths happen outside towns")
    left, right = st.columns([3, 2])
    with left:
        viz.show(viz.area_year_bars(summarize(acc, ["year", "area"])))
    by_area = summarize(acc, "area").set_index("area")
    if {"Rural", "Urban"} <= set(by_area.index):
        ru, ur = by_area.loc["Rural"], by_area.loc["Urban"]
        right.markdown(
            f"**Rural roads** carry **{100 * ru['accidents'] / tot['accidents']:.0f}%** of injury accidents but "
            f"**{100 * ru['killed'] / tot['killed']:.0f}%** of deaths.\n\n"
            f"An accident outside a town kills **{ru['lethality']:.1f}** people per 100 accidents, against "
            f"**{ur['lethality']:.1f}** in towns: **{ru['lethality'] / ur['lethality']:.1f}× deadlier**.\n\n"
            "Likely reasons (not measured here): higher speeds on two-way roads, trees and ditches close to the "
            "road, darker roads and longer emergency response times.")
