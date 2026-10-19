"""Download the raw BAAC files (cached) and rebuild the processed tables.

Usage (from the project root):
    python -m scripts.build_data            # use cached raw files when present
    python -m scripts.build_data --refresh  # force a fresh download from data.gouv.fr
"""

from __future__ import annotations

import argparse
import logging
import time

from utils.constants import TABLES, YEARS
from utils.io import fetch_and_cache, fetch_geojson
from utils.prep import build_all


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-download raw files")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    t0 = time.time()
    for year in YEARS:
        for table in TABLES:
            fetch_and_cache(year, table, force=args.refresh)
    fetch_geojson(force=args.refresh)
    tables = build_all()
    q = tables["quality"]
    print(f"Built {q['n_accidents']:,} accidents and {q['n_users']:,} people in {time.time() - t0:.1f}s")
    for c in q["checks"]:
        print(f"  [{c['status']:>4}] {c['check']}: {c['value']}")


if __name__ == "__main__":
    main()
