# Dataset used

**Bases de données annuelles des accidents corporels de la circulation routière – Années de 2005 à 2024**
Producer: ONISR – Ministère de l'Intérieur · Portal: data.gouv.fr · Licence: Licence Ouverte / Open Licence v2.0 (Etalab)

Dataset page: https://www.data.gouv.fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024

Files used (2020–2024, 4 tables per year) — stable links `https://www.data.gouv.fr/api/1/datasets/r/<id>`:

| Year | Accidents (caract) | Locations (lieux) | Vehicles (vehicules) | People (usagers) |
|---|---|---|---|---|
| 2020 | 07a88205-83c1-4123-a993-cba5331e8ae0 | e85c41f7-d4ea-4faf-877f-ab69a620ce21 | a66be22f-c346-49af-b196-71df24702250 | 78c45763-d170-4d51-a881-e3147802d7ee |
| 2021 | 85cfdc0c-23e4-4674-9bcd-79a970d7269b | 8a4935aa-38cd-43af-bf10-0209d6d17434 | 0bb5953a-25d8-46f8-8c25-b5c2f5ba905e | ba5a1956-7e82-41b7-a602-89d7dd484d7a |
| 2022 | 5fc299c0-4598-4c29-b74c-6a67b0cc27e7 | a6ef711a-1f03-44cb-921a-0ce8ec975995 | c9742921-4427-41e5-81bc-f13af8bc31a0 | 62c20524-d442-46f5-bfd8-982c59763ec8 |
| 2023 | 104dbb32-704f-4e99-a71e-43563cb604f2 | 8bef19bf-a5e4-46b3-b5f9-a145da4686bc | 146a42f5-19f0-4b3e-a887-5cd8fbef057b | 68848e2a-28dd-4efc-9d5f-d512f7dbe66f |
| 2024 | 83f0fb0e-e0ef-47fe-93dd-9aaee851674a | 228b3cda-fdfb-4677-bd54-ab2107028d2d | fd30513c-6b11-4a56-b6dc-5ac87728794b | f57b1f58-386d-4048-8f78-2ebe435df868 |

Codebook: "Description des bases de données annuelles des accidents corporels de la circulation routière – Années de 2005 à 2024" (ONISR, 21 Oct 2025), on the same dataset page.

Processed, analysis-ready extract included in `data/processed/` (Parquet, ≈9 MB). Rebuild with `python -m scripts.build_data`.

Reference layer: department boundaries – IGN Admin Express (simplified) via https://github.com/gregoiredavid/france-geojson (Licence Ouverte), file `data/geo/departements.geojson`.
