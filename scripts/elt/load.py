from pathlib import Path
import logging
import sys
from elt.load import convert_db_to_parquet, convert_api_to_parquet, load_to_hdfs
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"

logger = get_logger(__name__, "backend")


def main() -> None:
    logger.info("[Load] ETL Start")
    convert_db_to_parquet()
    convert_api_to_parquet()
    load_to_hdfs()
    logger.info("[Load] ETL Finished")


if __name__ == "__main__":
    main()
