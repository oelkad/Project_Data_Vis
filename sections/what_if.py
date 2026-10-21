"""4 · What-if: how much must each group of road users improve to reach the EU 2030 goal?"""

import pandas as pd
import streamlit as st

from sections.common import headline
from utils import constants as K
from utils import viz
from utils.filters import get_data

# 6 groups that do not overlap, so the lives saved add up (short name used on the chart)
GROUPS = {"Car occupants – rural roads": "Cars<br>rural", "Car occupants – towns": "Cars<br>towns",
          "Motorcyclists": "Motor-<br>cyclists", "Pedestrians": "Pedes-<br>trians",
          "Cyclists & e-scooter riders": "Bikes &<br>scooters", "Mopeds, vans, trucks & others": "Others"}
PRESETS = {"Rural-roads plan": {"Car occupants – rural roads": 35, "Motorcyclists": 20},
           "Vulnerable-users plan": {"Pedestrians": 30, "Cyclists & e-scooter riders": 30, "Motorcyclists": 25},
           "Both plans": {"Car occupants – rural roads": 35, "Car occupants – towns": 15, "Motorcyclists": 30,
                          "Pedestrians": 30, "Cyclists & e-scooter riders": 30, "Mopeds, vans, trucks & others": 15},
           "Reset": {}}


@st.cache_data(show_spinner=False)
def deaths_2024_by_group() -> pd.Series:
    acc, users = get_data()["accidents"], get_data()["users"]
    m = acc[(acc["territory"] == "Metropolitan France") & (acc["year"] == 2024)][["acc_id", "area"]]
    k = users[users["killed"]].merge(m, on="acc_id")
    mode = k["mode"].astype(str)
    group = pd.Series("Mopeds, vans, trucks & others", index=k.index)
    group[(mode == "Car") & (k["area"] == "Rural")] = "Car occupants – rural roads"
    group[(mode == "Car") & (k["area"] != "Rural")] = "Car occupants – towns"
    group[mode == "Motorcycle >50cc"] = "Motorcyclists"
    group[mode == "Pedestrian"] = "Pedestrians"
    group[mode.isin(["Bicycle", "E-scooter (EDP)"])] = "Cyclists & e-scooter riders"
    return group.value_counts().reindex(list(GROUPS), fill_value=0)


def apply_preset(preset: dict) -> None:
    for group in GROUPS:
        st.session_state[group] = preset.get(group, 0)


def render() -> None:
    st.title("What would it take to reach the 2030 goal?")
    base = deaths_2024_by_group()
    total = base.sum()
    goal = K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    headline(f"From {total:,} deaths in 2024 to about <b>{goal:,.0f}</b>: France must cut road deaths by "
             f"<b>{100 * (total - goal) / total:.0f}%</b>. Move the sliders to test which efforts get there.")
    st.caption("National figures (metropolitan France, 2024), independent of the filters.")

    for col, (name, preset) in zip(st.columns(len(PRESETS)), PRESETS.items()):
        col.button(name, on_click=apply_preset, args=(preset,), width="stretch")
    left, right = st.columns([1, 1.6])
    saved = {}
    with left:
        st.markdown("**Reduction of deaths in each group**")
        for group, deaths in base.items():
            cut = st.slider(f"{group} — {deaths:,} deaths ({100 * deaths / total:.0f}%)", 0, 60, step=5, key=group,
                            format="%d%%")
            saved[group] = deaths * cut / 100
    scenario = total - sum(saved.values())
    with right:
        c = st.columns(3)
        c[0].metric("Deaths per year", f"{scenario:,.0f}", border=True)
        c[1].metric("Lives saved per year", f"{total - scenario:,.0f}", border=True)
        c[2].metric("Gap to the 2030 goal", "Reached ✅" if scenario <= goal else f"{scenario - goal:,.0f}", border=True)
        items = [(GROUPS[g], v) for g, v in saved.items() if v > 0]
        viz.show(viz.waterfall("Deaths<br>2024", total, items, goal))
        st.progress(min(1.0, (total - scenario) / (total - goal)),
                    text=f"{100 * (total - scenario) / (total - goal):.0f}% of the reduction needed")

    st.markdown(
        f"- Even a **60% cut in rural car deaths** alone saves {0.6 * base.iloc[0]:,.0f} lives a year — not enough: "
        "no single group is big enough.\n"
        "- The goal is only reachable by acting on **rural roads *and* vulnerable users at the same time** "
        "(try *Both plans*).\n"
        "- Assumptions: reductions are hypothetical inputs, not forecasts (no traffic growth, no interaction "
        "between measures). The goal is 50% of the official 2019 figure (3,244).")
