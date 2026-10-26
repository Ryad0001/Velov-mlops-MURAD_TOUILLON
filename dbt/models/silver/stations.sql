-- Une ligne par station : sa description d'après son dernier snapshot.
select
    station_id,
    payload->>'$.name'                             as name,
    payload->>'$.commune'                          as commune,
    (payload->>'$.total_stands.capacity')::integer as capacity,
    (payload->>'$.lat')::double                    as lat,
    (payload->>'$.lng')::double                    as lon,
    payload->>'$.status'                           as status,
    last_update
from {{ source('bronze', 'velov_status') }}
qualify row_number() over (partition by station_id order by last_update desc) = 1
