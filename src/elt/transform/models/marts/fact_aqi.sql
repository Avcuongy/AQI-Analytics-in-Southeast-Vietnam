select
    t.time_key,
    l.location_key,
    c.aqi_key,
    a.pm10,
    a.pm2_5,
    a.carbon_monoxide,
    a.sulphur_dioxide,
    a.ozone,
    a.nitrogen_dioxide,
    a.aerosol_optical_depth,
    a.dust,
    a.us_aqi
from
    { { ref('stg_air_quality') } } a
    join { { ref('dim_time') } } t on cast(strftime(a.date, '%Y%m%d%H') as bigint) = t.time_key
    join { { ref('dim_location') } } l on a.location_id = l.location_id
    and l.is_current = true
    left join { { ref('dim_aqi_category') } } c on a.us_aqi between c.aqi_min
    and c.aqi_max