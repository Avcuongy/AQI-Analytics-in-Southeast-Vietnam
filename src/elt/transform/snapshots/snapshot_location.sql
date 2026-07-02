{ % snapshot snapshot_location % } { { config(
    target_schema = 'snapshots',
    unique_key = 'location_id',
    strategy = 'check',
    check_cols = ['location_name', 'location_latitude', 'location_longitude',
                    'location_timezone', 'location_elevation', 'location_population'],
    invalidate_hard_deletes = True
) } }
SELECT
    location_id,
    location_name,
    location_latitude,
    location_longitude,
    location_timezone,
    location_elevation,
    location_population
FROM
    { { ref('stg_geocoding') } } { % endsnapshot % }