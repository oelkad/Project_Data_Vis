"""Helpers shared by the pages, and the national reference figures used in the text."""

import streamlit as st

from utils import constants as K
from utils.filters import Filters, get_data, summarize


def current_filters() -> Filters:
    return st.session_state["filters"]


def headline(text: str) -> None:
    """The one-sentence key message at the top of a section."""
    st.markdown(f"<p style='font-size:1.25rem;line-height:1.45'>{text}</p>", unsafe_allow_html=True)


def page_header(title: str, f: Filters, acc) -> bool:
    """Title + current selection. Returns False (and shows a warning) when nothing matches the filters."""
    st.title(title)
    st.caption(f"Current selection: **{f.describe()}**")
    if acc.empty:
        st.warning("No accident matches the current filters. Widen the selection in the sidebar.")
    return not acc.empty


@st.cache_data(show_spinner=False)
def national_reference() -> dict:
    """Fixed figures for metropolitan France 2020–2024 (independent of the filters)."""
    acc, users = get_data()["accidents"], get_data()["users"]
    m = acc[acc["territory"] == "Metropolitan France"]
    k = users[users["acc_id"].isin(m["acc_id"]) & users["killed"]]
    involved = users[users["acc_id"].isin(m["acc_id"])].groupby("mode", observed=True).size()
    total = summarize(m)
    area = summarize(m, "area").set_index("area")
    light = summarize(m, "light_group").set_index("light_group")
    vma80 = m[m["vma"] == 80]
    wk_night, wd_day = m[m["weekend"] & (m["hour"] < 6)], m[~m["weekend"] & m["hour"].between(7, 19)]
    edp = k[k["mode"] == "E-scooter (EDP)"].groupby("year").size()
    old = k[k["age_band"] == "75+"]

    def share(part, whole="killed"):
        return 100 * part / total[whole]

    return {
        "by_year": summarize(m, "year"),
        "killed_2024": int(k["year"].eq(2024).sum()),
        "rural_acc_share": share(area.loc["Rural", "accidents"], "accidents"),
        "rural_killed_share": share(area.loc["Rural", "killed"]),
        "rural_leth": area.loc["Rural", "lethality"], "urban_leth": area.loc["Urban", "lethality"],
        "vma80_acc_share": share(len(vma80), "accidents"), "vma80_killed_share": share(vma80["n_killed"].sum()),
        "single_vehicle_share": share(m.loc[m["single_vehicle"], "n_killed"].sum()),
        "obstacle_share": share(m.loc[m["hit_fixed_obstacle"], "n_killed"].sum()),
        "tree_share": share(m.loc[m["hit_tree"], "n_killed"].sum()),
        "unlit_acc_share": share(light.loc["Night – unlit", "accidents"], "accidents"),
        "unlit_killed_share": share(light.loc["Night – unlit", "killed"]),
        "night_ratio": (wk_night["n_killed"].sum() / len(wk_night)) / (wd_day["n_killed"].sum() / len(wd_day)),
        "car_share": share((k["mode"] == "Car").sum()),
        "per1000": 1000 * k.groupby("mode", observed=True).size() / involved,
        "men_share": 100 * k["sexe"].eq(1).sum() / len(k),
        "age_18_24": (k["age_band"] == "18–24").sum() / len(K.YEARS), "age_75": len(old) / len(K.YEARS),
        "ped75_share": 100 * (old["mode"] == "Pedestrian").sum() / (k["mode"] == "Pedestrian").sum(),
        "edp_2020": int(edp.get(2020, 0)), "edp_2024": int(edp.get(2024, 0)),
    }
