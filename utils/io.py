"""Download the raw files (with a local cache) and load the processed tables."""

import json
from pathlib import Path

import pandas as pd
import requests

from utils import constants as K

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
GEO_PATH = ROOT / "data" / "geo" / "departements.geojson"


def fetch(url: str, path: Path, force: bool = False) -> Path:
    """Download `url` to `path` unless it is already there."""
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return path


def read_raw(year: int, table: str, force: bool = False) -> pd.DataFrame:
    """One raw BAAC CSV, every value kept as text (codes like '2A' or ' -1' must not be converted)."""
    path = fetch(K.RESOURCE_URL.format(rid=K.RESOURCES[year][table]), RAW_DIR / str(year) / f"{table}-{year}.csv",
                 force)
    df = pd.read_csv(path, sep=";", dtype=str, keep_default_na=False)
    df = df.rename(columns={"Accident_Id": "Num_Acc"})  # the 2022 file uses another name for the key
    return df.apply(lambda col: col.str.strip())


def load_geojson() -> dict:
    return json.loads(fetch(K.GEOJSON_URL, GEO_PATH).read_text(encoding="utf-8"))


def load_processed() -> dict:
    """Analysis-ready tables used by the app (built by scripts/build_data.py, rebuilt here if missing)."""
    if not (PROCESSED_DIR / "accidents.parquet").exists():
        from utils.prep import build_all
        build_all()
    return {
        "accidents": pd.read_parquet(PROCESSED_DIR / "accidents.parquet"),
        "users": pd.read_parquet(PROCESSED_DIR / "users.parquet"),
        "quality": json.loads((PROCESSED_DIR / "quality.json").read_text(encoding="utf-8")),
    }
