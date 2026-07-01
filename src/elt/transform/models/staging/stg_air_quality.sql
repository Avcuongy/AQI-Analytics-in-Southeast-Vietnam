SELECT
    location_id,
    CAST(date AS TIMESTAMP) AS date,
    pm10,
    pm2_5,
    carbon_monoxide,
    sulphur_dioxide,
    ozone,
    nitrogen_dioxide,
    aerosol_optical_depth,
    dust,
    us_aqi
FROM
    read_parquet(
        '{{ var("staging_path") }}/air_quality/**/*.parquet'
    )