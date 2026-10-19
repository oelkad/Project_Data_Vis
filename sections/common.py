"""Small helpers shared by the story sections."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils import constants as K
from utils.filters import Filters, get_data
from utils.metrics import summarize, totals


def current_filters() -> Filters:
    return st.session_state["filters"]


def headline(text: str) -> None:
    """One-sentence headline insight at the top of a section."""
    st.markdown(f"<p style='font-size:1.25rem;line-height:1.45;margin:0.2rem 0 1rem 0'>{text}</p>",
                unsafe_allow_html=True)


def scope_note(f: Filters) -> None:
    st.caption(f"Current selection: **{f.describe()}**")


def empty_guard(acc: pd.DataFrame) -> bool:
    if acc.empty:
        st.warning("No accident matches the current filters. Widen the selection in the sidebar "
                   "(or press **Reset filters**).")
        return True
    return False


@st.cache_data(show_spinner=False)
def national_reference() -> dict:
    """Fixed reference numbers for metropolitan France 2020–2024 (ignore filters).

    Used by the narrative text and the conclusions so the key messages do not
    change when the reader plays with the filters.
    """
    data = get_data()
    acc, users = data["accidents"], data["users"]
    m = acc[acc["territory"] == "Metropolitan France"]
    um = users[users["acc_id"].isin(m["acc_id"])]
    by_year = summarize(m, "year")
    by_area = summarize(m, "area").set_index("area")
    total = totals(m)
    killed_mode = um[um["killed"]].groupby("mode", observed=True).size()
    involved_mode = um.groupby("mode", observed=True).size()
    per1000 = (1000 * killed_mode / involved_mode).dropna()
    light = summarize(m, "light_group").set_index("light_group")
    wk_night = m[m["weekend"] & (m["hour"] < 6)]
    wd_day = m[(~m["weekend"]) & m["hour"].between(7, 19)]
    vma = summarize(m, "vma").set_index("vma")
    edp = um[um["killed"] & (um["mode"] == "E-scooter (EDP)")].groupby("year").size()
    k = um[um["killed"]]
    age = k.groupby("age_band", observed=True).size()
    ped75 = int(((k["mode"] == "Pedestrian") & (k["age_band"] == "75+")).sum())
    ped = int((k["mode"] == "Pedestrian").sum())
    single = int(m.loc[m["single_vehicle"] & (m["n_ped"] == 0), "n_killed"].sum())
    obstacle = int(m.loc[m["hit_fixed_obstacle"], "n_killed"].sum())
    tree = int(m.loc[m["hit_tree"], "n_killed"].sum())
    return {
        "by_year": by_year,
        "killed_2024": int(by_year.loc[by_year.year == 2024, "killed"].iloc[0]),
        "killed_total": int(total["killed"]),
        "acc_total": int(total["accidents"]),
        "lethality": float(total["lethality"]),
        "rural_acc_share": 100 * by_area.loc["Rural", "accidents"] / total["accidents"],
        "rural_killed_share": 100 * by_area.loc["Rural", "killed"] / total["killed"],
        "rural_leth": float(by_area.loc["Rural", "lethality"]),
        "urban_leth": float(by_area.loc["Urban", "lethality"]),
        "car_share": 100 * killed_mode.get("Car", 0) / killed_mode.sum(),
        "per1000": per1000,
        "men_share": 100 * float(k["sexe"].eq(1).sum()) / len(k),
        "age_18_24": float(age.get("18–24", 0)) / len(K.YEARS),
        "age_75": float(age.get("75+", 0)) / len(K.YEARS),
        "ped75_share": 100 * ped75 / ped if ped else 0.0,
        "unlit_acc_share": 100 * light.loc["Night – unlit", "accidents"] / total["accidents"],
        "unlit_killed_share": 100 * light.loc["Night – unlit", "killed"] / total["killed"],
        "unlit_leth": float(light.loc["Night – unlit", "lethality"]),
        "wk_night_leth": 100 * wk_night["n_killed"].sum() / len(wk_night),
        "wd_day_leth": 100 * wd_day["n_killed"].sum() / len(wd_day),
        "vma80_killed_share": 100 * vma.loc[80, "killed"] / total["killed"],
        "vma80_acc_share": 100 * vma.loc[80, "accidents"] / total["accidents"],
        "vma80_leth": float(vma.loc[80, "lethality"]),
        "edp_2020": int(edp.get(2020, 0)), "edp_2024": int(edp.get(2024, 0)),
        "single_vehicle_share": 100 * single / total["killed"],
        "obstacle_share": 100 * obstacle / total["killed"],
        "tree_share": 100 * tree / total["killed"],
    }
