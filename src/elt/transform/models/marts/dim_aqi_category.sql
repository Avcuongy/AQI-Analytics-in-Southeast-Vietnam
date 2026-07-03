select
    aqi_key,
    aqi_category,
    aqi_min,
    aqi_max,
    aqi_description
from
    (
        values
            (
                1,
                'good',
                0,
                50,
                'air quality is satisfactory, and air pollution poses little or no risk.'
            ),
            (
                2,
                'moderate',
                51,
                100,
                'air quality is acceptable. however, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.'
            ),
            (
                3,
                'unhealthy for sensitive groups',
                101,
                150,
                'members of sensitive groups may experience health effects. the general public is less likely to be affected.'
            ),
            (
                4,
                'unhealthy',
                151,
                200,
                'some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.'
            ),
            (
                5,
                'very unhealthy',
                201,
                300,
                'health alert: the risk of health effects is increased for everyone.'
            ),
            (
                6,
                'hazardous',
                301,
                9999,
                'health warning of emergency conditions: everyone is more likely to be affected.'
            )
    ) as t(
        aqi_key,
        aqi_category,
        aqi_min,
        aqi_max,
        aqi_description
    )