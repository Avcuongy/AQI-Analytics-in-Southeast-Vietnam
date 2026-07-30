from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import duckdb
from utils.logger import get_logger

logger = get_logger(__name__, "other")

PROJECT_ROOT = Path(__file__).parents[2]
DATA_DIR = PROJECT_ROOT / "data"
HISTORICAL_DIR = DATA_DIR / "historical"
RAW_GEOCODING_DIR = DATA_DIR / "raw" / "geocoding"
DB_PATH = PROJECT_ROOT / "data_warehouse.duckdb"
AIR_QUALITY_DIR = HISTORICAL_DIR / "air_quality"
WEATHER_DIR = HISTORICAL_DIR / "weather"

MAIN_SCHEMA = "main"
STAGING_SCHEMA = "main_staging"
SNAPSHOTS_SCHEMA = "main_snapshots"
MARTS_SCHEMA = "main_marts"

AQI_COLUMNS = [
    "location_id",
    "location_name",
    "date",
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "sulphur_dioxide",
    "ozone",
    "nitrogen_dioxide",
    "aerosol_optical_depth",
    "dust",
    "us_aqi",
]

WEATHER_COLUMNS = [
    "location_id",
    "location_name",
    "date",
    "temperature_2m",
    "relative_humidity_2m",
    "rain",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "weather_code",
    "sunshine_duration",
    "boundary_layer_height",
    "dew_point_2m",
    "is_day",
]

GEOCODING_COLUMNS = [
    "id",
    "name",
    "latitude",
    "longitude",
    "timezone",
    "elevation",
    "population",
    "country",
    "admin1",
    "admin2",
    "admin3",
    "admin4",
]

WEATHER_CODE_LOOKUP = {
    0: ("clear sky", "clear"),
    1: ("mainly clear", "partly sunny"),
    2: ("partly cloudy", "partly cloudy"),
    3: ("overcast", "cloudy"),
    45: ("fog", "low visibility"),
    48: ("depositing rime fog", "fog"),
    51: ("light drizzle", "drizzle"),
    53: ("moderate drizzle", "drizzle"),
    55: ("dense drizzle", "drizzle"),
    56: ("light freezing drizzle", "freezing drizzle"),
    57: ("dense freezing drizzle", "freezing drizzle"),
    61: ("slight rain", "rain"),
    63: ("moderate rain", "rain"),
    65: ("heavy rain", "rain"),
    66: ("light freezing rain", "freezing rain"),
    67: ("heavy freezing rain", "freezing rain"),
    71: ("slight snow fall", "snow"),
    73: ("moderate snow fall", "snow"),
    75: ("heavy snow fall", "snow"),
    77: ("snow grains", "snow"),
    80: ("slight rain showers", "rain showers"),
    81: ("moderate rain showers", "rain showers"),
    82: ("violent rain showers", "rain showers"),
    85: ("slight snow showers", "snow showers"),
    86: ("heavy snow showers", "snow showers"),
    95: ("thunderstorm", "thunderstorm"),
    96: ("thunderstorm with slight hail", "thunderstorm"),
    99: ("thunderstorm with heavy hail", "thunderstorm"),
}


def _read_folder_csvs(folder: Path) -> pd.DataFrame:
    files = sorted(folder.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {folder}")

    frames = []
    for file_path in files:
        frame = pd.read_csv(file_path)
        frame.columns = frame.columns.str.strip()
        frame = frame.replace({"": pd.NA})
        frame["source_file"] = file_path.name
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def _to_datetime_column(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], errors="coerce")


def _keep_nonempty_rows(
    frame: pd.DataFrame, required_columns: Iterable[str]
) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned = cleaned.dropna(subset=list(required_columns))
    cleaned = cleaned.drop_duplicates()
    return cleaned


