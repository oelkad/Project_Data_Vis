"""Aggregations used across the app (group-bys on the filtered tables)."""

from __future__ import annotations

import numpy as np
import pandas as pd

METRICS = {
    "People killed": "killed",
    "Lethality (killed per 100 accidents)": "lethality",
    "Injury accidents": "accidents",
    "Killed or hospitalised": "ksi",
}
METRIC_HELP = {
    "killed": "People who died on the spot or within 30 days of the accident.",
    "lethality": "People killed for every 100 injury accidents: how deadly an accident is, once it happens.",
    "accidents": "Injury accidents recorded by the police or gendarmerie (at least one person needing care).",
    "ksi": "Killed + hospitalised more than 24 h. Caution: 'hospitalised' is no longer an official statistic since 2019.",
}
METRIC_UNITS = {"killed": "people killed", "lethality": "killed per 100 accidents",
                "accidents": "injury accidents", "ksi": "killed or hospitalised"}


def summarize(acc: pd.DataFrame, by: list[str] | str | None = None) -> pd.DataFrame:
    """Accidents, killed, hospitalised, KSI and lethality, optionally grouped."""
    cols = {"acc_id": "size", "n_killed": "sum", "n_hosp": "sum", "n_light": "sum"}
    if by is None:
        s = pd.DataFrame([{"accidents": len(acc), "killed": acc["n_killed"].sum(),
                           "hosp": acc["n_hosp"].sum(), "light": acc["n_light"].sum()}])
    else:
        s = (acc.groupby(by, observed=True).agg(cols)
             .rename(columns={"acc_id": "accidents", "n_killed": "killed", "n_hosp": "hosp",
                              "n_light": "light"}).reset_index())
    s[["accidents", "killed", "hosp", "light"]] = s[["accidents", "killed", "hosp", "light"]].astype("int64")
    s["ksi"] = s["killed"] + s["hosp"]
    s["lethality"] = np.where(s["accidents"] > 0, 100 * s["killed"] / s["accidents"].clip(lower=1), np.nan)
    return s


def totals(acc: pd.DataFrame) -> dict:
    """Same figures as ``summarize`` for the whole table, as plain Python numbers."""
    row = summarize(acc).iloc[0]
    out = {k: int(row[k]) for k in ["accidents", "killed", "hosp", "light", "ksi"]}
    out["lethality"] = float(row["lethality"])
    return out


def pct(a: float, b: float) -> float:
    return 100 * a / b if b else float("nan")


def fmt_int(x: float) -> str:
    return f"{x:,.0f}"


def fmt_pct(x: float, digits: int = 0) -> str:
    return f"{x:.{digits}f}%"
