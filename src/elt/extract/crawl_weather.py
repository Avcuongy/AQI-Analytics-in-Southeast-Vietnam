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

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
URL = "https://archive-api.open-meteo.com/v1/archive"

logger = get_logger(__name__, "elt")


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


def crawl_weather():
    """Crawls 24-hour historical weather data for yesterday across all locations."""
    try:
        locations = _get_location()
    except Exception as e:
        logger.error(f"[Extract] Failed to retrieve location list: {e}")
        return

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    logger.info(f"[Extract] Proceeding to crawl weather data for date: {yesterday_str}")

    cache_session = requests_cache.CachedSession(".cache", expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    latitudes = [loc["latitude"] for loc in locations]
    longitudes = [loc["longitude"] for loc in locations]

    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "start_date": yesterday_str,
        "end_date": yesterday_str,
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
        responses = openmeteo.weather_api(URL, params=params)

        all_weather_records = []

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

            all_weather_records.append(pd.DataFrame(data=hourly_data))

        if all_weather_records:
            final_df = pd.concat(all_weather_records, ignore_index=True)

            (RAW_DIR / "weather").mkdir(parents=True, exist_ok=True)

            output_file = (
                RAW_DIR / "weather" / f"weather_{yesterday_str.replace('-', '_')}.csv"
            )
            final_df.to_csv(output_file, index=False)

            logger.info(
                f"[Extract] Successfully crawled {len(final_df)} weather records | Saved at {output_file}"
            )
        else:
            logger.warning(
                "[Extract] Execution finished but zero weather records were collected."
            )

    except Exception as e:
        logger.error(
            f"[Extract] Critical error handling Open-Meteo payload processing: {e}"
        )


if __name__ == "__main__":
    crawl_weather()
