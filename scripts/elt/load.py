from pathlib import Path
import logging
import sys
from elt.load import convert_air_quality, convert_weather, load_to_s3
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"

logger = get_logger(__name__, "elt")


def main() -> None:
    logger.info("[Load] Start")
    convert_air_quality()
    convert_weather()
    load_to_s3
    logger.info("[Load] Finished")


if __name__ == "__main__":
    main()
