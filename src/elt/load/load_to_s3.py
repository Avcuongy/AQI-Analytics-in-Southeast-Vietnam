import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
AQI_DIR = RAW_DIR / "air_quality"
WEATHER_DIR = RAW_DIR / "weather"

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("AWS_DEFAULT_REGION")

logger = get_logger(__name__, "elt")


def _get_latest_file_in_directory(directory: Path, extension: str = ".csv"):
    if not directory.exists() or not directory.is_dir():
        return None
    files = [f for f in directory.glob(f"*{extension}") if not f.name.startswith(".")]
    if not files:
        return None
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file


def _build_s3_key(local_path: Path) -> str:
    try:
        relative_path = local_path.relative_to(RAW_DIR)
        return f"data/{relative_path.as_posix()}"
    except ValueError:
        return f"data/{local_path.parent.name}/{local_path.name}"


def _get_s3_client():
    try:
        client = boto3.client("s3", region_name=S3_REGION)
        client.head_bucket(Bucket=S3_BUCKET)
        return client
    except NoCredentialsError:
        logger.error("[Load] Not found AWS credentials")
        return None
    except ClientError as e:
        logger.error(
            f"[Load] Not able to connect to bucket '{S3_BUCKET}': {e.response['Error']['Code']}"
        )
        return None


def load_to_s3(target_dir: Path) -> bool:
    if not S3_BUCKET:
        logger.error("[Load] Not configured S3_BUCKET_NAME")
        return False

    if not isinstance(target_dir, Path):
        target_dir = Path(target_dir)

    if not target_dir.exists():
        logger.error(f"[Load] Target directory not found: {target_dir}")
        return False

    local_file = _get_latest_file_in_directory(target_dir, ".csv")

    if local_file is None:
        candidates = list(target_dir.rglob("*.csv"))
        if not candidates:
            logger.warning(
                f"[Load] Not found any .csv files in {target_dir} or its subdirectories."
            )
            return False
        local_file = max(candidates, key=lambda f: f.stat().st_mtime)

    s3_client = _get_s3_client()
    if s3_client is None:
        return False

    s3_key = _build_s3_key(local_file)

    try:
        s3_client.upload_file(
            Filename=str(local_file),
            Bucket=S3_BUCKET,
            Key=s3_key,
        )
        logger.info(
            f"[Load] Upload successful: {local_file.name} to s3://{S3_BUCKET}/{s3_key}"
        )
        return True
    except ClientError as e:
        logger.error(
            f"[Load] Upload failed for {local_file.name}: {e.response['Error']['Code']}"
        )
        return False


if __name__ == "__main__":
    load_to_s3(target_dir=AQI_DIR)
    load_to_s3(target_dir=WEATHER_DIR)
