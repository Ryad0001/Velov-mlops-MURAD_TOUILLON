-- Exécuté une seule fois par l'image Postgres, à la création du volume de données.
CREATE TABLE IF NOT EXISTS predictions (
    id               BIGSERIAL PRIMARY KEY,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    station_id       INTEGER      NOT NULL,
    timestamp        TIMESTAMPTZ  NOT NULL,
    target_timestamp TIMESTAMPTZ  NOT NULL,
    capacity         INTEGER      NOT NULL,
    bikes_available  INTEGER      NOT NULL,
    temperature      REAL         NOT NULL,
    is_raining       BOOLEAN      NOT NULL,
    predicted_bikes  REAL         NOT NULL,
    model_version    TEXT         NOT NULL
);

CREATE INDEX IF NOT EXISTS predictions_station_created_idx
    ON predictions (station_id, created_at DESC);
