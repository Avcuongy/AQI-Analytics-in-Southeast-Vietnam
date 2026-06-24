import datetime
from pathlib import Path


def get_partition_folder(
    base_dir: Path, reference_time: datetime.datetime = None
) -> Path:
    """Defines the partition folder based on the provided base directory and reference time.

    Args:
        base_dir (Path): The base directory where the partitioned folders will be created.
        reference_time (datetime.datetime, optional): The time to use for determining the partition folder. Defaults to None.

    Returns:
        Path: The path to the partition folder.
    """
    if reference_time is None:
        reference_time = datetime.datetime.now()

    year = reference_time.strftime("%Y")
    month = reference_time.strftime("%m")

    folder = base_dir / f"year={year}" / f"month={month}"
    folder.mkdir(parents=True, exist_ok=True)

    return folder
