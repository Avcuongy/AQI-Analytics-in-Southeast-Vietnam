import datetime
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "geocoding"
LOCATIONS = [
    "ho chi minh",
    "bien hoa",
    "long khanh",
    "thu dau mot",
    "thuan an",
    "di an",
    "ba ria",
    "vung tau",
    "tay ninh",
    "dong xoai",
]

logger = get_logger(__name__, "elt")


def crawl_geocoding(
    locations: list = LOCATIONS,
    count: int = 3,
    filename="geocoding",
):
    """Crawls location geocoding data from the Open-Meteo API."""

    master_data = []

    if locations is None:
        logger.error("[Extract] No locations provided for crawling.")
        return

    for loc in locations:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={loc}&count={count}&format=json&language=en"
        try:
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()

                if "results" in data:
                    valid_location = None

                    for item in data["results"]:
                        if (
                            "population" in item
                            and item["population"] > 0
                            and item.get("country_code") == "VN"
                        ):
                            valid_location = item
                            break

                    if valid_location:
                        master_data.append(
                            {
                                "id": valid_location.get("id"),
                                "name": valid_location.get("name"),
                                "latitude": valid_location.get("latitude"),
                                "longitude": valid_location.get("longitude"),
                                "timezone": valid_location.get(
                                    "timezone", "Asia/Bangkok"
                                ),
                                "elevation": valid_location.get("elevation", 0),
                                "population": valid_location.get("population"),
                                "country": valid_location.get("country", "Vietnam"),
                                "admin1": valid_location.get("admin1", ""),
                                "admin2": valid_location.get("admin2", ""),
                                "admin3": valid_location.get("admin3", ""),
                                "admin4": valid_location.get("admin4", ""),
                            }
                        )
                    else:
                        logger.warning(
                            f"[Extract] No data with population found for location: {loc}"
                        )
                else:
                    logger.error(
                        f"[Extract] API returned no results for location: {loc}"
                    )
            else:
                logger.error(
                    f"[Extract] Failed to fetch data for {loc}. HTTP Status: {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"[Extract] Network error occurred while fetching {loc}: {e}")

        time.sleep(2)

    if master_data:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d")

        output_path = RAW_DIR / f"{filename}_{timestamp}.csv"

        df_location = pd.DataFrame(master_data)
        df_location.to_csv(output_path, index=False)
        logger.info(
            f"[Extract] Successfully crawled {len(master_data)} location records | Saved at {output_path}"
        )

        for idx, row in df_location.iterrows():
            logger.info(
                f"[Extract] Location: {row['name']:<18} | Latitude: {row['latitude']:<8.4f} | Longitude: {row['longitude']:<8.4f}"
            )
    else:
        logger.warning(
            "[Extract] No valid location data was collected. CSV file not created."
        )


if __name__ == "__main__":
    crawl_geocoding()
