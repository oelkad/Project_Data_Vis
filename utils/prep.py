"""Cleaning, validation and feature engineering.

raw CSVs (4 tables x 5 years) -> clean and join -> accidents.parquet (1 row per accident),
users.parquet (1 row per person) and quality.json (checks + cleaning log, shown in the app).
"""

import json

import numpy as np
import pandas as pd

from utils import constants as K
from utils.io import PROCESSED_DIR, load_geojson, read_raw


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def code(s: pd.Series) -> pd.Series:
    """Numeric code where -1 ('not filled') becomes missing."""
    out = num(s)
    return out.where(out != -1).astype("Int16")


def load_all_raw() -> dict[str, pd.DataFrame]:
    """The 4 tables, each with the 5 years stacked."""
    return {t: pd.concat([read_raw(y, t) for y in K.YEARS], ignore_index=True) for t in K.TABLES}


def clean_accidents(c: pd.DataFrame, geo: dict, log: list) -> pd.DataFrame:
    out = pd.DataFrame({"acc_id": num(c["Num_Acc"]).astype("int64"), "year": num(c["an"]).astype("int16"),
                        "month": num(c["mois"]).astype("int8"), "day": num(c["jour"]).astype("int8")})
    out["date"] = pd.to_datetime(out[["year", "month", "day"]])
    out["hour"] = num(c["hrmn"].str[:2]).astype("Int8")
    out["weekday"] = out["date"].dt.weekday
    for col in ["lum", "agg", "int", "col"]:
        out[col] = code(c[col])
    out["dep"] = c["dep"].str.upper().str.zfill(2)
    out["lat"] = num(c["lat"].str.replace(",", "."))
    out["lon"] = num(c["long"].str.replace(",", "."))

    names = {f["properties"]["code"]: f["properties"]["nom"] for f in geo["features"]} | K.OVERSEAS_NAMES
    out["dep_name"] = out["dep"].map(names).fillna(out["dep"])
    out["region"] = out["dep"].map(K.DEP_TO_REGION).fillna("Unknown")
    overseas = out["dep"].isin(K.OVERSEAS_DEPS)
    out["territory"] = np.where(overseas, "Overseas", "Metropolitan France")

    # GPS check: point inside the bounding box of its territory
    box = pd.DataFrame(out["dep"].map(lambda d: K.OVERSEAS_BBOX.get(d, K.METRO_BBOX)).tolist(), index=out.index)
    out["geo_ok"] = out["lat"].between(box[0], box[1]) & out["lon"].between(box[2], box[3])
    log.append({"step": "Dates, hours, GPS", "rows": int((~out["geo_ok"]).sum()),
                "action": "Date built from jour/mois/an; hour from hrmn; decimal commas in GPS fixed. Points outside "
                          "their territory are only left out of the point map."})
    return out


def clean_locations(l: pd.DataFrame, log: list) -> pd.DataFrame:
    l = l.assign(acc_id=num(l["Num_Acc"]).astype("int64"))
    n_rows = len(l)
    l = l.drop_duplicates("acc_id")  # since 2023 one row per road of an intersection: keep the main road
    vma = num(l["vma"]).replace(K.VMA_TYPO_FIX)
    log.append({"step": "Locations", "rows": n_rows - len(l),
                "action": "Several roads listed for one accident (since 2023): main road kept, so accidents are "
                          "not double-counted. Speed limits: typos fixed (500→50…), impossible values set to missing."})
    return pd.DataFrame({"acc_id": l["acc_id"], "catr": code(l["catr"]),
                         "vma": vma.where(vma.isin(K.VALID_VMA)).astype("Int16")})


def clean_vehicles(v: pd.DataFrame) -> pd.DataFrame:
    catv = num(v["catv"])
    return pd.DataFrame({"acc_id": num(v["Num_Acc"]).astype("int64"), "id_vehicule": v["id_vehicule"],
                         "mode": catv.map(K.CATV_TO_MODE).fillna("Other"), "obs": code(v["obs"])})


def clean_users(u: pd.DataFrame, veh: pd.DataFrame, log: list) -> pd.DataFrame:
    u = u.assign(acc_id=num(u["Num_Acc"]).astype("int64"))
    u = u.merge(veh[["acc_id", "id_vehicule", "mode"]], on=["acc_id", "id_vehicule"], how="left",
                validate="many_to_one")
    year = num(u["Num_Acc"].str[:4])
    age = year - num(u["an_nais"])
    out = pd.DataFrame({"acc_id": u["acc_id"], "year": year.astype("int16"), "grav": code(u["grav"]),
                        "sexe": code(u["sexe"]), "age": age.where(age.between(0, 105))})
    out["age_band"] = pd.cut(out["age"], bins=K.AGE_BINS, labels=K.AGE_LABELS, right=False)
    # pedestrians are attached to the vehicle that hit them, so their mode comes from catu = 3
    mode = np.where(num(u["catu"]) == 3, "Pedestrian", u["mode"].fillna("Other"))
    out["mode"] = pd.Categorical(mode, categories=K.MODE_ORDER)
    out["killed"] = out["grav"].eq(2).fillna(False).astype(bool)
    log.append({"step": "People", "rows": int(out["grav"].isna().sum()),
                "action": "Age = year − birth year (impossible ages removed). People who fled (since 2021) have no "
                          "injury severity: kept, but not counted as victims. 31 vehicle codes grouped into 8 modes."})
    return out.drop(columns="age")


