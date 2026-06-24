import datetime
import os
from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from utils.logger import get_logger
from utils.path_helper import get_partition_folder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

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


def crawl_air_quality():
    """Crawls 24-hour historical air quality data for yesterday across all locations."""
    try:
        locations = _get_location()
    except Exception as e:
        logger.error(f"[Extract] Failed to retrieve location list: {e}")
        return

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    logger.info(
        f"[Extract] Proceeding to crawl air quality data for date: {yesterday_str}"
    )

    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
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
        responses = openmeteo.weather_api(URL, params=params)

        all_aqi_records = []

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

            all_aqi_records.append(pd.DataFrame(data=hourly_data))

        if all_aqi_records:
            final_df = pd.concat(all_aqi_records, ignore_index=True)

            output_folder = get_partition_folder(RAW_DIR / "air_quality", yesterday)

            output_file = (
                output_folder / f"air_quality_{yesterday_str.replace('-', '_')}.csv"
            )
            final_df.to_csv(output_file, index=False)

            logger.info(
                f"[Extract] Successfully crawled {len(final_df)} AQI records | Saved at {output_file}"
            )
        else:
            logger.warning(
                "[Extract] Execution finished but zero AQI records were collected."
            )

    except Exception as e:
        logger.error(
            f"[Extract] Critical error handling Open-Meteo AQI payload processing: {e}"
        )


if __name__ == "__main__":
    crawl_air_quality()
