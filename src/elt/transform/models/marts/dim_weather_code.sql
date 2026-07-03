select
    row_number() over (
        order by
            weather_code
    ) as weather_key,
    weather_code,
    weather_description,
    weather_common
from
    {{ ref('weather_code_lookup') }}