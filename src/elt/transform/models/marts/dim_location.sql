SELECT
    row_number() OVER (
        ORDER BY
            location_id
    ) AS location_key,
    location_id,
    location_name,
    location_latitude,
    location_longitude,
    location_timezone,
    location_elevation,
    location_population,
    TRUE AS is_current
FROM
    { { ref('stg_geocoding') } }