from pathlib import Path
import duckdb
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
database_path = PROJECT_ROOT / "data_warehouse.duckdb"

logger = get_logger(__name__, "config")


def config_dw() -> None:
    if database_path.exists():
        database_path.unlink()
    conn = duckdb.connect(database=str(database_path))
    conn.close()
    logger.info(f"[Config] Successfully created DuckDB database at {database_path}")


if __name__ == "__main__":
    config_dw()
