-- Une ligne par station et par mesure, typée depuis le payload brut.
-- Aucune ligne n'est écartée ici : les anomalies restent visibles pour les tests.
select
    station_id,
    last_update                                                  as observed_at,
    (payload->>'$.total_stands.capacity')::integer               as capacity,
    (payload->>'$.total_stands.availabilities.bikes')::integer   as bikes_available,
    (payload->>'$.total_stands.availabilities.stands')::integer  as stands_available,
    payload->>'$.status'                                         as status,
    ingested_at
from {{ source('bronze', 'velov_status') }}
