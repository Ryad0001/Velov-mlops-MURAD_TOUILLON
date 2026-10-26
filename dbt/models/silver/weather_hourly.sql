-- Une ligne par heure UTC. Température à l'heure pile, précipitations cumulées sur l'heure écoulée.
select
    observed_at,
    (payload->>'$.temperature_2m')::double    as temperature,
    (payload->>'$.precipitation')::double     as precipitation,
    (payload->>'$.precipitation')::double > 0 as is_raining
from {{ source('bronze', 'weather_hourly') }}