def _drop_relation(con: duckdb.DuckDBPyConnection, schema: str, relation: str) -> None:
    relation_type = con.execute(
        """
        select table_type
        from information_schema.tables
        where lower(table_schema) = lower(?)
          and lower(table_name) = lower(?)
        limit 1
        """,
        [schema, relation],
    ).fetchone()
    if relation_type is None:
        return

    object_type = relation_type[0]
    if object_type == "VIEW":
        con.execute(f"drop view {schema}.{relation}")
    else:
        con.execute(f"drop table {schema}.{relation}")


def _register_df(
    con: duckdb.DuckDBPyConnection, name: str, frame: pd.DataFrame
) -> None:
    con.register(name, frame)


def load_to_duckdb(project_root: Optional[Path] = None) -> duckdb.DuckDBPyConnection:
    project_root = project_root or PROJECT_ROOT
    data_dir = project_root / "data"
    historical_dir = data_dir / "historical"
    raw_geocoding_dir = data_dir / "raw" / "geocoding"
    db_path = project_root / "data_warehouse.duckdb"
    air_quality_dir = historical_dir / "air_quality"
    weather_dir = historical_dir / "weather"

    con = duckdb.connect(str(db_path))
    con.execute("PRAGMA threads=4")
    con.execute(f"create schema if not exists {STAGING_SCHEMA}")
    con.execute(f"create schema if not exists {SNAPSHOTS_SCHEMA}")
    con.execute(f"create schema if not exists {MARTS_SCHEMA}")

    logger.info(f"Project root      : {project_root}")
    logger.info(f"DuckDB path       : {db_path}")

    raw_aqi = _read_folder_csvs(air_quality_dir)
    raw_weather = _read_folder_csvs(weather_dir)
    raw_geocoding = _read_folder_csvs(raw_geocoding_dir)

    aqi_measure_columns = [
        "pm10",
        "pm2_5",
        "carbon_monoxide",
        "sulphur_dioxide",
        "ozone",
        "nitrogen_dioxide",
        "aerosol_optical_depth",
        "dust",
        "us_aqi",
    ]

    weather_measure_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "rain",
        "surface_pressure",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "weather_code",
        "sunshine_duration",
        "boundary_layer_height",
        "dew_point_2m",
        "is_day",
    ]

    geo_history = raw_geocoding.copy()
    geo_history["snapshot_date"] = pd.to_datetime(
        geo_history["source_file"].str.extract(r"(\d{4}_\d{2}_\d{2})")[0],
        format="%Y_%m_%d",
        errors="coerce",
    )

    location_summary = (
        geo_history.sort_values(["id", "snapshot_date", "source_file"])
        .groupby("id", as_index=False)
        .agg(
            location_name=("name", "last"),
            location_latitude=("latitude", "last"),
            location_longitude=("longitude", "last"),
            location_timezone=("timezone", "last"),
            location_elevation=("elevation", "last"),
            location_population=("population", "last"),
            start_date=("snapshot_date", "min"),
        )
    )
    location_summary["end_date"] = pd.NaT
    location_summary["is_current"] = True
    location_summary = location_summary.rename(columns={"id": "location_id"})

    clean_aqi = (
        raw_aqi[AQI_COLUMNS + ["source_file"]]
        .assign(date=lambda df: _to_datetime_column(df, "date"))
        .pipe(_keep_nonempty_rows, ["location_id", "date"])
    )
    for column in ["location_id", *aqi_measure_columns]:
        clean_aqi[column] = pd.to_numeric(clean_aqi[column], errors="coerce")
    clean_aqi = clean_aqi.dropna(how="all", subset=aqi_measure_columns)
    clean_aqi = clean_aqi.sort_values(
        ["location_id", "date", "source_file"]
    ).drop_duplicates(subset=["location_id", "date"], keep="last")

    clean_weather = (
        raw_weather[WEATHER_COLUMNS + ["source_file"]]
        .assign(date=lambda df: _to_datetime_column(df, "date"))
        .pipe(_keep_nonempty_rows, ["location_id", "date"])
    )
    for column in ["location_id", *weather_measure_columns]:
        clean_weather[column] = pd.to_numeric(clean_weather[column], errors="coerce")
    clean_weather = clean_weather.dropna(how="all", subset=weather_measure_columns)
    clean_weather = clean_weather.sort_values(
        ["location_id", "date", "source_file"]
    ).drop_duplicates(subset=["location_id", "date"], keep="last")
    clean_weather["is_day"] = clean_weather["is_day"].astype("Int64")

    clean_geocoding = raw_geocoding[GEOCODING_COLUMNS + ["source_file"]].pipe(
        _keep_nonempty_rows, ["id", "name", "latitude", "longitude"]
    )
    for column in ["id", "latitude", "longitude", "elevation", "population"]:
        clean_geocoding[column] = pd.to_numeric(
            clean_geocoding[column], errors="coerce"
        )
    clean_geocoding = clean_geocoding.sort_values(
        ["id", "source_file"]
    ).drop_duplicates(subset=["id"], keep="last")

    logger.info(f"Raw AQI rows      : {len(raw_aqi):,}")
    logger.info(f"Clean AQI rows    : {len(clean_aqi):,}")
    logger.info(f"Raw weather rows  : {len(raw_weather):,}")
    logger.info(f"Clean weather rows: {len(clean_weather):,}")
    logger.info(f"Raw geo rows      : {len(raw_geocoding):,}")
    logger.info(f"Clean geo rows    : {len(clean_geocoding):,}")

    stg_air_quality = clean_aqi[
        [
            "location_id",
            "date",
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "sulphur_dioxide",
            "ozone",
            "nitrogen_dioxide",
            "aerosol_optical_depth",
            "dust",
            "us_aqi",
        ]
    ].copy()

    stg_weather = clean_weather[
        [
            "location_id",
            "date",
            "temperature_2m",
            "relative_humidity_2m",
            "rain",
            "surface_pressure",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code",
            "sunshine_duration",
            "boundary_layer_height",
            "dew_point_2m",
            "is_day",
        ]
    ].copy()

    stg_geocoding = location_summary[
        [
            "location_id",
            "location_name",
            "location_latitude",
            "location_longitude",
            "location_timezone",
            "location_elevation",
            "location_population",
            "start_date",
            "end_date",
            "is_current",
        ]
    ].copy()

    _register_df(con, "stg_air_quality_df", stg_air_quality)
    _register_df(con, "stg_weather_df", stg_weather)
    _register_df(con, "stg_geocoding_df", stg_geocoding)
    _register_df(
        con,
        "time_source_df",
        pd.DataFrame(
            {
                "full_date": pd.concat(
                    [stg_air_quality["date"], stg_weather["date"]], ignore_index=True
                )
            }
        )
        .dropna()
        .drop_duplicates()
        .sort_values("full_date"),
    )

    weather_code_rows = []
    available_weather_codes = set(
        stg_weather["weather_code"].dropna().astype(int).tolist()
    )
    for code, (description, common) in WEATHER_CODE_LOOKUP.items():
        if code in available_weather_codes:
            weather_code_rows.append(
                {
                    "weather_code": code,
                    "weather_description": description,
                    "weather_common": common,
                }
            )
    weather_code_lookup_df = pd.DataFrame(weather_code_rows)
    _register_df(con, "weather_code_lookup_df", weather_code_lookup_df)

    for relation in ["weather_code_lookup"]:
        _drop_relation(con, MAIN_SCHEMA, relation)
    for relation in ["stg_air_quality", "stg_weather", "stg_geocoding"]:
        _drop_relation(con, STAGING_SCHEMA, relation)
    for relation in ["snapshot_location"]:
        _drop_relation(con, SNAPSHOTS_SCHEMA, relation)
    for relation in [
        "dim_location",
        "dim_time",
        "dim_weather_code",
        "dim_aqi_category",
        "fact_aqi",
        "fact_weather",
    ]:
        _drop_relation(con, MARTS_SCHEMA, relation)

    con.execute(
        f"create or replace table {MAIN_SCHEMA}.weather_code_lookup as select * from weather_code_lookup_df"
    )
    con.execute(
        f"create or replace table {STAGING_SCHEMA}.stg_air_quality as select * from stg_air_quality_df"
    )
    con.execute(
        f"create or replace table {STAGING_SCHEMA}.stg_weather as select * from stg_weather_df"
    )
    con.execute(
        f"create or replace table {STAGING_SCHEMA}.stg_geocoding as select * from stg_geocoding_df"
    )
    con.execute(
        f"create or replace table {SNAPSHOTS_SCHEMA}.snapshot_location as select * from stg_geocoding_df"
    )
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.dim_location as
        select
            row_number() over (order by location_id) as location_key,
            location_id,
            location_name,
            location_latitude,
            location_longitude,
            location_timezone,
            location_elevation,
            location_population,
            cast(start_date as date) as start_date,
            cast(end_date as date) as end_date,
            is_current
        from {SNAPSHOTS_SCHEMA}.snapshot_location
        """)
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.dim_time as
        select distinct
            cast(strftime(full_date, '%Y%m%d%H') as bigint) as time_key,
            cast(full_date as timestamp) as full_date,
            hour(full_date) as hour,
            day(full_date) as day,
            month(full_date) as month,
            year(full_date) as year,
            quarter(full_date) as quarter,
            dayname(full_date) as day_of_week,
            weekofyear(full_date) as week_of_year,
            hour(full_date) between 6 and 17 as is_day
        from time_source_df
        """)
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.dim_weather_code as
        select
            row_number() over (order by weather_code) as weather_key,
            weather_code,
            weather_description,
            weather_common
        from weather_code_lookup_df
        """)
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.dim_aqi_category as
        select
            aqi_key,
            aqi_category,
            aqi_min,
            aqi_max,
            aqi_description
        from (
            values
                (1, 'good', 0, 50, 'air quality is satisfactory, and air pollution poses little or no risk.'),
                (2, 'moderate', 51, 100, 'air quality is acceptable. however, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.'),
                (3, 'unhealthy for sensitive groups', 101, 150, 'members of sensitive groups may experience health effects. the general public is less likely to be affected.'),
                (4, 'unhealthy', 151, 200, 'some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.'),
                (5, 'very unhealthy', 201, 300, 'health alert: the risk of health effects is increased for everyone.'),
                (6, 'hazardous', 301, 9999, 'health warning of emergency conditions: everyone is more likely to be affected.')
        ) as t(aqi_key, aqi_category, aqi_min, aqi_max, aqi_description)
        """)
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.fact_aqi as
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
        from {STAGING_SCHEMA}.stg_air_quality a
        join {MARTS_SCHEMA}.dim_time t on cast(strftime(a.date, '%Y%m%d%H') as bigint) = t.time_key
        join {MARTS_SCHEMA}.dim_location l on a.location_id = l.location_id and l.is_current = true
        left join {MARTS_SCHEMA}.dim_aqi_category c on a.us_aqi between c.aqi_min and c.aqi_max
        """)
    con.execute(f"""
        create or replace table {MARTS_SCHEMA}.fact_weather as
        select
            t.time_key,
            l.location_key,
            wc.weather_key,
            w.temperature_2m,
            w.relative_humidity_2m,
            w.rain,
            w.surface_pressure,
            w.cloud_cover,
            w.wind_speed_10m,
            w.wind_direction_10m,
            w.sunshine_duration,
            w.boundary_layer_height,
            w.dew_point_2m
        from {STAGING_SCHEMA}.stg_weather w
        join {MARTS_SCHEMA}.dim_time t on cast(strftime(w.date, '%Y%m%d%H') as bigint) = t.time_key
        join {MARTS_SCHEMA}.dim_location l on w.location_id = l.location_id and l.is_current = true
        join {MARTS_SCHEMA}.dim_weather_code wc on w.weather_code = wc.weather_code
        """)

    logger.info(f"DuckDB tables created successfully")

    return con


if __name__ == "__main__":
    load_to_duckdb()
