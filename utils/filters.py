"""Global sidebar filters and the cached filtering step.

The filters are drawn once in ``app.py`` (above every page) and stored in
``st.session_state`` so they persist while the reader moves through the story.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils import constants as K
from utils.io import load_processed
from utils.metrics import METRICS

TERRITORIES = ["Metropolitan France", "Overseas", "All of France"]
AREAS = ["All", "Urban", "Rural"]

DEFAULTS = {
    "f_years": (min(K.YEARS), max(K.YEARS)),
    "f_territory": "Metropolitan France",
    "f_regions": [],
    "f_deps": [],
    "f_area": "All",
    "f_modes": [],
    "f_metric": "People killed",
}


@dataclass(frozen=True)
class Filters:
    years: tuple[int, int]
    territory: str
    regions: tuple[str, ...]
    deps: tuple[str, ...]
    area: str
    modes: tuple[str, ...]
    metric_label: str

    @property
    def metric(self) -> str:
        return METRICS[self.metric_label]

    def key(self) -> tuple:
        return (self.years, self.territory, self.regions, self.deps, self.area, self.modes)

    def describe(self) -> str:
        parts = [f"{self.years[0]}–{self.years[1]}" if self.years[0] != self.years[1] else str(self.years[0]),
                 self.territory]
        if self.regions:
            parts.append(", ".join(self.regions) if len(self.regions) <= 2 else f"{len(self.regions)} regions")
        if self.deps:
            parts.append(f"{len(self.deps)} department(s)")
        if self.area != "All":
            parts.append(f"{self.area.lower()} roads")
        if self.modes:
            parts.append(", ".join(self.modes) if len(self.modes) <= 2 else f"{len(self.modes)} road-user types")
        return " · ".join(parts)

    @property
    def is_default_scope(self) -> bool:
        return not (self.regions or self.deps or self.modes or self.area != "All")


@st.cache_data(show_spinner="Loading the accident database…")
def get_data() -> dict:
    return load_processed()


def _reset() -> None:
    # Deleting the keys makes every widget start again from its default value.
    for k in DEFAULTS:
        st.session_state.pop(k, None)


def sidebar_filters() -> Filters:
    data = get_data()
    acc = data["accidents"]
    st.sidebar.header("Filters")
    st.sidebar.caption("Every chart and KPI follows these filters.")
    years = st.sidebar.select_slider("Years", options=K.YEARS, value=DEFAULTS["f_years"], key="f_years",
                                     help="Annual BAAC files 2020–2024. 2020 is distorted by COVID lockdowns.")
    territory = st.sidebar.radio("Territory", TERRITORIES, key="f_territory", horizontal=False,
                                 help="Overseas = 5 overseas departments + 6 overseas collectivities.")
    if territory == "All of France":
        region_opts = list(K.REGION_DEPS)
    else:
        region_opts = [r for r, ds in K.REGION_DEPS.items()
                       if (ds[0] in K.OVERSEAS_DEPS) == (territory == "Overseas")]
    if "f_regions" in st.session_state:
        st.session_state["f_regions"] = [r for r in st.session_state["f_regions"] if r in region_opts]
    regions = st.sidebar.multiselect("Region", region_opts, key="f_regions", placeholder="All regions")
    dep_pool = acc[["dep", "dep_name", "region", "territory"]].drop_duplicates()
    if territory != "All of France":
        dep_pool = dep_pool[dep_pool["territory"] == territory]
    if regions:
        dep_pool = dep_pool[dep_pool["region"].isin(regions)]
    dep_pool = dep_pool.sort_values("dep")
    dep_labels = {d: f"{d} – {n}" for d, n in zip(dep_pool["dep"], dep_pool["dep_name"])}
    if "f_deps" in st.session_state:
        st.session_state["f_deps"] = [d for d in st.session_state["f_deps"] if d in dep_labels]
    deps = st.sidebar.multiselect("Department", list(dep_labels), key="f_deps", placeholder="All departments",
                                  format_func=lambda d: dep_labels.get(d, d))
    area = st.sidebar.segmented_control("Road environment", AREAS, default=DEFAULTS["f_area"], key="f_area",
                                        required=True,
                                        help="Urban = inside a built-up area (agglomération); "
                                             "Rural = outside.")
    modes = st.sidebar.multiselect("Road users", K.MODE_ORDER, key="f_modes", placeholder="All road users",
                                   help="Keeps accidents involving at least one of these road users, and counts "
                                        "only their victims.")
    st.sidebar.divider()
    metric = st.sidebar.selectbox("Metric for maps & rankings", list(METRICS), key="f_metric",
                                  help="Lethality shows how deadly accidents are; counts show where the "
                                       "burden is largest.")
    st.sidebar.button("Reset filters", on_click=_reset, width="stretch")
    if isinstance(years, int):
        years = (years, years)
    return Filters(tuple(years), territory, tuple(regions), tuple(deps), area or "All", tuple(modes), metric)


@st.cache_data(show_spinner=False, max_entries=64)
def _filter(key: tuple, include_years: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    years, territory, regions, deps, area, modes = key
    data = get_data()
    acc, users = data["accidents"], data["users"]
    mask = pd.Series(True, index=acc.index)
    if include_years:
        mask &= acc["year"].between(years[0], years[1])
    if territory != "All of France":
        mask &= acc["territory"] == territory
    if regions:
        mask &= acc["region"].isin(regions)
    if deps:
        mask &= acc["dep"].isin(deps)
    if area != "All":
        mask &= acc["area"] == area
    a = acc[mask]
    u = users[users["acc_id"].isin(a["acc_id"])]
    if modes:
        u = u[u["mode"].isin(modes)]
        a = a[a["acc_id"].isin(u["acc_id"])].copy()
        # Count only the victims of the selected road users
        g = (u.assign(k=u["grav"].eq(2).fillna(False).astype(int), h=u["grav"].eq(3).fillna(False).astype(int),
                      l=u["grav"].eq(4).fillna(False).astype(int))
             .groupby("acc_id")[["k", "h", "l"]].sum())
        a["n_killed"] = a["acc_id"].map(g["k"]).fillna(0).astype("int32")
        a["n_hosp"] = a["acc_id"].map(g["h"]).fillna(0).astype("int32")
        a["n_light"] = a["acc_id"].map(g["l"]).fillna(0).astype("int32")
        a["fatal"] = a["n_killed"] > 0
    return a, u


def filtered(f: Filters) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Accidents and people matching every filter."""
    return _filter(f.key(), True)


def filtered_all_years(f: Filters) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Same filters but every year (used for deltas and long trends)."""
    return _filter(f.key(), False)
