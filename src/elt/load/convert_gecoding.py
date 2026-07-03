import os
from pathlib import Path

import numpy as np
import pandas as pd
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "geocoding"
STAGING_DIR = DATA_DIR / "staging" / "geocoding"

logger = get_logger(__name__, "elt")

GEOCODING_DTYPES = {
    "id": "Int64",
    "name": "string",
    "latitude": "float64",
    "longitude": "float64",
    "timezone": "string",
    "elevation": "float64",
    "population": "Int64",
    "country": "string",
    "admin1": "string",
    "admin2": "string",
    "admin3": "string",
    "admin4": "string",
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


def convert_geocoding(local_file: Path = None) -> Path:
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
            dtype=GEOCODING_DTYPES,
        )

        invalid_mask = df["id"].isna() | df["name"].isna()
        invalid_rows = int(invalid_mask.sum())
        if invalid_rows > 0:
            logger.warning(
                f"[Load] {invalid_rows} invalid rows found in {local_file}, they will be dropped."
            )
            df = df[~invalid_mask]

        os.makedirs(STAGING_DIR, exist_ok=True)
        output_file = STAGING_DIR / local_file.with_suffix(".parquet").name

        df.to_parquet(output_file, index=False, engine="pyarrow")

        logger.info(f"[Load] Successfully converted {local_file} to {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"[Load] Error occurred while converting {local_file}: {e}")
        return None


if __name__ == "__main__":
    convert_geocoding()
