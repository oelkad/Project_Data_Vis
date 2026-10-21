"""1 · Hook, audience and questions."""

import streamlit as st

from sections.common import headline, national_reference
from utils import constants as K
from utils import viz
from utils.about import about_card
from utils.filters import get_data


def render() -> None:
    ref = national_reference()
    q = get_data()["quality"]
    k24 = ref["killed_2024"]
    goal = K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    path_2024 = K.METRO_KILLED_2019 - (K.METRO_KILLED_2019 - goal) * 5 / (K.EU_TARGET_YEAR - 2019)
    change = 100 * (k24 - K.METRO_KILLED_2019) / K.METRO_KILLED_2019

    st.title("Road deaths in France: the curve has stopped falling")
    st.caption(f"A data story on {q['n_accidents']:,} injury road accidents, 2020–2024 · ONISR accident database "
               "(BAAC), published on data.gouv.fr")
    about_card()
    headline(f"In 2024, <b>{k24:,} people</b> died on the roads of metropolitan France — almost "
             f"<b>{k24 / 365:.0f} a day</b>, and only <b>{-change:.1f}% fewer</b> than in 2019. Europe's goal is to "
             f"halve road deaths by 2030. At this pace, France will miss it by far.")

    c1, c2, c3 = st.columns(3)
    c1.metric("People killed in 2024 (metropolitan France)", f"{k24:,}", f"{change:+.1f}% vs 2019",
              delta_color="inverse", border=True)
    c2.metric("EU 2030 goal (−50% vs 2019)", f"≈ {goal:,.0f}", border=True)
    c3.metric("Gap to the path in 2024", f"{k24 - path_2024:+,.0f} deaths", border=True)

    st.subheader("Off track for 2030")
    viz.show(viz.target_path(ref["by_year"]))
    st.caption("National figures, independent of the filters. 2019 value: ONISR; goal: European Commission; "
               "2020–2024: this dataset (identical to the official ONISR totals).")

    st.subheader("Who this story is for")
    left, right = st.columns(2)
    left.markdown(
        "**Local road-safety decision-makers** — the road-safety teams of the *préfectures* and the *conseils "
        "départementaux* that run the rural road network. They decide where to put speed checks, campaigns and "
        "road works.\n\n**Also:** citizens and journalists who want to know where the risk really is.")
    right.markdown(
        "**Questions answered**\n"
        "1. Is road safety still improving? → *The big picture*\n"
        "2. **Where**, **who** and **when** are accidents the deadliest? → *Where, who, when*\n"
        "3. What would it take to reach the 2030 goal? → *What would it take?*")

    st.info("**How to read it.** The sidebar filters (years, territory, region, urban/rural) drive pages 2 and 3. "
            "Two numbers matter: **how many** people die, and the **lethality** — people killed per 100 injury "
            "accidents, i.e. how deadly an accident is once it happens. Hover any chart for exact values. "
            "The data come from the police file of injury accidents: 4 tables per year joined on the accident ID. "
            "Every check and caveat is on the *Data quality & method* page.", icon=":material/info:")
