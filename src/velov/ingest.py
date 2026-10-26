"""Ingestion bronze : open data Vélo'v et météo de Lyon, chargés tels quels dans DuckDB.

Bronze = la donnée brute telle que reçue (payload JSON) + l'instant d'ingestion.
On n'y corrige rien : le typage et le nettoyage sont faits par dbt (silver),
le contrat de données est appliqué en gold.

Idempotence : chaque table a une clé naturelle déclarée PRIMARY KEY
(station + last_update pour Vélo'v, heure UTC pour la météo) et l'insertion ignore
les clés déjà présentes. Relancer l'ingestion n'ajoute aucun doublon : seules les
stations dont la mesure a changé depuis le passage précédent entrent en bronze.

Usage :
    python -m velov.ingest --db data/warehouse.duckdb
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd

# Disponibilité temps réel des stations (Grand Lyon, sans clé).
VELOV_URL = (
    "https://download.data.grandlyon.com/wfs/rdata?SERVICE=WFS&VERSION=2.0.0&request=GetFeature"
    "&typename=jcd_jcdecaux.jcdvelov&outputFormat=application/json;%20subtype=geojson"
)
# Météo horaire de Lyon (Open-Meteo, sans clé). timezone=GMT : heures renvoyées en UTC.
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast?latitude=45.76&longitude=4.84"
    "&hourly=temperature_2m,precipitation&past_days=2&forecast_days=1&timezone=GMT"
)

DDL = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.velov_status (
    station_id  INTEGER     NOT NULL,
    last_update TIMESTAMPTZ NOT NULL,
    payload     JSON        NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (station_id, last_update)
);
CREATE TABLE IF NOT EXISTS bronze.weather_hourly (
    observed_at TIMESTAMPTZ NOT NULL PRIMARY KEY,
    payload     JSON        NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);
"""


def fetch_json(url: str, timeout: float = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 (URL constante en https)
        return json.load(response)


def velov_rows(geojson: dict, ingested_at: datetime) -> pd.DataFrame:
    """Une ligne par station. Sans numéro ni last_update, une mesure n'a pas de clé : on l'écarte."""
    props = [f["properties"] for f in geojson["features"]]
    props = [p for p in props if p.get("number") is not None and p.get("last_update")]
    return pd.DataFrame(
        {
            "station_id": [p["number"] for p in props],
            "last_update": pd.to_datetime([p["last_update"] for p in props], utc=True),
            "payload": [json.dumps(p, ensure_ascii=False) for p in props],
            "ingested_at": ingested_at,
        }
    )


def weather_rows(payload: dict, ingested_at: datetime) -> pd.DataFrame:
    """Une ligne par heure. Les heures postérieures à l'ingestion sont des prévisions : écartées."""
    hourly = payload["hourly"]
    records = [dict(zip(hourly, values, strict=True)) for values in zip(*hourly.values(), strict=True)]
    rows = pd.DataFrame(
        {
            "observed_at": pd.to_datetime([r["time"] for r in records], utc=True),
            "payload": [json.dumps(r) for r in records],
            "ingested_at": ingested_at,
        }
    )
    return rows[rows["observed_at"] <= ingested_at]


def _count(con: duckdb.DuckDBPyConnection, table: str) -> int:
    return con.execute(f"SELECT count(*) FROM {table}").fetchall()[0][0]  # noqa: S608 (nom de table interne)


def _insert_new(con: duckdb.DuckDBPyConnection, table: str, rows: pd.DataFrame) -> int:
    """Insère les lignes dont la clé est absente de la table ; renvoie le nombre de lignes ajoutées."""
    before = _count(con, table)
    con.register("incoming", rows)
    con.execute(f"INSERT INTO {table} BY NAME SELECT * FROM incoming ON CONFLICT DO NOTHING")  # noqa: S608
    con.unregister("incoming")
    return _count(con, table) - before


def ingest(con: duckdb.DuckDBPyConnection, velov: dict, weather: dict, ingested_at: datetime) -> dict[str, int]:
    """Charge les deux payloads en bronze. Renvoie le nombre de nouvelles lignes par table."""
    con.execute(DDL)
    return {
        "bronze.velov_status": _insert_new(con, "bronze.velov_status", velov_rows(velov, ingested_at)),
        "bronze.weather_hourly": _insert_new(con, "bronze.weather_hourly", weather_rows(weather, ingested_at)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion bronze : open data Vélo'v + météo de Lyon.")
    parser.add_argument("--db", type=Path, default=Path(os.getenv("VELOV_WAREHOUSE", "data/warehouse.duckdb")))
    args = parser.parse_args()

    velov, weather = fetch_json(VELOV_URL), fetch_json(WEATHER_URL)
    args.db.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(args.db)) as con:
        inserted = ingest(con, velov, weather, datetime.now(UTC))
    for table, n in inserted.items():
        print(f"{table:<22} +{n} lignes")


if __name__ == "__main__":
    main()
