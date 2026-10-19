# Road deaths in France: the curve has stopped falling

**A data-storytelling dashboard built with Streamlit** · Individual student project – EFREI Paris, Data Visualization 2026 · `#EFREIDataStories2026`

> In 2024, 3,193 people died on the roads of metropolitan France — almost 9 a day, and only 1.6 % fewer than in 2019.
> The EU wants road deaths halved by 2030. This app shows **where, who and when** the risk concentrates, and what it would take to get there.

- **Live app:** `<add your Streamlit Community Cloud URL here>`
- **Demo video (2–4 min):** `<add your video link here>` — script in [`docs/demo_video_script.md`](docs/demo_video_script.md)
- **Storyboard:** [`docs/storyboard.md`](docs/storyboard.md)

---

## 1. The story in one minute

| | |
|---|---|
| **Audience** | Local road-safety decision-makers (departmental coordinators in the *préfectures*, *conseils départementaux* that run rural roads); secondary: citizens and journalists. |
| **Problem (hook)** | Deaths fell for decades, then stalled: 2,541 (2020, lockdowns) → 3,193 (2024). France is ~690 deaths above a straight path to the EU 2030 goal (≈1,622). |
| **Questions** | Is road safety still improving? Where are accidents deadliest? Who dies? When? What reductions would reach the goal? |
| **Pattern** | Before/after over time + compare regions with a map + rankings & distributions + what-if sliders. |

### Key insights (metropolitan France, 2020–2024)

1. **Plateau** – after the 2020 lockdown dip, ~3,200 deaths a year; 2024 is only 1.6 % below 2019.
2. **Rural roads** – 36 % of injury accidents but **67 % of deaths**; a rural accident is **3.6× as deadly** (11.1 vs 3.0 killed per 100 accidents). 80 km/h roads: 14 % of accidents, **36 % of deaths**.
3. **Loss of control** – **41 % of deaths** happen when a single vehicle crashes with nobody else involved; 43 % involve a fixed obstacle (trees: 10 %).
4. **Night** – unlit roads at night: 11 % of accidents, **25 % of deaths**; weekend nights are 2.3× as deadly per accident as weekday daytime.
5. **Unprotected road users** – per 1,000 people involved in an accident: pedestrians 49.8, motorcyclists 44.8, cyclists 38.5 vs car occupants 21.9.
6. **Two age peaks** – ~496 deaths/year among 18–24-year-olds and ~486 among the over-75s (37 % of pedestrians killed are 75+). Men = 78 % of deaths.
7. **New risk** – e-scooter deaths: 9 (2020) → 47 (2024).

**Implication:** halving deaths requires acting on rural roads **and** vulnerable users at the same time — no single group is large enough (see the *What would it take?* page).

---

## 2. Data

