from pathlib import Path
import logging
import sys
from elt.transform import
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"

logger = get_logger(__name__, "backend")


def main() -> None:
    logger.info("[Transform] Start")

    logger.info("[Transform] Finished")


if __name__ == "__main__":
    main()
