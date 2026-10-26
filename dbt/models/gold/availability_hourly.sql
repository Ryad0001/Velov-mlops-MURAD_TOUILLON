-- Historique au schéma du contrat de données (velov.features.RAW_COLUMNS), lu par l'entraînement.
-- Une ligne par station ouverte et par heure UTC : dernière mesure de l'heure + météo de l'heure.
-- Seules les lignes conformes au contrat d'entrée de l'API sont retenues.
with last_in_hour as (
    select
        station_id,
        date_trunc('hour', observed_at) as hour,
        capacity,
        bikes_available
    from {{ ref('station_status') }}
    where status = 'OPEN'
    qualify row_number() over (
        partition by station_id, date_trunc('hour', observed_at) order by observed_at desc
    ) = 1
)

select
    s.station_id,
    s.hour as "timestamp",
    s.capacity,
    s.bikes_available,
    w.temperature,
    w.is_raining
from last_in_hour as s
inner join {{ ref('weather_hourly') }} as w on w.observed_at = s.hour
where s.capacity between 1 and 100
  and s.bikes_available between 0 and s.capacity
  and w.temperature between -30 and 50
  and w.is_raining is not null
