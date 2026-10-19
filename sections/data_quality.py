"""Data quality, validation checks, cleaning log, caveats and ethics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from sections.common import current_filters, headline
from utils import constants as K
from utils import viz
from utils.filters import filtered, get_data
from utils.metrics import summarize

STATUS_ICON = {"pass": "✅ pass", "warn": "⚠️ warning", "fail": "❌ fail", "info": "ℹ️ info"}


def render() -> None:
    data = get_data()
    q = data["quality"]
    checks = pd.DataFrame(q["checks"])
    n_pass = int((checks["status"] == "pass").sum())
    st.title("Data quality & method")
    headline("The national picture is trustworthy: the cleaned data reproduce the official death toll "
             "<b>exactly</b>. But the file is a police record, not a census of every crash — read the caveats below.")

    c = st.columns(4)
    c[0].metric("Raw files (4 tables × 5 years)", f"{len(q['files'])}", border=True)
    rows = sum(sum(v.values()) for v in q["row_counts"].values())
    c[1].metric("Raw rows", f"{rows:,}", border=True)
    c[2].metric("Validation checks passed", f"{n_pass} / {len(checks)}", border=True,
                help="The rest are warnings that were handled (see table) or informational.")
    c[3].metric("Deaths 2023 & 2024 vs ONISR", "identical", border=True,
                help="3,398 and 3,432 killed (France incl. overseas), the official annual figures.")

    # ---------------- Source ----------------
    st.subheader("1. Source and integrity")
    st.markdown(
        f"- **Dataset:** [{K.DATASET_TITLE}]({K.DATASET_PAGE}) — producer {K.PRODUCER}; "
        f"licence [{K.LICENSE_NAME}]({K.LICENSE_URL}).\n"
        "- **Collection:** a form (BAAC) filled in by the police or gendarmerie unit that attends an injury accident "
        "on a road open to public traffic. Deaths are counted up to 30 days after the accident.\n"
        "- **Years used:** 2020–2024, the five years sharing the post-2019 schema (from 2019 the file format and "
        "several codes changed, so older years are not directly comparable).\n"
        "- **Integrity:** each downloaded file is compared with the byte size published by data.gouv.fr.")
    files = pd.DataFrame(q["files"])
    st.dataframe(files, hide_index=True, alt="Table of the 20 raw files with their size and the official size.",
                 column_config={"bytes": st.column_config.NumberColumn("bytes", format="%d"),
                                "official_bytes": st.column_config.NumberColumn("official bytes", format="%d")})

    # ---------------- Validation ----------------
    st.subheader("2. Validation checks")
    show = checks.assign(status=checks["status"].map(STATUS_ICON)).set_index("check")
    st.table(show)

    # ---------------- Cleaning log ----------------
    st.subheader("3. Cleaning and feature engineering")
    log = pd.DataFrame(q["cleaning_log"]).rename(columns={"rows": "rows concerned"}).set_index("step")
    log["rows concerned"] = log["rows concerned"].map(lambda v: f"{v:,}")
    st.table(log)
    st.markdown(
        "**Engineered features** used in the story: `lethality` (killed per 100 accidents), `area` (urban/rural), "
        "`mode` (8 road-user groups from 31 vehicle codes + pedestrians), `age` and `age_band`, `night`, "
        "`weekend`, `light_group`, `severity` (fatal / serious / slight), `single_vehicle`, `hit_tree`, "
        "presence flags (`has_moto`, `has_bike`, `has_edp`…), `region` and `territory`.")

    # ---------------- Missingness ----------------
    st.subheader("4. Missing values in the raw files")
    table = st.segmented_control("Table", ["caract", "lieux", "vehicules", "usagers"], default="usagers",
                                 key="dq_table", required=True,
                                 format_func=lambda t: {"caract": "Accidents", "lieux": "Locations",
                                                        "vehicules": "Vehicles", "usagers": "People"}[t])
    miss = data["missingness"]
    pv = miss[miss["table"] == table].pivot(index="column", columns="year", values="pct_missing")
    pv = pv.loc[pv.max(axis=1).sort_values(ascending=False).index]
    top = pv.max(axis=1).head(3)
    viz.show(viz.missing_heatmap(pv),
             alt=(f"Heatmap of the percentage of empty or 'not filled' (-1) values for each column of the {table} "
                  f"table and each year. Most columns are complete; the most incomplete are " +
                  ", ".join(f"{c} ({v:.0f}%)" for c, v in top.items()) + "."),
             key="dq_missing")
    st.caption("Counted as missing: empty cell, '-1', '.', 'N/A'. A blank cell means the column does not exist that "
               "year (id_usager starts in 2021). Many 'missing' values are structural: "
               "lartpc (central reserve width) only exists on divided roads, secu2/secu3 are second and third "
               "safety devices, v2 is a road-number suffix, occutc only applies to public transport.")

    # ---------------- Caveats ----------------
    st.subheader("5. Known biases and limitations")
    st.markdown(
        "1. **Under-reporting of light injuries.** Only accidents attended by the police are recorded. Many minor "
        "crashes — especially single-bicycle falls and urban scooter falls — never reach the file. Deaths are "
        "almost exhaustively recorded; slight injuries are not. Lethality is therefore over-estimated where minor "
        "accidents are less often reported.\n"
        "2. **'Hospitalised > 24 h' is no longer an official statistic** (not labelled since 2019, not comparable "
        "with years before 2018). We show it but never build a conclusion on it.\n"
        "3. **No exposure data.** The file has no traffic volumes (vehicle-km). Rates here are *per accident* or "
        "*per person involved*, not per km travelled: a group can look 'safe' simply because it travels less.\n"
        "4. **2020 is not a normal year** (three lockdowns). Comparisons with 2020 overstate any increase.\n"
        "5. **Location:** from 2023 several roads can be listed for one accident; we keep the first (main) road. "
        "GPS points are precise enough for a department map but some are placed at the town centre.\n"
        "6. **People who fled** are included since 2021 without age, sex or injury severity.\n"
        "7. **Correlation is not causation.** Rural roads, night and 80 km/h roads overlap heavily; the app shows "
        "associations, not the isolated effect of one factor.")

    st.subheader("6. Privacy and ethics")
    st.markdown(
        "- The source already removes personal details whose release could harm people (CADA opinion, 2012).\n"
        "- The app only shows **aggregates**. The point map shows accident locations (public information on public "
        "roads) without any personal attribute; hovering gives date, road type and number of victims only.\n"
        "- No attempt is made to link records with other sources that could identify a person.")

    st.subheader("7. Reproducibility")
    st.markdown(
        "- `python -m scripts.build_data` downloads the 20 files from their stable data.gouv.fr links (cached in "
        "`data/raw/`), runs every step above and writes `data/processed/` (Parquet + this report).\n"
        "- Dependencies are pinned in `requirements.txt`; the random sample of the point map uses a fixed seed "
        f"(`SEED = {K.SEED}` in `utils/constants.py`).\n"
        f"- Processed data built on {q['built_at']}.")

    f = current_filters()
    acc, _ = filtered(f)
    if not acc.empty:
        out = summarize(acc, ["year", "dep", "dep_name"])
        st.download_button("Download the current selection by department and year (CSV)",
                           out.to_csv(index=False).encode("utf-8"), file_name="road_accidents_selection.csv",
                           mime="text/csv", icon=":material/download:")
