"""Persistance des prédictions dans PostgreSQL.

Activée uniquement si DATABASE_URL est définie : sans base, l'API sert quand même
(les tests tournent sans Postgres). Une erreur d'écriture est loguée, pas remontée :
la base est un enregistrement a posteriori, pas une dépendance du serving.
"""

from __future__ import annotations

import logging
import os

import psycopg

from velov.api.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger("velov.db")

_INSERT = """
INSERT INTO predictions (
    station_id, timestamp, target_timestamp, capacity, bikes_available,
    temperature, is_raining, predicted_bikes, model_version
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def database_url() -> str | None:
    return os.getenv("DATABASE_URL") or None


def check_connection() -> bool:
    """Au démarrage : vérifie que la base répond. Ne crée rien (schéma porté par l'image Postgres)."""
    url = database_url()
    if url is None:
        logger.info("DATABASE_URL absente : prédictions non persistées")
        return False
    with psycopg.connect(url, connect_timeout=5) as conn:
        conn.execute("SELECT 1")
    logger.info("Connexion PostgreSQL OK")
    return True


def save_prediction(request: PredictionRequest, response: PredictionResponse) -> None:
    url = database_url()
    if url is None:
        return
    try:
        with psycopg.connect(url, connect_timeout=5) as conn:
            conn.execute(
                _INSERT,
                (
                    request.station_id,
                    request.timestamp,
                    response.target_timestamp,
                    request.capacity,
                    request.bikes_available,
                    request.temperature,
                    request.is_raining,
                    response.predicted_bikes,
                    response.model_version,
                ),
            )
    except Exception:
        logger.exception("Échec de l'enregistrement de la prédiction")
