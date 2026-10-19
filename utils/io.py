"""Data input/output: download with local cache, raw loading, processed loading.

The raw BAAC files are *not* bundled in the repository (≈150 MB). They are
downloaded once from data.gouv.fr into ``data/raw/<year>/`` and reused
afterwards. The app itself only reads the small processed Parquet files in
``data/processed/`` (built by ``scripts/build_data.py``).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from utils.constants import (
    DATASET_PAGE, DATASET_TITLE, GEOJSON_URL, LICENSE_NAME, LICENSE_URL, PRODUCER,
    RESOURCE_URL, RESOURCES, TABLES, YEARS,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
GEO_PATH = ROOT / "data" / "geo" / "departements.geojson"

PROCESSED_FILES = {
    "accidents": PROCESSED_DIR / "accidents.parquet",
    "users": PROCESSED_DIR / "users.parquet",
    "missingness": PROCESSED_DIR / "missingness.parquet",
    "quality": PROCESSED_DIR / "quality.json",
}


def raw_path(year: int, table: str) -> Path:
    return RAW_DIR / str(year) / f"{table}-{year}.csv"


def fetch_and_cache(year: int, table: str, force: bool = False, timeout: int = 120) -> Path:
    """Return the local path of one raw file, downloading it if needed."""
    import requests  # imported lazily: only needed when building from scratch

    path = raw_path(year, table)
    if path.exists() and not force:
        return path
    rid, official_name, official_size = RESOURCES[year][table]
    url = RESOURCE_URL.format(rid=rid)
    log.info("Downloading %s (%s) from %s", official_name, year, url)
    path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    tmp = path.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(path)
    size = path.stat().st_size
    if size != official_size:
        # Not fatal: data.gouv.fr occasionally republishes a file. We log it so
        # the data-quality report can mention it.
        log.warning("%s: %d bytes, official size %d", official_name, size, official_size)
    return path


def fetch_geojson(force: bool = False) -> Path:
    import requests

    if GEO_PATH.exists() and not force:
        return GEO_PATH
    GEO_PATH.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(GEOJSON_URL, timeout=60)
    resp.raise_for_status()
    GEO_PATH.write_bytes(resp.content)
    return GEO_PATH


def read_raw(year: int, table: str) -> pd.DataFrame:
    """Read one raw BAAC CSV as strings, exactly as published.

    * separator ``;``, UTF-8, every value quoted;
    * values kept as text (codes such as "2A" or " -1" must not be coerced);
    * surrounding spaces stripped (the files contain values like " -1");
    * the 2022 key column ``Accident_Id`` is renamed ``Num_Acc``.
    """
    path = fetch_and_cache(year, table)
    df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"Accident_Id": "Num_Acc"})
    for col in df.columns:
        df[col] = df[col].str.strip()
    return df


def load_raw_all(years: list[int] | None = None) -> dict[str, dict[int, pd.DataFrame]]:
    years = years or YEARS
    return {t: {y: read_raw(y, t) for y in years} for t in TABLES}


def processed_ready() -> bool:
    return all(p.exists() for p in PROCESSED_FILES.values())


def load_processed() -> dict:
    """Load the analysis-ready tables (fast path used by the app)."""
    if not processed_ready():
        # Clean checkout without processed files: rebuild them (downloads raw data).
        from utils.prep import build_all

        build_all()
    return {
        "accidents": pd.read_parquet(PROCESSED_FILES["accidents"]),
        "users": pd.read_parquet(PROCESSED_FILES["users"]),
        "missingness": pd.read_parquet(PROCESSED_FILES["missingness"]),
        "quality": json.loads(PROCESSED_FILES["quality"].read_text(encoding="utf-8")),
    }


def load_geojson() -> dict:
    return json.loads(fetch_geojson().read_text(encoding="utf-8"))


def license_text() -> str:
    return (
        f"**Data:** *{DATASET_TITLE}* – {PRODUCER}, published on "
        f"[data.gouv.fr]({DATASET_PAGE}) under the [{LICENSE_NAME}]({LICENSE_URL}). "
        "Department boundaries: IGN Admin Express via "
        "[france-geojson](https://github.com/gregoiredavid/france-geojson) (Licence Ouverte). "
        "Code: MIT licence."
    )
