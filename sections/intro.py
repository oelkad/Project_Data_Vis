"""1 · Hook, context, audience and questions."""

from __future__ import annotations

import streamlit as st

from sections.common import headline, national_reference
from utils import constants as K
from utils import viz
from utils.about import about_card
from utils.filters import get_data


def render() -> None:
    ref = national_reference()
    q = get_data()["quality"]
    by_year = ref["by_year"]
    k24 = ref["killed_2024"]
    goal = K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    path_2024 = K.METRO_KILLED_2019 + (goal - K.METRO_KILLED_2019) * (2024 - 2019) / (K.EU_TARGET_YEAR - 2019)
    change_vs_2019 = 100 * (k24 - K.METRO_KILLED_2019) / K.METRO_KILLED_2019

    st.title("Road deaths in France: the curve has stopped falling")
    st.caption("A data story on 268,788 injury road accidents, 2020–2024 · ONISR accident database (BAAC), "
               "published on data.gouv.fr")
    about_card()

    headline(f"In 2024, <b>{k24:,} people</b> died on the roads of metropolitan France — almost "
             f"<b>{k24 / 365:.0f} a day</b>, and only <b>{abs(change_vs_2019):.1f}% fewer</b> than in 2019. "
             f"Europe's goal is to halve road deaths by 2030. At this pace, France will miss it by far.")

    c1, c2, c3 = st.columns(3)
    c1.metric("People killed in 2024 (metropolitan France)", f"{k24:,}",
              f"{change_vs_2019:+.1f}% vs 2019", delta_color="inverse", border=True,
              help="2019 official figure: 3,244 (ONISR). Killed = died within 30 days.")
    c2.metric("EU 2030 goal (−50% vs 2019)", f"≈ {goal:,.0f}", border=True,
              help="European Commission target for the 2021–2030 decade, baseline year 2019.")
    c3.metric("Gap to the straight-line path in 2024", f"{k24 - path_2024:+,.0f} deaths", border=True,
              help="Difference between recorded deaths and a linear path from 3,244 (2019) to ≈1,622 (2030).")

    st.subheader("Off track for 2030")
    viz.show(
        viz.target_path(by_year),
        alt=(f"Line chart. People killed per year in metropolitan France: "
             + ", ".join(f"{int(r.year)}: {int(r.killed):,}" for r in by_year.itertuples())
             + f". The dashed path to the EU goal falls from 3,244 in 2019 to {goal:,.0f} in 2030. "
               f"After the 2020 lockdown dip, deaths returned to about 3,200 a year, "
               f"{k24 - path_2024:,.0f} above the path in 2024."),
        key="intro_target",
    )
    st.caption("This chart ignores the sidebar filters: it compares national totals with the official goal. "
               "2019 value and goal from ONISR / European Commission; 2020–2024 computed from the dataset "
               "(they match ONISR's published totals).")

    st.subheader("Who this story is for")
    a, b = st.columns(2)
    with a:
        st.markdown(
            "**Primary audience — road-safety decision-makers at local level:** departmental road-safety "
            "coordinators in the *préfectures* and the *conseils départementaux* who manage the rural road "
            "network. They choose where to put speed checks, prevention campaigns and road works.\n\n"
            "**Secondary audience — citizens and journalists** who want to understand where the risk really is.")
    with b:
        st.markdown(
            "**Questions this app answers**\n"
            "1. Is road safety still improving since 2020? → *The big picture*\n"
            "2. **Where** are accidents the deadliest? → *Where, who, when*\n"
            "3. **Who** dies, and who is most exposed? → *Where, who, when*\n"
            "4. **When** do the deadliest accidents happen? → *Where, who, when*\n"
            "5. What would it take to reach the 2030 goal? → *What would it take?*")

    st.subheader("How to read this app")
    st.markdown(
        "- The **sidebar filters** (years, territory, region, department, urban/rural, road users) drive every "
        "KPI and chart of sections 2 and 3. The *metric* selector changes the map and the rankings.\n"
        "- Two numbers matter: **how many** people die (burden) and **lethality** — people killed per "
        "100 injury accidents (how deadly an accident is once it happens). A place can have few accidents and "
        "still be very deadly.\n"
        "- Hover any mark for exact values; open *Table view* under a chart to read the numbers.")

    st.info(
        f"**The data.** The national file of injury accidents (BAAC) is filled in by the police or gendarmerie "
        f"for every accident on a public road with at least one person needing care. Four tables per year — "
        f"accidents, locations, vehicles, people — joined on the accident ID: "
        f"**{q['n_accidents']:,} accidents** and **{q['n_users']:,} people** for 2020–2024. Light injuries are "
        f"under-reported and the 'hospitalised' indicator is no longer an official statistic — see "
        f"*Data quality & method* for every check and caveat.", icon=":material/database:")
