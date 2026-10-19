"""5 · Insights, implications and next steps."""

from __future__ import annotations

import streamlit as st

from sections.common import headline, national_reference
from utils import constants as K


def render() -> None:
    r = national_reference()
    goal = K.METRO_KILLED_2019 * K.EU_TARGET_FACTOR
    st.title("Takeaways")
    headline("Road deaths are no longer falling, and they are not spread evenly: <b>rural roads, the night, "
             "and unprotected road users</b> concentrate the risk. That is where the next life-saving measures "
             "must go.")
    st.caption("Figures below: metropolitan France, 2020–2024, all road users (independent of the sidebar).")

    st.subheader("What the data say")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"**1. The plateau.** After the 2020 lockdown dip, deaths settled around 3,200 a year: "
            f"{r['killed_2024']:,} in 2024, only {100 * (1 - r['killed_2024'] / K.METRO_KILLED_2019):.1f}% below 2019. "
            f"The EU goal (≈{goal:,.0f} by 2030) requires halving them.\n\n"
            f"**2. Rural roads.** {r['rural_acc_share']:.0f}% of accidents but **{r['rural_killed_share']:.0f}% of "
            f"deaths**. A rural accident is {r['rural_leth'] / r['urban_leth']:.1f}× as deadly as an urban one "
            f"({r['rural_leth']:.1f} vs {r['urban_leth']:.1f} killed per 100). 80 km/h roads alone: "
            f"{r['vma80_acc_share']:.0f}% of accidents, **{r['vma80_killed_share']:.0f}% of deaths**. "
            f"**{r['single_vehicle_share']:.0f}% of all deaths** happen when a single vehicle crashes with no one "
            f"else involved (loss of control, run-off-road); {r['obstacle_share']:.0f}% involve hitting a fixed "
            f"obstacle (trees alone: {r['tree_share']:.0f}%).\n\n"
            f"**3. The night.** Unlit roads at night: {r['unlit_acc_share']:.0f}% of accidents, "
            f"**{r['unlit_killed_share']:.0f}% of deaths**. Weekend nights are "
            f"{r['wk_night_leth'] / r['wd_day_leth']:.1f}× as deadly per accident as weekday daytime.")
    with c2:
        p = r["per1000"]
        st.markdown(
            f"**4. Unprotected road users.** Car occupants are {r['car_share']:.0f}% of the dead, but once involved in "
            f"an accident, pedestrians ({p.get('Pedestrian', 0):.0f}‰), motorcyclists "
            f"({p.get('Motorcycle >50cc', 0):.0f}‰) and cyclists ({p.get('Bicycle', 0):.0f}‰) die about twice as "
            f"often as car occupants ({p.get('Car', 0):.0f}‰).\n\n"
            f"**5. Two age peaks.** About {r['age_18_24']:.0f} deaths a year among 18–24-year-olds and "
            f"{r['age_75']:.0f} among the over-75s — {r['ped75_share']:.0f}% of all pedestrians killed are 75+. "
            f"Men are {r['men_share']:.0f}% of the dead.\n\n"
            f"**6. A new risk.** E-scooter deaths rose from {r['edp_2020']} (2020) to {r['edp_2024']} (2024). Small "
            f"numbers, fast growth.")

    st.subheader("So what? Implications for local decision-makers")
    st.markdown(
        "| Finding | Where to act | Possible levers |\n"
        "|---|---|---|\n"
        "| Rural accidents are 3–4× deadlier | Departmental two-way roads, high-lethality departments "
        "(map & ranking in section 3) | Speed enforcement on the deadliest sections, forgiving roadsides "
        "(obstacles, ditches, trees), rumble strips, overtaking lanes |\n"
        "| 4 deaths in 10: a single vehicle, nobody else involved | Rural bends and run-off-road hotspots | Bend signage, safety barriers "
        "suited to motorcyclists, rest areas against fatigue |\n"
        "| Nights and weekend nights | Leisure routes at night | Alcohol & drug checks Fri–Sun nights, late-night "
        "transport alternatives for young adults |\n"
        "| Pedestrians 75+ in towns | Urban crossings near shops, health services | Shorter crossings, longer "
        "green time, 30 km/h zones, lighting in winter evenings |\n"
        "| Motorcyclists, summer | Scenic and commuting routes, April–September | Seasonal campaigns, "
        "protective-gear incentives, training |\n"
        "| E-scooter growth | Dense urban areas | Monitoring, helmet campaigns, protected lanes |")
    st.caption("The levers are standard road-safety measures listed for discussion; this dataset shows where the "
               "risk is, it does not evaluate the measures.")

    st.subheader("Limits to keep in mind")
    st.markdown(
        "- **Association, not causation** — rural, night, high speed and single-vehicle factors overlap.\n"
        "- **No exposure data** — without vehicle-km we cannot say a group is 'riskier per trip'.\n"
        "- **Police-recorded data** — slight injuries are under-counted, so lethality is an upper bound.\n"
        "- **Five years** — enough to see a plateau, too short for long-run trends or policy evaluation.")

    st.subheader("Next steps")
    st.markdown(
        "1. Add **exposure** (traffic counts, vehicle-km by road type) to turn lethality into true risk rates.\n"
        "2. Add **population** by department (INSEE) for deaths per inhabitant.\n"
        "3. Extend to **2005–2019** with a harmonised schema to study long-run trends and the 2018 speed-limit "
        "change with a proper before/after design.\n"
        "4. Fit a **multivariate model** (e.g. logistic regression on accident severity) to separate the effects of "
        "road type, speed limit, lighting and road user.\n"
        "5. Publish a **hotspot list** of road sections with repeated fatal accidents for each department.")
    st.success("**One sentence to remember:** France will not halve road deaths by 2030 by doing the same things "
               "harder everywhere — the gains are on rural roads, at night, and for people outside a car.")
