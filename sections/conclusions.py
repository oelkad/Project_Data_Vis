"""5 · Insights, implications and next steps."""

import streamlit as st

from sections.common import headline, national_reference
from utils import constants as K


def render() -> None:
    r = national_reference()
    p = r["per1000"]
    st.title("Takeaways")
    headline("Road deaths are no longer falling, and they are not spread evenly: <b>rural roads, the night and "
             "unprotected road users</b> concentrate the risk. That is where the next measures must go.")
    st.caption("Metropolitan France, 2020–2024, independent of the filters.")

    st.subheader("What the data say")
    left, right = st.columns(2)
    left.markdown(
        f"**1. The plateau.** About 3,200 deaths a year since 2021: {r['killed_2024']:,} in 2024, only "
        f"{100 * (1 - r['killed_2024'] / K.METRO_KILLED_2019):.1f}% below 2019. The EU goal needs half that.\n\n"
        f"**2. Rural roads.** {r['rural_acc_share']:.0f}% of accidents but **{r['rural_killed_share']:.0f}% of "
        f"deaths**; a rural accident is {r['rural_leth'] / r['urban_leth']:.1f}× as deadly. 80 km/h roads: "
        f"{r['vma80_acc_share']:.0f}% of accidents, **{r['vma80_killed_share']:.0f}% of deaths**. "
        f"**{r['single_vehicle_share']:.0f}%** of deaths come from a single vehicle crashing with nobody else "
        f"involved; {r['obstacle_share']:.0f}% involve a fixed obstacle (trees: {r['tree_share']:.0f}%).\n\n"
        f"**3. The night.** Unlit roads at night: {r['unlit_acc_share']:.0f}% of accidents, "
        f"**{r['unlit_killed_share']:.0f}% of deaths**. Weekend nights are {r['night_ratio']:.1f}× as deadly per "
        "accident as weekday daytime.")
    right.markdown(
        f"**4. Unprotected road users.** Car occupants are {r['car_share']:.0f}% of the dead, but per 1,000 people "
        f"involved, pedestrians ({p['Pedestrian']:.0f}), motorcyclists ({p['Motorcycle >50cc']:.0f}) and cyclists "
        f"({p['Bicycle']:.0f}) die about twice as often as car occupants ({p['Car']:.0f}).\n\n"
        f"**5. Two age peaks.** About {r['age_18_24']:.0f} deaths a year among 18–24-year-olds and "
        f"{r['age_75']:.0f} among the over-75s ({r['ped75_share']:.0f}% of pedestrians killed are 75+). "
        f"Men are {r['men_share']:.0f}% of the dead.\n\n"
        f"**6. A new risk.** E-scooter deaths: {r['edp_2020']} in 2020, {r['edp_2024']} in 2024.\n\n"
        "**7. Correlations.** Across departments, lethality goes with roadside obstacles, 80 km/h roads and unlit "
        "roads — rural factors that all go together.")

    st.subheader("So what? Where to act")
    st.markdown(
        "| Finding | Where to act | Possible levers |\n|---|---|---|\n"
        "| Rural accidents are 3–4× deadlier | Departmental two-way roads in high-lethality departments | Speed "
        "enforcement on the deadliest sections, forgiving roadsides (trees, ditches), overtaking lanes |\n"
        "| 4 deaths in 10: a single vehicle, nobody else | Rural bends, run-off-road hotspots | Bend signage, "
        "barriers adapted to motorcyclists |\n"
        "| Nights, weekend nights | Leisure routes at night | Alcohol & drug checks Fri–Sun nights, late transport |\n"
        "| Pedestrians aged 75+ | Urban crossings near shops and health services | Shorter crossings, 30 km/h zones, "
        "lighting |\n"
        "| Motorcyclists in summer, e-scooters | Scenic routes, dense cities | Seasonal campaigns, protective gear, "
        "protected lanes |")
    st.caption("The levers are standard road-safety measures listed for discussion; the data show where the risk is, "
               "not which measure works.")

    st.subheader("Limits and next steps")
    st.markdown(
        "- **Association, not causation**: rural, night, high-speed and single-vehicle factors overlap.\n"
        "- **No exposure data**: without traffic volumes we cannot compute a risk per km. Next step: add traffic "
        "counts and population (INSEE).\n"
        "- **Police-recorded data**: slight injuries are under-counted, so lethality is an upper bound.\n"
        "- **Next**: extend to 2005–2019 and fit a model of accident severity to separate the factors.")
    st.success("**To remember:** the gains are on rural roads, at night, and for people outside a car.")
