"""Constants shared by the pipeline and the app.

Everything that is a "magic value" lives here: official resource IDs, code
labels from the ONISR codebook, department/region reference tables, the
colour palette and the random seed. Keeping them in one place makes the
pipeline reproducible and the charts consistent.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------
SEED = 2026  # used whenever we sample points (map layer) - see README
YEARS = [2020, 2021, 2022, 2023, 2024]
TABLES = ["caract", "lieux", "vehicules", "usagers"]

# --------------------------------------------------------------------------
# Source: data.gouv.fr - "Bases de données annuelles des accidents corporels
# de la circulation routière - Années de 2005 à 2024" (ONISR / Ministère de
# l'Intérieur), Licence Ouverte / Open Licence v2.0 (Etalab).
# Stable resource links: https://www.data.gouv.fr/api/1/datasets/r/<id>
# Sizes are the official byte sizes published in the data.gouv.fr API; they
# are used as an integrity check after download.
# --------------------------------------------------------------------------
DATASET_ID = "53698f4ca3a729239d2036df"
DATASET_PAGE = (
    "https://www.data.gouv.fr/datasets/"
    "bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024"
)
DATASET_TITLE = (
    "Bases de données annuelles des accidents corporels de la circulation "
    "routière – Années de 2005 à 2024"
)
PRODUCER = "ONISR – Ministère de l'Intérieur"
LICENSE_NAME = "Licence Ouverte / Open Licence v2.0 (Etalab)"
LICENSE_URL = "https://www.etalab.gouv.fr/licence-ouverte-open-licence/"
RESOURCE_URL = "https://www.data.gouv.fr/api/1/datasets/r/{rid}"

RESOURCES: dict[int, dict[str, tuple[str, str, int]]] = {
    # year: {table: (resource id, official file name, official size in bytes)}
    2020: {
        "caract": ("07a88205-83c1-4123-a993-cba5331e8ae0", "caracteristiques-2020.csv", 5655584),
        "lieux": ("e85c41f7-d4ea-4faf-877f-ab69a620ce21", "lieux-2020.csv", 4521088),
        "vehicules": ("a66be22f-c346-49af-b196-71df24702250", "vehicules-2020.csv", 5492931),
        "usagers": ("78c45763-d170-4d51-a881-e3147802d7ee", "usagers-2020.csv", 10054646),
    },
    2021: {
        "caract": ("85cfdc0c-23e4-4674-9bcd-79a970d7269b", "carcteristiques-2021.csv", 7045926),
        "lieux": ("8a4935aa-38cd-43af-bf10-0209d6d17434", "lieux-2021.csv", 5771984),
        "vehicules": ("0bb5953a-25d8-46f8-8c25-b5c2f5ba905e", "vehicules-2021.csv", 6202316),
        "usagers": ("ba5a1956-7e82-41b7-a602-89d7dd484d7a", "usagers-2021.csv", 13028412),
    },
    2022: {
        "caract": ("5fc299c0-4598-4c29-b74c-6a67b0cc27e7", "carcteristiques-2022.csv", 6884406),
        "lieux": ("a6ef711a-1f03-44cb-921a-0ce8ec975995", "lieux-2022.csv", 5617313),
        "vehicules": ("c9742921-4427-41e5-81bc-f13af8bc31a0", "vehicules-2022.csv", 6021965),
        "usagers": ("62c20524-d442-46f5-bfd8-982c59763ec8", "usagers-2022.csv", 13013255),
    },
    2023: {
        "caract": ("104dbb32-704f-4e99-a71e-43563cb604f2", "caract-2023.csv", 6591826),
        "lieux": ("8bef19bf-a5e4-46b3-b5f9-a145da4686bc", "lieux-2023.csv", 7176266),
        "vehicules": ("146a42f5-19f0-4b3e-a887-5cd8fbef057b", "vehicules-2023.csv", 6431828),
        "usagers": ("68848e2a-28dd-4efc-9d5f-d512f7dbe66f", "usagers-2023.csv", 13938227),
    },
    2024: {
        "caract": ("83f0fb0e-e0ef-47fe-93dd-9aaee851674a", "caract-2024.csv", 6538156),
        "lieux": ("228b3cda-fdfb-4677-bd54-ab2107028d2d", "lieux-2024.csv", 7070795),
        "vehicules": ("fd30513c-6b11-4a56-b6dc-5ac87728794b", "vehicules-2024.csv", 6369908),
        "usagers": ("f57b1f58-386d-4048-8f78-2ebe435df868", "usagers-2024.csv", 13843733),
    },
}

GEOJSON_URL = (
    "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/"
    "departements-version-simplifiee.geojson"
)

# --------------------------------------------------------------------------
# External reference figures (context only - NOT computed from the dataset)
# ONISR, "La sécurité routière en France - bilan définitif 2024" (May 2025)
# and European Commission road-safety target (-50 % deaths 2019 -> 2030).
# --------------------------------------------------------------------------
METRO_KILLED_2019 = 3244          # official, metropolitan France
EU_TARGET_YEAR = 2030
EU_TARGET_FACTOR = 0.5            # halve deaths vs. 2019
ONISR_TOTAL_KILLED = {2023: 3398, 2024: 3432}  # France incl. overseas, official
ONISR_SOURCE_URL = (
    "https://www.onisr.securite-routiere.gouv.fr/etat-de-linsecurite-routiere/"
    "bilans-annuels-de-la-securite-routiere/bilan-2024-de-la-securite-routiere"
)
EU_TARGET_SOURCE_URL = (
    "https://transport.ec.europa.eu/news-events/news/"
    "2023-figures-show-stalling-progress-reducing-road-fatalities-too-many-countries-2024-03-08_en"
)

# Lockdowns (used as annotation bands on time series)
LOCKDOWNS = [
    ("2020-03-17", "2020-05-11", "Lockdown 1"),
    ("2020-10-30", "2020-12-15", "Lockdown 2"),
    ("2021-04-03", "2021-05-03", "Lockdown 3"),
]

# --------------------------------------------------------------------------
# Code labels (ONISR codebook, "Description des bases de données annuelles")
# --------------------------------------------------------------------------
LUM = {1: "Daylight", 2: "Dusk / dawn", 3: "Night, no street lighting",
       4: "Night, lighting off", 5: "Night, lighting on"}
LUM_GROUP = {1: "Day", 2: "Dusk / dawn", 3: "Night – unlit", 4: "Night – unlit", 5: "Night – lit"}
AGG = {1: "Rural (outside built-up area)", 2: "Urban (built-up area)"}
AGG_SHORT = {1: "Rural", 2: "Urban"}
ATM = {1: "Normal", 2: "Light rain", 3: "Heavy rain", 4: "Snow / hail", 5: "Fog / smoke",
       6: "Strong wind", 7: "Dazzling", 8: "Overcast", 9: "Other"}
COL = {1: "Head-on (2 vehicles)", 2: "Rear-end (2 vehicles)", 3: "Side (2 vehicles)",
       4: "Chain (3+ vehicles)", 5: "Multiple (3+ vehicles)", 6: "Other collision",
       7: "No collision (single vehicle)"}
CATR = {1: "Motorway", 2: "National road", 3: "Departmental road", 4: "Municipal road",
        5: "Off public network", 6: "Car park", 7: "Urban metropolitan road", 9: "Other"}
INT = {1: "No intersection", 2: "X intersection", 3: "T intersection", 4: "Y intersection",
       5: "5+ branches", 6: "Roundabout", 7: "Square", 8: "Level crossing", 9: "Other"}
SURF = {1: "Normal", 2: "Wet", 3: "Puddles", 4: "Flooded", 5: "Snow", 6: "Mud", 7: "Icy",
        8: "Oil / grease", 9: "Other"}
GRAV = {1: "Unhurt", 2: "Killed", 3: "Hospitalised (>24 h)", 4: "Slightly injured"}
CATU = {1: "Driver", 2: "Passenger", 3: "Pedestrian"}
SEXE = {1: "Male", 2: "Female"}
TRAJET = {1: "Home – work", 2: "Home – school", 3: "Shopping", 4: "Professional use",
          5: "Leisure", 9: "Other"}
OBS_TREE = 2

# Vehicle category (catv) -> road-user mode (feature engineering).
# 8 groups max so that categorical colours stay distinguishable.
MODE_ORDER = ["Car", "Motorcycle >50cc", "Pedestrian", "Bicycle", "Moped ≤50cc",
              "E-scooter (EDP)", "Van / truck / bus", "Other"]
CATV_TO_MODE: dict[int, str] = {}
for _c in (7, 3):
    CATV_TO_MODE[_c] = "Car"
for _c in (31, 32, 33, 34, 42, 43):
    CATV_TO_MODE[_c] = "Motorcycle >50cc"
for _c in (2, 30, 41, 35):
    CATV_TO_MODE[_c] = "Moped ≤50cc"
for _c in (1, 80):
    CATV_TO_MODE[_c] = "Bicycle"
for _c in (50, 60):
    CATV_TO_MODE[_c] = "E-scooter (EDP)"
for _c in (10, 13, 14, 15, 16, 17, 37, 38, 39, 40):
    CATV_TO_MODE[_c] = "Van / truck / bus"
# everything else (0 unknown, 20 special, 21 tractor, 36 heavy quad, 99 other) -> Other

VULNERABLE_MODES = ["Pedestrian", "Bicycle", "E-scooter (EDP)", "Moped ≤50cc", "Motorcycle >50cc"]

AGE_BINS = [0, 14, 18, 25, 35, 45, 55, 65, 75, 200]
AGE_LABELS = ["0–13", "14–17", "18–24", "25–34", "35–44", "45–54", "55–64", "65–74", "75+"]

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

VALID_VMA = {10, 15, 20, 25, 30, 40, 45, 50, 60, 70, 80, 90, 100, 110, 120, 130}
VMA_TYPO_FIX = {300: 30, 500: 50, 700: 70, 800: 80, 900: 90}  # an extra 0 typed

# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
REGION_DEPS = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Bretagne": ["22", "29", "35", "56"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corse": ["2A", "2B"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Normandie": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
    "Guadeloupe": ["971"],
    "Martinique": ["972"],
    "Guyane": ["973"],
    "La Réunion": ["974"],
    "Mayotte": ["976"],
    "Overseas collectivities (COM)": ["975", "977", "978", "986", "987", "988"],
}
DEP_TO_REGION = {d: r for r, ds in REGION_DEPS.items() for d in ds}
OVERSEAS_DEPS = {"971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"}
OVERSEAS_NAMES = {
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion",
    "975": "Saint-Pierre-et-Miquelon", "976": "Mayotte", "977": "Saint-Barthélemy",
    "978": "Saint-Martin", "986": "Wallis-et-Futuna", "987": "Polynésie française",
    "988": "Nouvelle-Calédonie",
}
# Generous bounding boxes (lat_min, lat_max, lon_min, lon_max) used to validate
# GPS coordinates of overseas accidents. Metropolitan departments are checked
# against their own polygon bounding box computed from the GeoJSON.
OVERSEAS_BBOX = {
    "971": (15.8, 16.6, -61.9, -60.9), "972": (14.35, 14.9, -61.3, -60.75),
    "973": (2.0, 6.0, -54.7, -51.5), "974": (-21.45, -20.85, 55.15, 55.9),
    "975": (46.7, 47.2, -56.5, -56.1), "976": (-13.1, -12.55, 44.95, 45.35),
    "977": (17.85, 17.98, -62.95, -62.78), "978": (18.0, 18.15, -63.2, -62.95),
    "986": (-14.4, -13.1, -178.3, -176.0), "987": (-28.0, -7.0, -155.0, -134.0),
    "988": (-23.0, -19.0, 163.0, 169.0),
}
METRO_BBOX = (41.2, 51.2, -5.3, 9.7)

# --------------------------------------------------------------------------
# Visual identity (validated with the colour-blind checker - see README)
# --------------------------------------------------------------------------
BLUE = "#2a78d6"      # primary series
ORANGE = "#eb6834"    # contrast / emphasis series
GREY = "#c3c2b7"      # de-emphasised marks
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORDINAL_BLUE = ["#86b6ef", "#3987e5", "#256abf", "#104281"]
AREA_COLORS = {"Urban": BLUE, "Rural": ORANGE}
