"""Ingestion bronze : deux passages sur les mêmes données n'ajoutent aucun doublon."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb
import pytest

from velov.ingest import ingest

NOW = datetime(2026, 10, 26, 14, 30, tzinfo=UTC)


def _station(number: int, last_update: str, bikes: int) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "number": number,
            "status": "OPEN",
            "last_update": last_update,
            "total_stands": {"capacity": 20, "availabilities": {"bikes": bikes, "stands": 20 - bikes}},
        },
    }


@pytest.fixture
def velov() -> dict:
    return {
        "features": [
            _station(1, "2026-10-26T14:20:00.000+00:00", 5),
            _station(2, "2026-10-26T14:25:00.000+00:00", 12),
        ]
    }


@pytest.fixture
def weather() -> dict:
    # 15 h UTC est postérieure à NOW : c'est une prévision, elle ne doit pas entrer en bronze.
    return {
        "hourly": {
            "time": ["2026-10-26T12:00", "2026-10-26T13:00", "2026-10-26T14:00", "2026-10-26T15:00"],
            "temperature_2m": [12.1, 13.0, 13.4, 13.2],
            "precipitation": [0.0, 0.2, 0.0, 0.0],
        }
    }


@pytest.fixture
def con():
    with duckdb.connect(":memory:") as c:
        yield c


def test_second_run_adds_nothing(con, velov, weather):
    first = ingest(con, velov, weather, NOW)
    second = ingest(con, velov, weather, NOW)
    assert first == {"bronze.velov_status": 2, "bronze.weather_hourly": 3}
    assert second == {"bronze.velov_status": 0, "bronze.weather_hourly": 0}
    assert con.execute("SELECT count(*) FROM bronze.velov_status").fetchall() == [(2,)]


def test_only_updated_station_is_added(con, velov, weather):
    ingest(con, velov, weather, NOW)
    velov["features"][0]["properties"]["last_update"] = "2026-10-26T14:28:00.000+00:00"
    assert ingest(con, velov, weather, NOW)["bronze.velov_status"] == 1


def test_payload_is_kept_raw(con, velov, weather):
    ingest(con, velov, weather, NOW)
    bikes = con.execute(
        "SELECT payload->>'$.total_stands.availabilities.bikes' FROM bronze.velov_status WHERE station_id = 2"
    ).fetchall()
    assert bikes == [("12",)]
