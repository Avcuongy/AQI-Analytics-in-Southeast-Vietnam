select
    row_number() over (
        order by
            location_id,
            dbt_valid_from
    ) as location_key,
    location_id,
    location_name,
    location_latitude,
    location_longitude,
    location_timezone,
    location_elevation,
    location_population,
    cast(dbt_valid_from as date) as start_date,
    cast(dbt_valid_to as date) as end_date,
    (dbt_valid_to is null) as is_current
from
    { { ref('snapshot_location') } }