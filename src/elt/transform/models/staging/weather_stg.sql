SELECT
    location_id,
    CAST(date AS TIMESTAMP) AS date,
    temperature_2m,
    relative_humidity_2m,
    rain,
    surface_pressure,
    cloud_cover,
    wind_speed_10m,
    wind_direction_10m,
    CAST(weather_code AS INTEGER) AS weather_code,
    sunshine_duration,
    boundary_layer_height,
    dew_point_2m,
    CAST(is_day AS BOOLEAN) AS is_day
FROM
    read_parquet('{{ var("staging_path") }}/weather/**/*.parquet')