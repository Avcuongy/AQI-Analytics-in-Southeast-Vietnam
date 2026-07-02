select
    *
from
    (
        values
            (
                1,
                'Good',
                0,
                50,
                'Air quality is satisfactory, and air pollution poses little or no risk.'
            ),
            (
                2,
                'Moderate',
                51,
                100,
                'Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.'
            ),
            (
                3,
                'Unhealthy for Sensitive Groups',
                101,
                150,
                'Members of sensitive groups may experience health effects. The general public is less likely to be affected.'
            ),
            (
                4,
                'Unhealthy',
                151,
                200,
                'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.'
            ),
            (
                5,
                'Very Unhealthy',
                201,
                300,
                'Health alert: The risk of health effects is increased for everyone.'
            ),
            (
                6,
                'Hazardous',
                301,
                9999,
                'Health warning of emergency conditions: everyone is more likely to be affected.'
            )
    ) t(
        aqi_key,
        aqi_category,
        aqi_min,
        aqi_max,
        aqi_description
    )