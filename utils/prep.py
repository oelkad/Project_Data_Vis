"""Cleaning, validation and feature engineering for the BAAC files.

Pipeline (run by ``scripts/build_data.py`` or automatically on a clean checkout):

    raw CSVs (4 tables x 5 years, text)
        -> profile raw quality (missingness, duplicates, keys)
        -> harmonise schemas (Accident_Id, spaces, decimal commas, code formats)
        -> clean & validate (dates, hours, GPS, speed limits, ages, codes)
        -> join the 4 tables and engineer features
        -> accidents.parquet (1 row / accident), users.parquet (1 row / person)
        -> quality.json + missingness.parquet (shown in the Data-quality section)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from utils import constants as K
from utils.io import PROCESSED_DIR, PROCESSED_FILES, load_geojson, load_raw_all, raw_path

log = logging.getLogger(__name__)

MISSING_TOKENS = {"", "-1", ".", "N/A", "NaN", "nan"}

# Valid code domains (codebook) used by the domain checks
DOMAINS = {
    ("caract", "lum"): set(range(1, 6)),
    ("caract", "agg"): {1, 2},
    ("caract", "int"): set(range(1, 10)),
    ("caract", "atm"): set(range(1, 10)),
    ("caract", "col"): set(range(1, 8)),
    ("lieux", "catr"): {1, 2, 3, 4, 5, 6, 7, 9},
    ("lieux", "surf"): set(range(1, 10)),
    ("vehicules", "catv"): {0, 1, 2, 3, 7, 10, 13, 14, 15, 16, 17, 20, 21, 30, 31, 32, 33, 34, 35, 36,
                            37, 38, 39, 40, 41, 42, 43, 50, 60, 80, 99},
    ("usagers", "catu"): {1, 2, 3},
    ("usagers", "grav"): {1, 2, 3, 4},
    ("usagers", "sexe"): {1, 2},
}


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _code(s: pd.Series) -> pd.Series:
    """Numeric code with the 'not filled' value -1 turned into NA."""
    out = _num(s)
    return out.where(out != -1).astype("Int16")


def _concat(raw_tables: dict[int, pd.DataFrame]) -> pd.DataFrame:
    frames = []
    for year, df in raw_tables.items():
        d = df.copy()
        d["file_year"] = year
        frames.append(d)
    return pd.concat(frames, ignore_index=True, sort=False)


# ---------------------------------------------------------------------------
# 1. Raw-data profiling
# ---------------------------------------------------------------------------
def profile_missingness(raw: dict) -> pd.DataFrame:
    rows = []
    for table, by_year in raw.items():
        for year, df in by_year.items():
            n = len(df)
            for col in df.columns:
                if col in {"Num_Acc"}:
                    continue
                miss = df[col].isin(MISSING_TOKENS).sum()
                rows.append({"table": table, "year": year, "column": col, "rows": n,
                             "missing": int(miss), "pct_missing": 100 * miss / n if n else np.nan})
    return pd.DataFrame(rows)


def file_integrity() -> list[dict]:
    out = []
    for year in K.YEARS:
        for table in K.TABLES:
            p = raw_path(year, table)
            rid, name, official = K.RESOURCES[year][table]
            if not p.exists():
                continue
            size = p.stat().st_size
            with open(p, "rb") as fh:
                data = fh.read()
            n_lines = data.count(b"\n")
            crlf = data.count(b"\r\n")
            # LF-only copy of a CRLF original differs by exactly one byte per line
            note = "identical size"
            if size != official:
                note = ("differs only by line endings (CRLF→LF)" if official - size == n_lines and crlf == 0
                        else "size differs from the published file")
            out.append({"year": year, "table": table, "official_file": name, "bytes": size,
                        "official_bytes": official, "check": note})
    return out


# ---------------------------------------------------------------------------
# 2. Accidents (caract + lieux + aggregated vehicles/users)
# ---------------------------------------------------------------------------
def _dep_bboxes(geo: dict, margin: float = 0.15) -> dict[str, tuple[float, float, float, float]]:
    boxes = {}
    for feat in geo["features"]:
        coords = []
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for ring in poly:
                coords.extend(ring)
        arr = np.asarray(coords)
        boxes[feat["properties"]["code"]] = (arr[:, 1].min() - margin, arr[:, 1].max() + margin,
                                             arr[:, 0].min() - margin, arr[:, 0].max() + margin)
    boxes.update(K.OVERSEAS_BBOX)
    return boxes


def dep_names(geo: dict) -> dict[str, str]:
    names = {f["properties"]["code"]: f["properties"]["nom"] for f in geo["features"]}
    names.update(K.OVERSEAS_NAMES)
    return names


def build_caract(raw_caract: dict, geo: dict, log_: list) -> pd.DataFrame:
    c = _concat(raw_caract)
    out = pd.DataFrame({"acc_id": _num(c["Num_Acc"]).astype("int64")})
    out["year"] = _num(c["an"]).astype("int16")
    out["month"] = _num(c["mois"]).astype("int8")  # '1' (2020) and '01' (2021+) both parse
    out["day"] = _num(c["jour"]).astype("int8")
    out["date"] = pd.to_datetime(dict(year=out.year, month=out.month, day=out.day), errors="coerce")
    hhmm = c["hrmn"].str.extract(r"^(\d{1,2}):(\d{2})$")
    out["hour"] = _num(hhmm[0]).astype("Int8")
    out["weekday"] = out["date"].dt.weekday.astype("int8")
    for col in ["lum", "agg", "int", "atm", "col"]:
        out[col] = _code(c[col])
    dep = c["dep"].str.upper()
    dep = dep.where(dep.str.len() != 1, dep.str.zfill(2))
    out["dep"] = dep
    out["com"] = c["com"]
    out["lat"] = _num(c["lat"].str.replace(",", ".", regex=False))
    out["lon"] = _num(c["long"].str.replace(",", ".", regex=False))

    names = dep_names(geo)
    out["dep_name"] = out["dep"].map(names).fillna(out["dep"])
    out["region"] = out["dep"].map(K.DEP_TO_REGION).fillna("Unknown")
    out["territory"] = np.where(out["dep"].isin(K.OVERSEAS_DEPS), "Overseas", "Metropolitan France")

    # GPS validation: point must fall in the bounding box of its own department
    boxes = _dep_bboxes(geo)
    b = out["dep"].map(boxes)
    ok = []
    for (lat, lon, box) in zip(out["lat"].to_numpy(), out["lon"].to_numpy(), b.to_numpy()):
        ok.append(isinstance(box, tuple) and box[0] <= lat <= box[1] and box[2] <= lon <= box[3])
    out["geo_ok"] = np.array(ok, dtype=bool)

    n_bad_date = int(out["date"].isna().sum())
    n_bad_hour = int((out["hour"].isna() | (out["hour"] > 23)).sum())
    log_.append({"step": "Dates & times", "rows": n_bad_date + n_bad_hour,
                 "action": f"Built a proper date from jour/mois/an (month coded '1' in 2020 vs '01' "
                           f"afterwards). Invalid dates: {n_bad_date}; invalid hrmn: {n_bad_hour}."})
    log_.append({"step": "GPS coordinates", "rows": int((~out.geo_ok).sum()),
                 "action": "Decimal commas converted to points. Points outside the bounding box of their "
                           "own department are flagged (geo_ok = False) and left out of the point map only; "
                           "they still count in every statistic (the department code is reliable)."})
    return out


def build_lieux(raw_lieux: dict, log_: list) -> pd.DataFrame:
    l = _concat(raw_lieux)
    l["acc_id"] = _num(l["Num_Acc"]).astype("int64")
    n_rows = l.groupby("acc_id").size()
    multi = int((n_rows > 1).sum())
    first = l.drop_duplicates("acc_id", keep="first").set_index("acc_id")
    out = pd.DataFrame(index=first.index)
    for col in ["catr", "circ", "prof", "plan", "surf", "infra", "situ", "vosp"]:
        out[col] = _code(first[col])
    out["n_roads"] = n_rows.reindex(out.index).astype("int32")

    vma_raw = _num(first["vma"])
    vma = vma_raw.replace(K.VMA_TYPO_FIX)
    fixed = int(vma_raw.isin(K.VMA_TYPO_FIX.keys()).sum())
    invalid = int((~vma.isin(K.VALID_VMA) & vma.notna() & (vma != -1)).sum())
    not_filled = int((vma == -1).sum())
    out["vma"] = vma.where(vma.isin(K.VALID_VMA)).astype("Int16")
    log_.append({"step": "Several road rows per accident", "rows": multi,
                 "action": "From 2023 the LIEUX file lists every road involved in an intersection "
                           "(70,860 rows for 54,822 accidents in 2023). We keep the first row (main road) "
                           "so the join stays one-to-one and accidents are not double-counted."})
    log_.append({"step": "Speed limit (vma)", "rows": fixed + invalid + not_filled,
                 "action": f"{fixed} values with an extra zero (500→50, 900→90…) corrected; "
                           f"{invalid} implausible values (1, 2, 5, 6 km/h…) and {not_filled} 'not filled' (-1) "
                           "set to missing."})
    return out.reset_index()


def build_vehicles(raw_veh: dict) -> pd.DataFrame:
    v = _concat(raw_veh)
    v["acc_id"] = _num(v["Num_Acc"]).astype("int64")
    v["catv"] = _num(v["catv"]).astype("Int16")
    v["obs"] = _code(v["obs"])
    v["veh_mode"] = v["catv"].map(K.CATV_TO_MODE).fillna("Other")
    v["id_vehicule"] = v["id_vehicule"]
    return v[["acc_id", "id_vehicule", "num_veh", "catv", "veh_mode", "obs", "file_year"]]


def build_users(raw_usr: dict, veh: pd.DataFrame, acc_year: pd.Series, log_: list) -> pd.DataFrame:
    u = _concat(raw_usr)
    u["acc_id"] = _num(u["Num_Acc"]).astype("int64")
    u = u.merge(veh[["acc_id", "id_vehicule", "catv", "veh_mode"]], on=["acc_id", "id_vehicule"],
                how="left", validate="many_to_one")
    out = pd.DataFrame({"acc_id": u["acc_id"]})
    out["year"] = u["file_year"].astype("int16")
    out["catu"] = _code(u["catu"]).astype("Int8")
    out["grav"] = _code(u["grav"]).astype("Int8")
    out["sexe"] = _code(u["sexe"]).astype("Int8")
    out["trajet"] = _code(u["trajet"]).where(lambda s: s != 0).astype("Int8")
    birth = _num(u["an_nais"])
    age = out["year"] - birth
    implausible = int(((age < 0) | (age > 105)).sum())
    out["age"] = age.where((age >= 0) & (age <= 105)).astype("Int16")
    out["age_band"] = pd.cut(out["age"].astype("float"), bins=K.AGE_BINS, labels=K.AGE_LABELS, right=False)
    # Feature: road-user mode. Pedestrians are attached to the vehicle that hit
    # them, so their mode comes from catu, not from catv.
    out["mode"] = np.where(out["catu"].eq(3).fillna(False), "Pedestrian", u["veh_mode"].fillna("Other"))
    out["mode"] = pd.Categorical(out["mode"], categories=K.MODE_ORDER)
    out["catv"] = u["catv"]
    secu = u[["secu1", "secu2", "secu3"]].apply(_num)
    out["belt"] = secu.eq(1).any(axis=1)
    out["helmet"] = secu.eq(2).any(axis=1)
    out["killed"] = out["grav"].eq(2).fillna(False)
    out["victim"] = out["grav"].isin([2, 3, 4]).fillna(False)

    log_.append({"step": "Age", "rows": int(out["age"].isna().sum()),
                 "action": f"Age = accident year − birth year. Missing birth year (mostly fleeing users "
                           f"added since 2021) or implausible age ({implausible} rows, <0 or >105) → missing."})
    log_.append({"step": "Injury severity unknown (grav = -1)", "rows": int(out["grav"].isna().sum()),
                 "action": "Users who fled the scene are recorded since 2021 without severity. "
                           "They are kept in the table but excluded from victim counts."})
    log_.append({"step": "Road-user mode (feature)", "rows": len(out),
                 "action": "31 vehicle codes (catv) grouped into 8 modes; pedestrians identified by catu = 3 "
                           "(they are attached to the vehicle that hit them)."})
    return out


def assemble_accidents(car: pd.DataFrame, lieux: pd.DataFrame, veh: pd.DataFrame,
                       users: pd.DataFrame) -> pd.DataFrame:
    acc = car.merge(lieux, on="acc_id", how="left", validate="one_to_one")

    vflags = pd.DataFrame({"acc_id": veh["acc_id"]})
    for mode, flag in [("Motorcycle >50cc", "has_moto"), ("Moped ≤50cc", "has_moped"),
                       ("Bicycle", "has_bike"), ("E-scooter (EDP)", "has_edp"),
                       ("Van / truck / bus", "has_heavy")]:
        vflags[flag] = veh["veh_mode"].eq(mode)
    vflags["hit_tree"] = veh["obs"].eq(K.OBS_TREE).fillna(False)
    vflags["hit_fixed_obstacle"] = veh["obs"].between(1, 17).fillna(False)
    vagg = vflags.groupby("acc_id").any()
    vagg["n_veh"] = veh.groupby("acc_id").size()

    ind = pd.DataFrame({
        "acc_id": users["acc_id"],
        "n_users": 1,
        "n_killed": users["grav"].eq(2).fillna(False).astype(int),
        "n_hosp": users["grav"].eq(3).fillna(False).astype(int),
        "n_light": users["grav"].eq(4).fillna(False).astype(int),
        "n_ped": users["catu"].eq(3).fillna(False).astype(int),
    })
    uagg = ind.groupby("acc_id").sum()
    acc = acc.merge(vagg, left_on="acc_id", right_index=True, how="left")
    acc = acc.merge(uagg, left_on="acc_id", right_index=True, how="left")
    for col in ["n_veh", "n_users", "n_killed", "n_hosp", "n_light", "n_ped"]:
        acc[col] = acc[col].fillna(0).astype("int32")
    for col in ["has_moto", "has_moped", "has_bike", "has_edp", "has_heavy", "hit_tree", "hit_fixed_obstacle"]:
        acc[col] = acc[col].fillna(False).astype(bool)

    # Engineered features
    acc["fatal"] = acc["n_killed"] > 0
    acc["severity"] = np.select([acc["fatal"], acc["n_hosp"] > 0], ["Fatal", "Serious"], "Slight")
    acc["area"] = acc["agg"].map(K.AGG_SHORT).fillna("Unknown")
    acc["night"] = acc["lum"].isin([3, 4, 5])
    acc["light_group"] = acc["lum"].map(K.LUM_GROUP).fillna("Unknown")
    acc["weekend"] = acc["weekday"] >= 5
    acc["single_vehicle"] = acc["n_veh"] == 1
    acc["ym"] = acc["date"].dt.to_period("M").dt.to_timestamp()

    cat_cols = ["dep", "dep_name", "region", "territory", "area", "light_group", "severity", "com"]
    for col in cat_cols:
        acc[col] = acc[col].astype("category")
    return acc


# ---------------------------------------------------------------------------
# 3. Validation checks
# ---------------------------------------------------------------------------
def validation_checks(raw: dict, acc: pd.DataFrame, users: pd.DataFrame, veh: pd.DataFrame) -> list[dict]:
    checks = []

    def add(name, value, status, detail):
        checks.append({"check": name, "value": value, "status": status, "detail": detail})

    dup_keys = sum(int(df["Num_Acc"].duplicated().sum()) for df in raw["caract"].values())
    add("Accident key unique in CARACT", dup_keys, "pass" if dup_keys == 0 else "fail",
        "Num_Acc (named Accident_Id in 2022) is unique within every yearly file.")

    caract_ids = set(acc["acc_id"])
    orphan = {t: int((~_num(pd.concat(raw[t].values())["Num_Acc"]).isin(caract_ids)).sum())
              for t in ["lieux", "vehicules", "usagers"]}
    add("Referential integrity (child → CARACT)", sum(orphan.values()),
        "pass" if sum(orphan.values()) == 0 else "fail",
        "Rows of LIEUX / VEHICULES / USAGERS whose accident does not exist: " +
        ", ".join(f"{k} {v}" for k, v in orphan.items()) + ".")

    no_user = int((acc["n_users"] == 0).sum())
    no_veh = int((acc["n_veh"] == 0).sum())
    add("Each accident has ≥1 vehicle and ≥1 person", no_user + no_veh,
        "pass" if no_user + no_veh == 0 else "warn", f"Accidents without person: {no_user}; without vehicle: {no_veh}.")

    unmatched = int(users["catv"].isna().sum())
    add("Person → vehicle link (Num_Acc + id_vehicule)", unmatched, "pass" if unmatched == 0 else "warn",
        "Every person is attached to a vehicle of the same accident (pedestrians to the vehicle that hit them).")

    veh_keys = veh[["acc_id", "id_vehicule"]].drop_duplicates()
    raw_u = pd.concat(raw["usagers"].values())
    u_keys = pd.DataFrame({"acc_id": _num(raw_u["Num_Acc"]).astype("int64"), "id_vehicule": raw_u["id_vehicule"]})
    vehicles_without_people = len(veh_keys.merge(u_keys.drop_duplicates(), how="left", indicator=True)
                                  .query("_merge == 'left_only'"))
    add("Vehicles with no person recorded", vehicles_without_people, "info",
        "Hit-and-run drivers that were not created in USAGERS (documented by ONISR).")

    dup_users_2020 = int(raw["usagers"][2020].duplicated().sum())
    add("Identical rows in USAGERS 2020", dup_users_2020, "warn",
        "2020 has no person identifier, so two passengers of the same car with the same sex and birth year "
        "look identical. They are plausible real people → kept (0.06 % of 2020 rows).")

    for (table, col), domain in DOMAINS.items():
        vals = _num(pd.concat(raw[table].values())[col])
        bad = int((~vals.isin(domain) & vals.notna() & (vals != -1)).sum())
        add(f"Code domain {table}.{col}", bad, "pass" if bad == 0 else "warn",
            f"Values outside the codebook list ({sorted(domain)[:6]}…).")

    bad_geo = int((~acc["geo_ok"]).sum())
    add("GPS point inside its department", f"{100 * acc['geo_ok'].mean():.2f} %", "warn" if bad_geo else "pass",
        f"{bad_geo:,} accidents ({100 * bad_geo / len(acc):.2f} %) have coordinates outside their department's "
        "bounding box → excluded from the point map only.")

    for year, official in K.ONISR_TOTAL_KILLED.items():
        ours = int(users.loc[users.year == year, "killed"].sum())
        add(f"Reconciliation with ONISR official deaths {year}", f"{ours:,} vs {official:,}",
            "pass" if ours == official else "warn",
            "Killed (France incl. overseas) in our cleaned table vs the official annual report.")
    return checks


# ---------------------------------------------------------------------------
# 4. Orchestration
# ---------------------------------------------------------------------------
def make_tables(raw: dict) -> dict:
    geo = load_geojson()
    cleaning_log: list[dict] = [{
        "step": "Schema harmonisation", "rows": len(raw["caract"][2022]),
        "action": "Key column 'Accident_Id' (2022 file) renamed 'Num_Acc'; surrounding spaces "
                  "stripped (values such as ' -1'); every value read as text, then typed explicitly."}]
    car = build_caract(raw["caract"], geo, cleaning_log)
    lieux = build_lieux(raw["lieux"], cleaning_log)
    veh = build_vehicles(raw["vehicules"])
    users = build_users(raw["usagers"], veh, car.set_index("acc_id")["year"], cleaning_log)
    acc = assemble_accidents(car, lieux, veh, users)
    checks = validation_checks(raw, acc, users, veh)
    missing = profile_missingness(raw)

    quality = {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "row_counts": {t: {str(y): len(df) for y, df in by_year.items()} for t, by_year in raw.items()},
        "n_accidents": int(len(acc)),
        "n_users": int(len(users)),
        "files": file_integrity(),
        "cleaning_log": cleaning_log,
        "checks": checks,
    }
    users_out = users.drop(columns=["catv"])
    return {"accidents": acc, "users": users_out, "missingness": missing, "quality": quality}


def save_tables(tables: dict) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    tables["accidents"].to_parquet(PROCESSED_FILES["accidents"], index=False, compression="zstd")
    tables["users"].to_parquet(PROCESSED_FILES["users"], index=False, compression="zstd")
    tables["missingness"].to_parquet(PROCESSED_FILES["missingness"], index=False)
    PROCESSED_FILES["quality"].write_text(json.dumps(tables["quality"], indent=2, ensure_ascii=False,
                                                     default=str), encoding="utf-8")


def build_all() -> dict:
    raw = load_raw_all()
    tables = make_tables(raw)
    save_tables(tables)
    return tables
