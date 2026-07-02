select
    location_id,
    cast(date as timestamp) as full_date,
    temperature_2m,
    relative_humidity_2m,
    rain,
    surface_pressure,
    cloud_cover,
    wind_speed_10m,
    wind_direction_10m,
    cast(weather_code as int) as weather_code,
    sunshine_duration,
    boundary_layer_height,
    dew_point_2m,
    cast(is_day as boolean) as is_day
from
    read_parquet('{{ var("staging_path") }}/weather/**/*.parquet')