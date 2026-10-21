"""Sidebar filters, cached data access and the aggregation used by every page."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from utils import constants as K
from utils.io import load_processed

TERRITORIES = ["Metropolitan France", "Overseas", "All of France"]
METRICS = {"People killed": "killed", "Lethality (killed per 100 accidents)": "lethality",
           "Injury accidents": "accidents"}


@dataclass(frozen=True)
class Filters:
    years: tuple[int, int]
    territory: str
    regions: tuple[str, ...]
    area: str
    metric_label: str

    @property
    def metric(self) -> str:
        return METRICS[self.metric_label]

    def describe(self) -> str:
        y0, y1 = self.years
        parts = [f"{y0}–{y1}" if y0 != y1 else str(y0), self.territory, *self.regions]
        if self.area != "All":
            parts.append(f"{self.area.lower()} roads")
        return " · ".join(parts)


@st.cache_data(show_spinner="Loading the accident database…")
def get_data() -> dict:
    return load_processed()


def sidebar_filters() -> Filters:
    st.sidebar.header("Filters")
    years = st.sidebar.select_slider("Years", options=K.YEARS, value=(K.YEARS[0], K.YEARS[-1]))
    territory = st.sidebar.radio("Territory", TERRITORIES)
    overseas = {"Metropolitan France": False, "Overseas": True}.get(territory)
    regions = [r for r, deps in K.REGION_DEPS.items() if overseas is None or (deps[0] in K.OVERSEAS_DEPS) == overseas]
    chosen = st.sidebar.multiselect("Region", regions, placeholder="All regions")
    area = st.sidebar.segmented_control("Road environment", ["All", "Urban", "Rural"], default="All", required=True,
                                        help="Urban = inside a built-up area; Rural = outside.")
    metric = st.sidebar.selectbox("Metric for the map and ranking", list(METRICS))
    return Filters(tuple(years), territory, tuple(chosen), area, metric)


@st.cache_data(show_spinner=False, max_entries=64)
def filtered(f: Filters, all_years: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Accidents and people matching the filters (every year if `all_years`)."""
    acc, users = get_data()["accidents"], get_data()["users"]
    mask = pd.Series(True, index=acc.index)
    if not all_years:
        mask &= acc["year"].between(*f.years)
    if f.territory != "All of France":
        mask &= acc["territory"] == f.territory
    if f.regions:
        mask &= acc["region"].isin(f.regions)
    if f.area != "All":
        mask &= acc["area"] == f.area
    acc = acc[mask]
    return acc, users[users["acc_id"].isin(acc["acc_id"])]


def summarize(acc: pd.DataFrame, by=None):
    """Accidents, killed, hospitalised and lethality (killed per 100 accidents), optionally per group."""
    if by is None:
        n, k = len(acc), int(acc["n_killed"].sum())
        return {"accidents": n, "killed": k, "hosp": int(acc["n_hosp"].sum()),
                "lethality": 100 * k / n if n else float("nan")}
    s = (acc.groupby(by, observed=True)
         .agg(accidents=("acc_id", "size"), killed=("n_killed", "sum"), hosp=("n_hosp", "sum")).reset_index())
    s["lethality"] = np.where(s["accidents"] > 0, 100 * s["killed"] / s["accidents"].clip(lower=1), np.nan)
    return s
