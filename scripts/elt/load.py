from pathlib import Path
import logging
import sys
from elt.load import load_air_quality, load_weather
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"

logger = get_logger(__name__, "elt")


def main() -> None:
    logger.info("[Load] Start")
    load_air_quality()
    load_weather()
    logger.info("[Load] Finished")


if __name__ == "__main__":
    main()
