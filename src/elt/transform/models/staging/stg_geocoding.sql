SELECT
    id AS location_id,
    name AS location_name,
    latitude AS location_latitude,
    longitude AS location_longitude,
    timezone AS location_timezone,
    elevation AS location_elevation,
    population AS location_population
FROM
    read_parquet(
        '{{ var("staging_path") }}/geocoding/geocoding_latest.parquet'
    )