def build_accidents(car: pd.DataFrame, loc: pd.DataFrame, veh: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    acc = car.merge(loc, on="acc_id", how="left", validate="one_to_one")
    # per-accident flags and counts from the vehicles and people tables
    v = veh.assign(has_moto=veh["mode"].eq("Motorcycle >50cc"),
                   hit_tree=veh["obs"].eq(K.OBS_TREE).fillna(False).astype(bool),
                   hit_fixed_obstacle=veh["obs"].between(1, 17).fillna(False).astype(bool))
    vagg = v.groupby("acc_id").agg(has_moto=("has_moto", "any"), hit_tree=("hit_tree", "any"),
                                   hit_fixed_obstacle=("hit_fixed_obstacle", "any"), n_veh=("mode", "size"))
    p = users.assign(n_killed=users["killed"].astype(int), n_hosp=users["grav"].eq(3).fillna(False).astype(int),
                     n_ped=users["mode"].eq("Pedestrian").astype(int))
    uagg = p.groupby("acc_id")[["n_killed", "n_hosp", "n_ped"]].sum()
    acc = acc.join(vagg, on="acc_id").join(uagg, on="acc_id")
    acc[["n_killed", "n_hosp", "n_ped"]] = acc[["n_killed", "n_hosp", "n_ped"]].fillna(0).astype("int32")

    # engineered features
    acc["single_vehicle"] = (acc["n_veh"] == 1) & (acc["n_ped"] == 0)  # one vehicle, nobody else involved
    acc["fatal"] = acc["n_killed"] > 0
    acc["area"] = acc["agg"].map({1: "Rural", 2: "Urban"}).fillna("Unknown")
    acc["night"] = acc["lum"].isin([3, 4, 5]).astype(bool)
    acc["light_group"] = acc["lum"].map(K.LUM_GROUP).fillna("Unknown")
    acc["weekend"] = acc["weekday"] >= 5
    acc["ym"] = acc["date"].dt.to_period("M").dt.to_timestamp()
    for col in ["dep", "dep_name", "region", "territory", "area", "light_group"]:
        acc[col] = acc[col].astype("category")
    return acc.drop(columns=["agg", "n_veh"])


def validation_checks(raw: dict, acc: pd.DataFrame, users: pd.DataFrame) -> list[dict]:
    checks = []

    def add(name, value, ok, detail):
        checks.append({"check": name, "value": value, "status": "✅ pass" if ok else "⚠️ warning", "detail": detail})

    dup = int(raw["caract"]["Num_Acc"].duplicated().sum())
    add("Accident ID unique", dup, dup == 0, "Num_Acc is unique in the accidents table.")
    orphans = sum(int((~num(raw[t]["Num_Acc"]).isin(acc["acc_id"])).sum()) for t in ["lieux", "vehicules", "usagers"])
    add("Every row links to an accident", orphans, orphans == 0,
        "Rows of the locations, vehicles and people tables whose accident does not exist.")
    empty = sum(int((~acc["acc_id"].isin(num(raw[t]["Num_Acc"]))).sum()) for t in ["vehicules", "usagers"])
    add("Every accident has a vehicle and a person", empty, empty == 0, "Accidents with no vehicle or nobody recorded.")
    for table, col, valid in [("caract", "lum", range(1, 6)), ("caract", "col", range(1, 8)),
                              ("usagers", "grav", range(1, 5)), ("usagers", "catu", range(1, 4))]:
        v = num(raw[table][col])
        bad = int((~v.isin(list(valid)) & (v != -1)).sum())
        add(f"Codes of {table}.{col}", bad, bad == 0, "Values outside the codebook list.")
    bad_geo = int((~acc["geo_ok"]).sum())
    add("GPS point inside its territory", f"{100 * acc['geo_ok'].mean():.2f}%", bad_geo == 0,
        f"{bad_geo} accidents left out of the point map only.")
    for year, official in K.ONISR_TOTAL_KILLED.items():
        ours = int(users.loc[users["year"] == year, "killed"].sum())
        add(f"Deaths {year} vs official ONISR figure", f"{ours:,} vs {official:,}", ours == official,
            "People killed (France incl. overseas) in the cleaned data vs the official annual report.")
    return checks


def build_all() -> dict:
    raw = load_all_raw()
    log = [{"step": "Schema", "rows": int(raw["caract"].shape[0]),
            "action": "Key 'Accident_Id' (2022) renamed 'Num_Acc'; spaces stripped; values read as text, then typed."}]
    car = clean_accidents(raw["caract"], load_geojson(), log)
    loc = clean_locations(raw["lieux"], log)
    veh = clean_vehicles(raw["vehicules"])
    users = clean_users(raw["usagers"], veh, log)
    acc = build_accidents(car, loc, veh, users)
    quality = {"n_accidents": len(acc), "n_users": len(users),
               "n_raw_rows": int(sum(len(df) for df in raw.values())),
               "cleaning_log": log, "checks": validation_checks(raw, acc, users)}

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    acc.to_parquet(PROCESSED_DIR / "accidents.parquet", index=False, compression="zstd")
    users.to_parquet(PROCESSED_DIR / "users.parquet", index=False, compression="zstd")
    (PROCESSED_DIR / "quality.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
    return quality
