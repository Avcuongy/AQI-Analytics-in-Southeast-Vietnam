select
    id as location_id,
    name as location_name,
    latitude as location_latitude,
    longitude as location_longitude,
    timezone as location_timezone,
    elevation as location_elevation,
    population as location_population
from
    read_parquet(
        '{{ var("staging_path") }}/geocoding/geocoding_latest.parquet'
    )