| | |
|---|---|
| **Dataset** | *Bases de données annuelles des accidents corporels de la circulation routière – Années de 2005 à 2024* |
| **Portal** | data.gouv.fr (approved portal) – <https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024> |
| **Producer** | ONISR – Ministère de l'Intérieur (BAAC file, filled in by police / gendarmerie) |
| **Licence** | Licence Ouverte / Open Licence v2.0 (Etalab) – reuse allowed with attribution |
| **Years used** | 2020–2024 (5 years × 4 tables = 20 CSV files, ≈150 MB raw) |
| **Size after cleaning** | 268,788 accidents · 612,181 people involved |
| **Reference layer** | Department boundaries: IGN Admin Express, simplified by [france-geojson](https://github.com/gregoiredavid/france-geojson) (Licence Ouverte) |
| **Context figures** | 2019 baseline (3,244 deaths) – ONISR *Bilan 2024*; EU target −50 % 2019→2030 – European Commission |

The exact resource IDs and official byte sizes of the 20 files are in `utils/constants.py` (`RESOURCES`). The raw files are **not** bundled: `scripts/build_data.py` downloads them from their stable data.gouv.fr links. The small, analysis-ready Parquet files are included in `data/processed/` so the app starts instantly.

### Four tables, one join key

```
caract (1 row / accident) ──Num_Acc── lieux (1+ rows / accident since 2023)
        │                                  
        └──Num_Acc── vehicules (1 row / vehicle) ──Num_Acc + id_vehicule── usagers (1 row / person)
```

### Cleaning & validation (all shown in the app, page *Data quality & method*)

- Schema harmonisation: key `Accident_Id` (2022) → `Num_Acc`; spaces stripped (`" -1"`); everything read as text then typed explicitly; month `"1"` (2020) vs `"01"`.
- `lieux` lists several roads per accident from 2023 (70,860 rows for 54,822 accidents) → first (main) road kept, so joins stay one-to-one.
- Speed limit: typos with an extra zero corrected (500→50…), implausible values (1–6 km/h) and `-1` set to missing.
- GPS: decimal commas, check that each point falls inside its own department's bounding box (99.99 % do).
- Age from birth year; implausible ages removed; people who fled (since 2021, no severity) kept but excluded from victim counts.
- **Validation:** key uniqueness, referential integrity of the 3 child tables, person→vehicle link, code domains for 11 coded variables, file sizes vs published sizes, and **reconciliation with ONISR's official death toll (2023: 3,398; 2024: 3,432 — identical)**.

### Feature engineering

`lethality` (killed per 100 accidents), `area` (urban / rural), `mode` (31 vehicle codes + pedestrians → 8 road-user groups), `age_band`, `night`, `weekend`, `light_group`, `severity`, `single_vehicle`, `hit_tree`, `hit_fixed_obstacle`, presence flags (`has_moto`, `has_bike`, `has_edp`…), `region`, `territory`.

### Limitations (also in the app)

Police-recorded data under-count slight injuries (lethality is an upper bound) · "hospitalised" no longer an official statistic since 2019 · no exposure data (vehicle-km), so rates are per accident / per person involved, not per km · 2020 distorted by lockdowns · associations, not causal effects.

---

## 3. Run it

Requires **Python 3.11+** (tested with 3.13).

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                 # opens http://localhost:8501
```

Rebuild the processed data from the official files (≈150 MB download, ~30 s processing):

```bash
python -m scripts.build_data            # uses cached raw files in data/raw/ if present
python -m scripts.build_data --refresh  # force a fresh download from data.gouv.fr
```

Tests (data invariants + every page under 7 filter scenarios):

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Or with `make`: `make install`, `make data`, `make run`, `make test`.

### Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository (the `.gitignore` excludes `data/raw/`).
2. On <https://share.streamlit.io> → *Create app* → choose the repo, branch `main`, main file `app.py`; in *Advanced settings* pick Python 3.12 or 3.13.
3. Deploy. The app reads `data/processed/*.parquet`; if they are missing it rebuilds them by downloading the raw files.

---

## 4. Project structure

```
app.py                     entry point: page config, navigation, sidebar filters
sections/
  intro.py                 1 · hook, audience, questions, how to read
  overview.py              2 · KPI header tied to filters, monthly trend, urban vs rural
  deep_dives.py            3 · Where (map, scatter, ranking, breakdowns, drill-down) / Who / When
  what_if.py               4 · scenario sliders vs EU 2030 goal (waterfall)
  conclusions.py           5 · insights, implications, limits, next steps
  data_quality.py          checks, cleaning log, missingness, biases, ethics, reproducibility
  common.py                shared helpers + fixed national reference figures
utils/
  constants.py             resource IDs, code labels, regions, palette, SEED
  io.py                    fetch_and_cache(), read_raw(), load_processed(), license_text()
  prep.py                  cleaning, validation, joins, feature engineering, quality report
  filters.py               sidebar filters + cached filtering
  metrics.py               group-by aggregations (accidents, killed, lethality…)
  viz.py                   chart functions enforcing one visual style
scripts/build_data.py      download + rebuild processed data
tests/                     pytest: data invariants + app smoke tests
data/processed/            accidents.parquet, users.parquet, missingness.parquet, quality.json
data/geo/                  departements.geojson
docs/                      storyboard, demo-video script
```

### Engineering choices

- **Performance:** raw CSVs are processed once into typed Parquet (11 MB); the app loads them with `st.cache_data`; filtered tables are cached per filter combination; accident-level counts are pre-aggregated so most charts are a single `groupby`. The point map draws all fatal accidents but samples non-fatal ones (≤4,000, fixed `SEED`).
- **Reproducibility:** pinned `requirements.txt`, deterministic pipeline, fixed seed, stable source URLs with size checks, tests.
- **Accessibility:** every chart has `alt` text *and* an optional visible text description (sidebar toggle), plus a table view; axes and units labelled; one primary hue (blue), orange only for contrast, grey for context — pair validated for colour-blind separation; sequential maps use a single-hue ramp; no dual axes; small multiples instead of busy legends.
- **Map basemap:** the department choropleth needs no external tiles. The drill-down point map uses CARTO "positron" tiles loaded by the browser; set `MAP_STYLE=white-bg` to run fully offline.

---

## 5. Credits & licences

- Data: ONISR – Ministère de l'Intérieur, via data.gouv.fr, Licence Ouverte v2.0. Boundaries: IGN / france-geojson, Licence Ouverte.
- Code: MIT licence (see `LICENSE`).
- Development note: in the build environment data.gouv.fr was not reachable, so the 20 files were taken from a public GitHub copy and checked against the official byte sizes published by the data.gouv.fr API: 17 identical, 3 (2020) differ only by line endings. Running `python -m scripts.build_data --refresh` re-downloads the originals.
