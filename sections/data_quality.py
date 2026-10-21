"""Data quality, cleaning log, limitations and method."""

import pandas as pd
import streamlit as st

from sections.common import headline
from utils import constants as K
from utils.filters import get_data


def render() -> None:
    q = get_data()["quality"]
    checks = pd.DataFrame(q["checks"])
    st.title("Data quality & method")
    headline("The cleaned data reproduce the official death toll <b>exactly</b>. But the file is a police record, "
             "not a census of every crash — read the limitations below.")
    c = st.columns(3)
    c[0].metric("Raw rows read (20 files)", f"{q['n_raw_rows']:,}", border=True)
    c[1].metric("Accidents · people after cleaning", f"{q['n_accidents']:,} · {q['n_users']:,}", border=True)
    c[2].metric("Checks passed", f"{checks['status'].str.contains('pass').sum()} / {len(checks)}", border=True)

    st.subheader("1. Source")
    st.markdown(
        f"[{K.DATASET_TITLE}]({K.DATASET_PAGE}) — ONISR, Ministère de l'Intérieur, on data.gouv.fr, Licence Ouverte "
        "v2.0. The police or gendarmerie fill in a form (BAAC) for every injury accident on a public road; deaths "
        "are counted up to 30 days after. Years 2020–2024: 4 tables per year (accidents, locations, vehicles, "
        "people) joined on the accident ID.")

    st.subheader("2. Validation checks")
    st.table(checks.set_index("check"))

    st.subheader("3. Cleaning and features")
    st.table(pd.DataFrame(q["cleaning_log"]).set_index("step"))
    st.markdown("**Features built for the story:** lethality (killed per 100 accidents), urban/rural, 8 road-user "
                "groups, age bands, night, lighting, weekend, single-vehicle crash, fixed-obstacle crash, region.")

    st.subheader("4. Limitations")
    st.markdown(
        "1. **Slight injuries are under-reported** (only accidents attended by the police are recorded), so "
        "lethality is an upper bound. Deaths are almost all recorded.\n"
        "2. **'Hospitalised' is no longer an official statistic** since 2019: shown, but never used for a "
        "conclusion.\n"
        "3. **No traffic volumes**: rates are per accident or per person involved, not per km travelled.\n"
        "4. **2020 is not a normal year** (three lockdowns).\n"
        "5. **Correlation is not causation**: rural roads, night and 80 km/h roads overlap heavily.\n"
        "6. **Privacy**: the source already removes personal details; the app only shows aggregates and accident "
        "locations on public roads.")

    st.subheader("5. Reproducibility")
    st.markdown("`python -m scripts.build_data` downloads the 20 files from data.gouv.fr (cached in `data/raw/`) and "
                "rebuilds `data/processed/` with every step above. Library versions are pinned in "
                "`requirements.txt`.")
