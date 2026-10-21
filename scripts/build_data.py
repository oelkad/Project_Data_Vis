"""Download the 20 raw files from data.gouv.fr (cached in data/raw/) and rebuild data/processed/.

Usage, from the project root:  python -m scripts.build_data
To force a fresh download, delete the data/raw/ folder first.
"""

from utils.prep import build_all

if __name__ == "__main__":
    quality = build_all()
    print(f"Built {quality['n_accidents']:,} accidents and {quality['n_users']:,} people")
    for c in quality["checks"]:
        print(f"  {c['status']}  {c['check']}: {c['value']}")
