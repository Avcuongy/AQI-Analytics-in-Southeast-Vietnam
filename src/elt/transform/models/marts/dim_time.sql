select
    distinct cast(strftime("full_date", '%Y%m%d%H') as bigint) as time_key,
    full_date,
    hour("full_date") as hour,
    day("full_date") as day,
    month("full_date") as month,
    year("full_date") as year,
    quarter("full_date") as quarter,
    dayname("full_date") as day_of_week,
    weekofyear("full_date") as week_of_year,
    hour("full_date") between 6
    and 17 as is_day
from
    {{ ref('stg_weather') }}