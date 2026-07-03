select
    id as location_id,
    name as location_name,
    latitude as location_latitude,
    longitude as location_longitude,
    timezone as location_timezone,
    elevation as location_elevation,
    population as location_population,
    country as location_country,
    admin1 as location_admin1,
    admin2 as location_admin2,
    admin3 as location_admin3,
    admin4 as location_admin4
from
    read_parquet(
        '{{ var("staging_path") }}/geocoding/**/*.parquet'
    )