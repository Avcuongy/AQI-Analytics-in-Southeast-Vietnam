from pathlib import Path
import sys
import logging
from elt.extract import crawl_geocoding, crawl_air_quality, crawl_weather
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")


logger = get_logger(__name__, "elt")


def main() -> None:
    logger.info("[Extract] Start")
    crawl_geocoding()
    crawl_weather()
    crawl_air_quality()
    logger.info("[Extract] Finished")


if __name__ == "__main__":
    main()
