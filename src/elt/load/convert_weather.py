import os
from pathlib import Path

import numpy as np
import pandas as pd
from utils.logger import get_logger
from utils.path_helper import get_partition_folder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "weather"
STAGING_DIR = DATA_DIR / "staging" / "weather"

logger = get_logger(__name__, "elt")

WEATHER_DTYPES = {
    "location_id": "Int32",
    "location_name": "string",
    "temperature_2m": "float64",
    "relative_humidity_2m": "float64",
    "rain": "float64",
    "surface_pressure": "float64",
    "cloud_cover": "float64",
    "wind_speed_10m": "float64",
    "wind_direction_10m": "float64",
    "weather_code": "Int32",
    "sunshine_duration": "float64",
    "boundary_layer_height": "float64",
    "dew_point_2m": "float64",
    "is_day": "Int32",
}


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


def convert_weather(local_file: Path = None) -> Path:
    if local_file is None:
        local_file = _get_latest_file_in_directory(RAW_DIR, ".csv")
        if local_file is None:
            candidates = list(RAW_DIR.rglob("*.csv"))
            if not candidates:
                logger.warning(f"[Load] Not found any .csv files in {RAW_DIR}")
                return None
            local_file = max(candidates, key=os.path.getmtime)

    if not local_file.exists():
        logger.error(f"[Load] File does not exist: {local_file}")
        return None

    try:
        df = pd.read_csv(
            local_file,
            dtype=WEATHER_DTYPES,
            parse_dates=["date"],
        )

        df["is_day"] = df["is_day"] == 1

        invalid_mask = df["location_id"].isna() | df["date"].isna()
        invalid_rows = int(invalid_mask.sum())
        if invalid_rows > 0:
            logger.warning(
                f"[Load] {invalid_rows} invalid rows found in {local_file}, they will be dropped."
            )
            df = df[~invalid_mask]

        reference_time = df["date"].iloc[0].to_pydatetime()

        output_folder = get_partition_folder(STAGING_DIR, reference_time)
        output_file = output_folder / local_file.with_suffix(".parquet").name

        df.to_parquet(output_file, index=False, engine="pyarrow")

        logger.info(f"[Load] Successfully converted {local_file} to {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"[Load] Error occurred while converting {local_file}: {e}")
        return None


if __name__ == "__main__":
    convert_weather()
