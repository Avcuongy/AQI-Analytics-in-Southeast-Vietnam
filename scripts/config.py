from utils.logger import get_logger
from utils.setup_folder import setup_folder
# from utils.config_dw import config_dw
from elt.extract import crawl_geocoding
import warnings

warnings.filterwarnings("ignore")

logger = get_logger(__name__, "config")


def main() -> None:
    logger.info("[Config] Config project folders")
    setup_folder()
    # config_dw()
    crawl_geocoding()
    logger.info("[Config] Config project is complete")


if __name__ == "__main__":
    main()
