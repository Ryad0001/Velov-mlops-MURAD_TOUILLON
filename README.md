# velov-mlops

Projet fil rouge du cours **Industrialisation de l'IA dans le Cloud** (M2 Data Engineering / IA).

Objectif métier : prédire, pour chaque station Vélo'v, le nombre de vélos disponibles **dans une heure**,
et servir cette prédiction via une API fiable, conteneurisée, puis déployée (on-premise et cloud).

## Progression par session

Chaque étape du cours correspond à un tag git. Absent ou bloqué : repartez du tag de fin de la session précédente.

| Tag | Contenu |
|---|---|
| `s1-start` | Données simulées, features, entraînement. API à compléter (TP1) |
| `s1-end` | Modèle v0 servi par FastAPI, tests pytest |

```bash
git checkout s1-end          # récupérer l'état de fin de S1
git checkout -b mon-binome   # travailler sur sa propre branche
```

## Démarrage rapide

Prérequis : Python 3.11+ (3.12 recommandé), git. Docker sera nécessaire en S2.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -e .                     # rend le package velov importable

python -m velov.data                 # génère data/velov_history.csv (simulateur, seed fixe)
python -m velov.train                # entraîne et écrit models/model.joblib + models/metadata.json
python -m velov.train --mlflow       # idem + journalisation MLflow (puis : mlflow ui)
pytest                               # tests
uvicorn velov.api.main:app --reload  # API sur http://127.0.0.1:8000/docs (--reload : en dev uniquement)
```

Exemple d'appel :

```bash
curl -X POST http://127.0.0.1:8000/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"station_id": 3, "timestamp": "2026-10-06T08:00:00+02:00", "capacity": 20,
       "bikes_available": 12, "temperature": 14.5, "is_raining": false}'
```

Le `timestamp` doit porter un fuseau (`+02:00`, `Z`...) : sans fuseau, l'API répond 422.
Les instants sont renvoyés et journalisés en UTC (`"target_timestamp": "2026-10-06T07:00:00Z"`).

## Pipeline de données (S3)

Architecture médaillon dans un entrepôt DuckDB local (`data/warehouse.duckdb`, hors git) :

| Couche | Contenu | Produit par |
|---|---|---|
| bronze | payloads bruts de l'open data Vélo'v (Grand Lyon) et de la météo (Open-Meteo) | `python -m velov.ingest` |
| silver | `stations`, `station_status`, `weather_hourly` : typées, une ligne par clé | dbt |
| gold | `availability_hourly` : une ligne par station et par heure UTC, au schéma du contrat | dbt |

```bash
python -m velov.ingest               # à relancer autant que voulu : aucun doublon
cd dbt && dbt build                  # silver puis gold (profil DuckDB dans dbt/profiles.yml)
```

L'ingestion est **idempotente** : chaque table bronze a une clé naturelle (station + `last_update`,
heure UTC pour la météo) et les clés déjà présentes sont ignorées. Deux passages de suite :
le second affiche `+0 lignes` tant que les stations n'ont pas publié de nouvelle mesure.

La table gold a exactement les colonnes du contrat (`velov.features.RAW_COLUMNS`, celles du simulateur) :
`station_id, timestamp, capacity, bikes_available, temperature, is_raining`. Son contrat dbt est
**enforced** (`dbt/models/gold/_gold.yml`) : une colonne manquante, renommée ou d'un autre type fait
échouer le build, et les bornes du contrat d'entrée de l'API (capacité 1-100, vélos entre 0 et la
capacité, température entre -30 et 50 °C) sont des contraintes de la table.

## Exigences du projet

Le service doit respecter les exigences de [docs/exigences.md](docs/exigences.md), de S1 à S9.
Chaque rendu indique celles qu'il couvre et comment le vérifier.


## Structure

```
src/velov/
  data.py          simulateur de données (remplacé par l'open data en S3, même schéma)
  ingest.py        ingestion bronze idempotente (open data Vélo'v + météo) dans DuckDB
  features.py      features partagées entraînement / API (anti training-serving skew)
  train.py         entraînement, baseline, artefact + metadata.json, option MLflow
  api/main.py      FastAPI : /health, /ready, /v1/model, /v1/predict, /v1/predict/batch
  api/schemas.py   contrat d'entrée / sortie (Pydantic)
tests/             pytest (features, API)
docs/              templates : model card, runbook, ADR
dbt/               modèles silver et gold (S3)
exercices/         démo pickle (S1)
```

## Usage de l'IA générative

Chaque activité indique son mode : **sans IA**, **IA déclarée** ou **IA imposée**.
En mode IA déclarée, ajoutez dans la description de vos commits ou de votre rendu :
outil utilisé, ce que vous lui avez demandé, ce que vous avez vérifié ou corrigé.
