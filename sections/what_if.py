"""4 · What-if: how much would each group have to improve to reach the EU 2030 goal?"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import headline
from utils import constants as K
from utils import viz
from utils.filters import get_data

SEGMENTS = {
    "Car occupants – rural roads": "s_car_rural",
    "Car occupants – towns": "s_car_urban",
    "Motorcyclists": "s_moto",
    "Pedestrians": "s_ped",
    "Cyclists & e-scooter riders": "s_bike",
    "Mopeds, vans, trucks & others": "s_other",
}
SHORT = {
    "Car occupants – rural roads": "Cars<br>rural", "Car occupants – towns": "Cars<br>towns",
    "Motorcyclists": "Motor-<br>cyclists", "Pedestrians": "Pedes-<br>trians",
    "Cyclists & e-scooter riders": "Bikes &<br>scooters", "Mopeds, vans, trucks & others": "Others",
}
PRESETS = {
    "Rural-roads plan": {"s_car_rural": 35, "s_moto": 20},
    "Vulnerable-users plan": {"s_ped": 30, "s_bike": 30, "s_moto": 25},
    "Both plans": {"s_car_rural": 35, "s_car_urban": 15, "s_moto": 30, "s_ped": 30, "s_bike": 30, "s_other": 15},
}


@st.cache_data(show_spinner=False)
def segment_baseline() -> pd.DataFrame:
    data = get_data()
    acc, users = data["accidents"], data["users"]
    m = acc[acc["territory"] == "Metropolitan France"][["acc_id", "area"]]
    k = users[users["killed"]].merge(m, on="acc_id")
    mode = k["mode"].astype(str)
    seg = pd.Series("Mopeds, vans, trucks & others", index=k.index)
    seg[(mode == "Car") & (k["area"] == "Rural")] = "Car occupants – rural roads"
    seg[(mode == "Car") & (k["area"] != "Rural")] = "Car occupants – towns"
    seg[mode == "Motorcycle >50cc"] = "Motorcyclists"
    seg[mode == "Pedestrian"] = "Pedestrians"
    seg[mode.isin(["Bicycle", "E-scooter (EDP)"])] = "Cyclists & e-scooter riders"
    k = k.assign(segment=seg)
    return k.groupby(["year", "segment"]).size().rename("killed").reset_index()


def _apply(preset: dict) -> None:
    for key in SEGMENTS.values():
        st.session_state[key] = preset.get(key, 0)


def render() -> None:
    st.title("What would it take to reach the 2030 goal?")
    goal = K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    seg = segment_baseline()

    base_choice = st.segmented_control("Baseline", ["2024", "Average 2022–2024"], default="2024",
                                       key="wi_base", required=True,
                                       help="Deaths per year in metropolitan France used as the starting point.")
    if base_choice == "2024":
        base = seg[seg["year"] == 2024].set_index("segment")["killed"]
    else:
        base = seg[seg["year"].between(2022, 2024)].groupby("segment")["killed"].mean()
    base = base.reindex(list(SEGMENTS)).fillna(0)
    total = float(base.sum())
    base_2024 = float(seg.loc[seg["year"] == 2024, "killed"].sum())
    needed = 100 * (total - goal) / total

    headline(f"To reach about <b>{goal:,.0f} deaths a year</b>, France must cut road deaths by "
             f"<b>{needed:.0f}%</b> from today's level. Move the sliders to test which combination of efforts "
             f"gets there.")

    st.caption("This page ignores the sidebar filters: the goal is national (metropolitan France). Deaths are split "
               "into six groups that do not overlap, so reductions add up exactly.")
    for key in SEGMENTS.values():
        st.session_state.setdefault(key, 0)
    p = st.columns(len(PRESETS) + 1)
    for i, (name, preset) in enumerate(PRESETS.items()):
        p[i].button(name, on_click=_apply, args=(preset,), width="stretch", key=f"preset_{i}")
    p[-1].button("Reset sliders", on_click=_apply, args=({},), width="stretch", key="preset_reset")

    left, right = st.columns([1, 1.6])
    saved = {}
    with left:
        st.markdown("**Reduction of deaths in each group (%)**")
        for name, key in SEGMENTS.items():
            share = 100 * base[name] / total if total else 0
            pct_red = st.slider(f"{name} — {base[name]:,.0f} deaths ({share:.0f}%)", 0, 60, step=5, key=key,
                                format="%d%%")
            saved[name] = base[name] * pct_red / 100
    scenario = total - sum(saved.values())
    with right:
        c1, c2, c3 = st.columns(3)
        lives = sum(saved.values())
        c1.metric("Scenario deaths / year", f"{scenario:,.0f}", f"{-lives:,.0f}" if lives else None,
                  delta_color="inverse", border=True)
        c2.metric("Lives saved / year", f"{lives:,.0f}", border=True)
        gap = scenario - goal
        c3.metric("Gap to 2030 goal", "Reached ✅" if gap <= 0 else f"{gap:,.0f}", border=True,
                  help="Deaths per year still above the EU 2030 goal.")
        items = [(SHORT[n], v) for n, v in saved.items() if v > 0]
        viz.show(viz.waterfall(f"Baseline<br>{base_choice.replace('Average ', 'avg ')}", total, items, goal),
                 alt=(f"Waterfall chart starting from {total:,.0f} deaths per year, subtracting the lives saved in "
                      f"each group ({', '.join(f'{n}: {v:,.0f}' for n, v in saved.items() if v > 0) or 'none yet'}), "
                      f"ending at "
                      f"{scenario:,.0f}. Dashed line: EU 2030 goal of about {goal:,.0f}."),
                 key="wi_waterfall")
        progress = min(1.0, (total - scenario) / max(total - goal, 1))
        st.progress(progress, text=f"{100 * progress:.0f}% of the reduction needed by 2030")

    st.markdown("##### Reading the result")
    rural_only = base["Car occupants – rural roads"] * 0.6
    st.markdown(
        f"- Even a **60% cut in rural car deaths** alone would save {rural_only:,.0f} lives a year — "
        f"{100 * rural_only / (total - goal):.0f}% of what is needed. No single group is big enough.\n"
        "- The goal is only reachable by acting on **rural roads *and* vulnerable users at the same time** "
        "(try *Both plans*).\n"
        f"- For scale: in 2024, deaths in metropolitan France were only "
        f"{100 * (1 - base_2024 / K.METRO_KILLED_2019):.1f}% below 2019 ({base_2024:,.0f} vs "
        f"{K.METRO_KILLED_2019:,}). Halving them in six years would be a sharp break with the trend, "
        "not a continuation.")
    with st.expander("Assumptions and limits of this simulation"):
        st.markdown(
            "- **Baseline**: deaths recorded in the BAAC file for metropolitan France (2024 = 3,193, identical to "
            "the official ONISR figure). Goal = 50% of the 2019 official figure (3,244), as in the EU road-safety "
            "framework 2021–2030.\n"
            "- **Groups** are mutually exclusive: car occupants are split by road environment; every other road "
            "user is counted once, whatever the road.\n"
            "- Reductions are **hypothetical inputs**, not forecasts: no traffic growth, no shift between modes, "
            "no interaction between measures.\n"
            "- The tool says *how much* each group would need to improve, not *how* — the levers (speed control, "
            "road design, lighting, protected bike lanes, enforcement at night) are discussed in the takeaways.")
    st.dataframe(pd.DataFrame({"group": list(SEGMENTS), "baseline deaths": base.round(0).values,
                               "reduction (%)": [st.session_state[k] for k in SEGMENTS.values()],
                               "lives saved": [round(saved[n]) for n in SEGMENTS]}),
                 hide_index=True, alt="Table of the six groups with baseline deaths, chosen reduction and lives saved.")
