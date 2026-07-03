select
    t.time_key,
    l.location_key,
    wc.weather_key,
    w.temperature_2m,
    w.relative_humidity_2m,
    w.rain,
    w.surface_pressure,
    w.cloud_cover,
    w.wind_speed_10m,
    w.wind_direction_10m,
    w.sunshine_duration,
    w.boundary_layer_height,
    w.dew_point_2m
from
    {{ ref('stg_weather') }} w
    join {{ ref('dim_time') }} t on cast(strftime(w.full_date, '%Y%m%d%H') as bigint) = t.time_key
    join {{ ref('dim_location') }} l on w.location_id = l.location_id
    and l.is_current = true
    join {{ ref('dim_weather_code') }} wc on w.weather_code = wc.weather_code