select
    location_id,
    cast(date as timestamp) as full_date,
    pm10,
    pm2_5,
    carbon_monoxide,
    sulphur_dioxide,
    ozone,
    nitrogen_dioxide,
    aerosol_optical_depth,
    dust,
    us_aqi
from
    read_parquet(
        '{{ var("staging_path") }}/air_quality/**/*.parquet'
    )