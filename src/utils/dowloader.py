import datetime
import json
import logging
import os
import sys
import time
from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
HISTORICAL_DIR = RAW_DIR / "historical"

logger = get_logger(__name__, "other")


def _get_latest_file_in_directory(directory, extension):
    if not os.path.exists(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension) and not f.startswith(".")
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return Path(latest_file)


def _get_location() -> list[dict]:
    geocoding_dir = RAW_DIR / "geocoding"
    latest_file = _get_latest_file_in_directory(geocoding_dir, ".csv")
    if not latest_file:
        raise FileNotFoundError(f"No .csv files found at directory: {geocoding_dir}")
    df = pd.read_csv(latest_file)
    required_cols = ["id", "name", "latitude", "longitude"]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(
                f"File {latest_file.name} is missing the required column: '{col}'"
            )

    return df[required_cols].to_dict(orient="records")


def _get_months_in_year(year: int):
    months = []
    for month in range(1, 13):
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year, 12, 31)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        months.append(
            (month, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        )
    return months


def crawl_air_quality(year: int):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    try:
        locations = _get_location()
    except Exception as e:
        logger.error(f"[Extract - AQI] Failed to retrieve location list: {e}")
        return

    logger.info(
        f"[Extract - AQI] Starting air quality crawl for the entire year: {year} (01/01 -> 31/12)"
    )

    cache_session = requests_cache.CachedSession(".cache_aqi", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    latitudes = [loc["latitude"] for loc in locations]
    longitudes = [loc["longitude"] for loc in locations]

    all_year_records = []
    months = _get_months_in_year(year)

    for month_idx, start_str, end_str in months:
        logger.info(
            f"[Extract - AQI] Fetching month {month_idx}/{year} ({start_str} -> {end_str})"
        )

        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "start_date": start_str,
            "end_date": end_str,
            "hourly": [
                "pm10",
                "pm2_5",
                "carbon_monoxide",
                "sulphur_dioxide",
                "ozone",
                "nitrogen_dioxide",
                "aerosol_optical_depth",
                "dust",
                "us_aqi_pm2_5",
                "us_aqi_pm10",
                "us_aqi_nitrogen_dioxide",
                "us_aqi_carbon_monoxide",
                "us_aqi_ozone",
                "us_aqi_sulphur_dioxide",
                "us_aqi",
            ],
            "timezone": "Asia/Bangkok",
        }

        try:
            responses = openmeteo.weather_api(url, params=params)

            for i, response in enumerate(responses):
                location_info = locations[i]
                hourly = response.Hourly()

                utc_offset = response.UtcOffsetSeconds()

                date_range = pd.date_range(
                    start=pd.to_datetime(hourly.Time() + utc_offset, unit="s"),
                    end=pd.to_datetime(hourly.TimeEnd() + utc_offset, unit="s"),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                )

                hourly_data = {
                    "location_id": location_info["id"],
                    "location_name": location_info["name"],
                    "date": date_range,
                    "pm10": hourly.Variables(0).ValuesAsNumpy(),
                    "pm2_5": hourly.Variables(1).ValuesAsNumpy(),
                    "carbon_monoxide": hourly.Variables(2).ValuesAsNumpy(),
                    "sulphur_dioxide": hourly.Variables(3).ValuesAsNumpy(),
                    "ozone": hourly.Variables(4).ValuesAsNumpy(),
                    "nitrogen_dioxide": hourly.Variables(5).ValuesAsNumpy(),
                    "aerosol_optical_depth": hourly.Variables(6).ValuesAsNumpy(),
                    "dust": hourly.Variables(7).ValuesAsNumpy(),
                    "us_aqi_pm2_5": hourly.Variables(8).ValuesAsNumpy(),
                    "us_aqi_pm10": hourly.Variables(9).ValuesAsNumpy(),
                    "us_aqi_nitrogen_dioxide": hourly.Variables(10).ValuesAsNumpy(),
                    "us_aqi_carbon_monoxide": hourly.Variables(11).ValuesAsNumpy(),
                    "us_aqi_ozone": hourly.Variables(12).ValuesAsNumpy(),
                    "us_aqi_sulphur_dioxide": hourly.Variables(13).ValuesAsNumpy(),
                    "us_aqi": hourly.Variables(14).ValuesAsNumpy(),
                }
                all_year_records.append(pd.DataFrame(data=hourly_data))

            time.sleep(0.5)

        except Exception as e:
            logger.error(
                f"[Extract - AQI] Error handling Open-Meteo AQI payload for month {month_idx}: {e}"
            )
            continue

    if all_year_records:
        final_df = pd.concat(all_year_records, ignore_index=True)
        (HISTORICAL_DIR / "air_quality").mkdir(parents=True, exist_ok=True)
        output_file = HISTORICAL_DIR / "air_quality" / f"air_quality_year_{year}.csv"

        final_df.to_csv(output_file, index=False)
        logger.info(
            f"[Extract - AQI] Successfully saved {len(final_df)} records to CSV: {output_file}"
        )
    else:
        logger.warning(
            f"[Extract - AQI] Completed execution but collected zero records for year {year}."
        )


def crawl_weather(year: int):
    """Crawls full-year historical weather archive data partitioned by month for all locations and exports to CSV."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    try:
        locations = _get_location()
    except Exception as e:
        logger.error(f"[Extract - Weather] Failed to retrieve location list: {e}")
        return

    logger.info(
        f"[Extract - Weather] Starting weather archive crawl for the entire year: {year} (01/01 -> 31/12)"
    )

    cache_session = requests_cache.CachedSession(".cache_weather", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    latitudes = [loc["latitude"] for loc in locations]
    longitudes = [loc["longitude"] for loc in locations]

    all_year_records = []
    months = _get_months_in_year(year)

    for month_idx, start_str, end_str in months:
        logger.info(
            f"[Extract - Weather] Fetching month {month_idx}/{year} ({start_str} -> {end_str})"
        )

        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "start_date": start_str,
            "end_date": end_str,
            "hourly": [
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
            ],
            "timezone": "Asia/Bangkok",
        }

        try:
            responses = openmeteo.weather_api(url, params=params)

            for i, response in enumerate(responses):
                location_info = locations[i]
                hourly = response.Hourly()

                utc_offset = response.UtcOffsetSeconds()

                date_range = pd.date_range(
                    start=pd.to_datetime(hourly.Time() + utc_offset, unit="s"),
                    end=pd.to_datetime(hourly.TimeEnd() + utc_offset, unit="s"),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                )

                hourly_data = {
                    "location_id": location_info["id"],
                    "location_name": location_info["name"],
                    "date": date_range,
                    "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
                    "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
                    "rain": hourly.Variables(2).ValuesAsNumpy(),
                    "surface_pressure": hourly.Variables(3).ValuesAsNumpy(),
                    "cloud_cover": hourly.Variables(4).ValuesAsNumpy(),
                    "wind_speed_10m": hourly.Variables(5).ValuesAsNumpy(),
                    "wind_direction_10m": hourly.Variables(6).ValuesAsNumpy(),
                    "weather_code": hourly.Variables(7).ValuesAsNumpy(),
                    "sunshine_duration": hourly.Variables(8).ValuesAsNumpy(),
                    "boundary_layer_height": hourly.Variables(9).ValuesAsNumpy(),
                    "dew_point_2m": hourly.Variables(10).ValuesAsNumpy(),
                }
                all_year_records.append(pd.DataFrame(data=hourly_data))

            time.sleep(0.5)

        except Exception as e:
            logger.error(
                f"[Extract - Weather] Error handling Open-Meteo Weather payload for month {month_idx}: {e}"
            )
            continue

    if all_year_records:
        final_df = pd.concat(all_year_records, ignore_index=True)
        (HISTORICAL_DIR / "weather").mkdir(parents=True, exist_ok=True)
        output_file = HISTORICAL_DIR / "weather" / f"weather_year_{year}.csv"

        final_df.to_csv(output_file, index=False)
        logger.info(
            f"[Extract - Weather] Successfully saved {len(final_df)} records to CSV: {output_file}"
        )
    else:
        logger.warning(
            f"[Extract - Weather] Completed execution but collected zero records for year {year}."
        )


if __name__ == "__main__":
    crawl_air_quality(year=2022)
    crawl_weather(year=2022)
