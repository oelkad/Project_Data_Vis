<img src="assets/efrei_logo.png" alt="Efrei Paris" width="180">

# Road deaths in France: the curve has stopped falling

| | |
|---|---|
| **Name** | Othmane El Kadiri |
| **Programme** | Data and AI |
| **Email** | [othmane.el-kadiri@efrei.net](mailto:othmane.el-kadiri@efrei.net) |
| **Year** | 2026–2027 |
| **Promo** | 2028 |
| **LinkedIn** | [linkedin.com/in/othmane-el-kadiri-59733b252](https://www.linkedin.com/in/othmane-el-kadiri-59733b252/) |
| **GitHub** | [github.com/oelkad](https://github.com/oelkad) |
| **Course** | Data Analysis & Visualization |
| **Professor** | Mano Joseph MATHEW · [LinkedIn](https://www.linkedin.com/in/manomathew/) · [mano.mathew@efrei.fr](mailto:mano.mathew@efrei.fr) |

**A data-storytelling dashboard built with Streamlit** · Individual student project – Efrei Paris, Data Analysis & Visualization 2026–2027 · `#EFREIDataStories2026`

> In 2024, 3,193 people died on the roads of metropolitan France — almost 9 a day, and only 1.6 % fewer than in 2019.
> The EU wants road deaths halved by 2030. This app shows **where, who and when** the risk concentrates, and what it would take to get there.

- **Live app:** https://road-deaths-france.streamlit.app
- **Demo video:** ['docs/Video.mov']
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
8. **What goes with deadly accidents (correlation matrix, 96 departments)** – lethality rises with the share of crashes into fixed obstacles (r = 0.75), accidents on 80 km/h roads (0.72) and on unlit roads at night (0.71); it falls where there are many accidents (−0.78) and many pedestrian accidents (−0.42). These rural factors are themselves strongly inter-correlated.

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

The resource IDs of the 20 files are in `utils/constants.py` (`RESOURCES`). The raw files are **not** bundled: `scripts/build_data.py` downloads them from data.gouv.fr. The small, analysis-ready Parquet files are included in `data/processed/` so the app starts instantly.

### Four tables, one join key

```
caract (1 row / accident) ──Num_Acc── lieux (1+ rows / accident since 2023)
        │
        └──Num_Acc── vehicules (1 row / vehicle) ──Num_Acc + id_vehicule── usagers (1 row / person)
```

### Cleaning & validation (shown in the app, page *Data quality & method*)

- Schema harmonisation: key `Accident_Id` (2022) → `Num_Acc`; spaces stripped (`" -1"`); everything read as text, then typed.
- `lieux` lists several roads per accident since 2023 → main road kept, so accidents are not double-counted.
- Speed limit: typos with an extra zero corrected (500→50…), impossible values set to missing.
- GPS: decimal commas fixed; points outside their territory left out of the point map only.
- Age from birth year; people who fled (since 2021, no severity) kept but not counted as victims.
- **Validation:** unique accident ID, every row linked to an accident, every accident with a vehicle and a person, codes inside the codebook, GPS inside its territory, and **reconciliation with ONISR's official death toll (2023: 3,398; 2024: 3,432 — identical)**.

### Feature engineering

`lethality` (killed per 100 accidents), `area` (urban / rural), `mode` (31 vehicle codes + pedestrians → 8 road-user groups), `age_band`, `night`, `light_group`, `weekend`, `single_vehicle` (one vehicle, nobody else involved), `hit_fixed_obstacle`, `hit_tree`, `has_moto`, `region`, `territory`.

### Limitations (also in the app)

Police-recorded data under-count slight injuries (lethality is an upper bound) · "hospitalised" no longer an official statistic since 2019 · no traffic volumes, so rates are per accident / per person involved, not per km · 2020 distorted by lockdowns · associations, not causal effects.

---

## 3. Run it

Requires **Python 3.11+** (tested with 3.13).

```bash
pip install -r requirements.txt
streamlit run app.py                 # opens http://localhost:8501
```

Rebuild the processed data from the official files (≈150 MB download the first time, ~20 s processing):

```bash
python -m scripts.build_data         # delete data/raw/ first to force a fresh download
```

### Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository (`data/raw/` is excluded by `.gitignore`).
2. On <https://share.streamlit.io> → *Create app* → repo, branch `main`, file `app.py`, Python 3.13.
3. After each `git push`, use *Reboot app* if a change does not show up.

---

## 4. Project structure

```
app.py               entry point: page config, navigation, sidebar filters, footer
sections/
  intro.py           1 · hook, author card, audience, questions
  overview.py        2 · KPIs tied to the filters, monthly trend, urban vs rural
  deep_dives.py      3 · Where (map, scatter, top 10, breakdowns, correlation matrix, drill-down) / Who / When
  what_if.py         4 · scenario sliders vs the EU 2030 goal (waterfall)
  conclusions.py     5 · insights, where to act, limits
  data_quality.py    checks, cleaning log, limitations, reproducibility
  common.py          shared helpers + fixed national figures used in the text
utils/
  constants.py       source file IDs, code labels, regions, colours
  io.py              download with cache, load the processed tables
  prep.py            cleaning, joins, feature engineering, validation checks
  filters.py         sidebar filters, cached filtering, summarize() aggregation
  viz.py             every chart (Plotly) with one shared style
  about.py           author / course card and Efrei logo
scripts/build_data.py   rebuild data/processed/ from the raw files
data/processed/      accidents.parquet, users.parquet, quality.json
data/geo/            departements.geojson
docs/                storyboard, demo-video script
assets/              Efrei logo
```

### Engineering choices

- **Performance:** raw CSVs are processed once into typed Parquet (≈9 MB); the app loads them with `st.cache_data` and caches each filter combination; per-accident counts are pre-computed, so most charts are a single `groupby`. The point map shows every fatal accident and a random sample of up to 4,000 others.
- **Reproducibility:** pinned `requirements.txt`, one script rebuilds all the data from the official files.
- **Readability of the charts:** one main colour (blue), orange only for contrast, grey for context; one-hue scale for maps; blue/red for correlations; no dual axes; small multiples instead of crowded legends; hover tooltips everywhere.

---

## 5. Credits & licences

- Data: ONISR – Ministère de l'Intérieur, via data.gouv.fr, Licence Ouverte v2.0. Boundaries: IGN / france-geojson, Licence Ouverte.
