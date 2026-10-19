"""Invariants of the processed tables (run after scripts/build_data.py)."""

import pandas as pd
import pytest

from utils import constants as K
from utils.io import load_processed


@pytest.fixture(scope="module")
def data():
    return load_processed()


def test_accident_key_unique(data):
    assert data["accidents"]["acc_id"].is_unique


def test_every_person_belongs_to_an_accident(data):
    assert data["users"]["acc_id"].isin(data["accidents"]["acc_id"]).all()


def test_years_and_dates(data):
    acc = data["accidents"]
    assert set(acc["year"].unique()) == set(K.YEARS)
    assert acc["date"].notna().all()
    assert (acc["date"].dt.year == acc["year"]).all()


def test_killed_matches_official_totals(data):
    users = data["users"]
    for year, official in K.ONISR_TOTAL_KILLED.items():
        assert int(users.loc[users["year"] == year, "killed"].sum()) == official


def test_accident_level_counts_consistent(data):
    acc, users = data["accidents"], data["users"]
    assert int(acc["n_killed"].sum()) == int(users["killed"].sum())
    assert (acc["fatal"] == (acc["n_killed"] > 0)).all()


def test_speed_limits_valid(data):
    vma = data["accidents"]["vma"].dropna()
    assert vma.isin(K.VALID_VMA).all()


def test_modes_known(data):
    assert set(data["users"]["mode"].dropna().unique()) <= set(K.MODE_ORDER)
    assert data["users"]["mode"].notna().all()


def test_age_range(data):
    age = data["users"]["age"].dropna()
    assert age.between(0, 105).all()


def test_metropolitan_coordinates_inside_france(data):
    acc = data["accidents"]
    m = acc[(acc["territory"] == "Metropolitan France") & acc["geo_ok"]]
    lat0, lat1, lon0, lon1 = K.METRO_BBOX
    assert m["lat"].between(lat0, lat1).all() and m["lon"].between(lon0, lon1).all()
