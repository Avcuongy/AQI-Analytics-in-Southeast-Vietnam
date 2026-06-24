import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
WEATHER_DIR = RAW_DIR / "weather"

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("AWS_DEFAULT_REGION")

logger = get_logger(__name__, "elt")


def _get_latest_file_in_directory(directory, extension):
    if not os.path.exists(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension) and not f.startswith(".")
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return Path(latest_file)


def _build_s3_key(local_path: Path) -> str:
    relative_path = local_path.relative_to(DATA_DIR)
    return relative_path.as_posix()


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


def load_weather(local_file: Path = None) -> bool:
    if not S3_BUCKET:
        logger.error("[Load] Not configured S3_BUCKET_NAME")
        return False

    if local_file is None:
        local_file = _get_latest_file_in_directory(WEATHER_DIR, ".csv")
        if local_file is None:
            candidates = list(WEATHER_DIR.rglob("*.csv"))
            if not candidates:
                logger.warning(f"[Load] Not found any .csv files in {WEATHER_DIR}")
                return False
            local_file = max(candidates, key=os.path.getmtime)

    if not local_file.exists():
        logger.error(f"[Load] File not found: {local_file}")
        return False

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
    load_weather()
