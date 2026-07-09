import subprocess
import sys
from pathlib import Path

from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_PROJECT_DIR = PROJECT_ROOT / "src" / "elt" / "transform"
LOGS_DIR = PROJECT_ROOT / "logs"

logger = get_logger(__name__, "elt")


def _run_dbt(command: list[str]) -> bool:

    full_command = [str(arg) for arg in (command + ["--log-path", LOGS_DIR])]
    logger.info(f"[Transform] Running: {' '.join(full_command)}")

    process = subprocess.Popen(
        full_command,
        cwd=DBT_PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()

    if process.returncode != 0:
        logger.error(
            f"[Transform] FAILED: {' '.join(full_command)} (exit code {process.returncode})"
        )
        return False

    logger.info(f"[Transform] SUCCESS: {' '.join(full_command)}")
    return True


def transform() -> bool:
    """
    Run the entire dbt Transform pipeline in the exact order of dependencies:
        1. dbt debug                    :Validate DuckDB connection + profiles.yml configuration
        2. dbt seed                     :Load lookup tables (weather_code_lookup.csv) into DuckDB
        3. dbt snapshot                 :Apply SCD Type 2 for dim_location (detect geocoding changes)
        4. dbt run --select staging     :Build staging views from local Parquet files
        5. dbt run --select marts       :Build 4 Dim + 2 Fact tables in warehouse.duckdb
        6. dbt test                     :Validate

    Strict execution order matters:
        - seed     must run before snapshot/run (dim_weather_code depends on seeds)
        - snapshot must run before marts (dim_location reads from snapshot_location)
        - staging  must run before marts (fact_* JOIN with stg_*)

    Halt immediately at the first failed step and do not proceed to subsequent steps
    if upstream data is invalid, preventing error propagation into gold layers.

    Returns:
        True if the entire pipeline succeeds, False if any step fails.
    """
    steps = [
        (["dbt", "debug"], "Validate configuration"),
        (["dbt", "seed"], "Load seed lookup"),
        (["dbt", "snapshot"], "Snapshot SCD Type 2"),
        (["dbt", "run", "--select", "staging"], "Build staging"),
        (["dbt", "run", "--select", "marts"], "Build data marts"),
        (["dbt", "test"], "Validate everything"),
    ]

    for command, description in steps:
        logger.info(f"[Transform] {description}")
        success = _run_dbt(command)

        if not success:
            logger.error(
                f"[Transform] Pipeline stopped at step '{description}'. "
                f"Check the log above to find the cause."
            )
            return False

    logger.info("[Transform] All steps completed successfully")
    return True


if __name__ == "__main__":
    success = transform()
    sys.exit(0 if success else 1)
