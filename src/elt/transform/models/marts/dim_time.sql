select
    distinct cast(strftime(date, '%Y%m%d%H') as bigint) as time_key,
    date as full_date,
    hour(date) as hour,
    day(date) as day,
    month(date) as month,
    year(date) as year,
    quarter(date) as quarter,
    dayname(date) as day_of_week,
    weekofyear(date) as week_of_year,
    hour(date) between 6
    and 17 as is_day
from
    { { ref('stg_weather') } }