import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
STAGING_DIR = DATA_DIR / "staging"
AQI_DIR = STAGING_DIR / "air_quality"
WEATHER_DIR = STAGING_DIR / "weather"

MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL")
MINIO_REGION = os.getenv("MINIO_REGION")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

logger = get_logger(__name__, "elt")


def _get_latest_file_in_directory(directory: Path, extension: str = ".parquet"):
    if not directory.exists() or not directory.is_dir():
        return None
    files = [f for f in directory.glob(f"*{extension}") if not f.name.startswith(".")]
    if not files:
        return None
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file


# ĐÃ SỬA: Loại bỏ tiền tố "data/"
def _build_s3_key(local_path: Path) -> str:
    try:
        relative_path = local_path.relative_to(STAGING_DIR)
        return relative_path.as_posix()
    except ValueError:
        return f"{local_path.parent.name}/{local_path.name}"


def _get_s3_client():
    """
    Create and return a boto3 S3 client configured for MinIO. Returns None if connection fails.
    """

    use_ssl_env = str(MINIO_USE_SSL).strip().lower()
    use_ssl_bool = use_ssl_env == "true"
    protocol = "https" if use_ssl_bool else "http"
    endpoint_url = f"{protocol}://{MINIO_ENDPOINT}"

    try:
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name=MINIO_REGION,
            use_ssl=use_ssl_bool,
        )
        client.head_bucket(Bucket=MINIO_BUCKET_NAME)
        return client
    except NoCredentialsError:
        logger.error("[Load] Not found MinIO/S3 credentials")
        return None
    except ClientError as e:
        logger.error(
            f"[Load] Unable to connect to bucket '{MINIO_BUCKET_NAME}' at {endpoint_url}: {e.response['Error']['Code']}"
        )
        return None
    except Exception as e:
        logger.error(f"[Load] Unexpected error connecting to MinIO: {e}")
        return None


def load_to_s3(s3_client, target_dir: Path, local_file: Path = None) -> bool:
    """
    Upload a local file to S3/MinIO. If local_file is None, find the latest .parquet file in target_dir.
    """
    if s3_client is None:
        logger.error("[Load] s3_client is None, connection to MinIO failed earlier.")
        return False

    if not isinstance(target_dir, Path):
        target_dir = Path(target_dir)

    if local_file is None:
        if not target_dir.exists():
            logger.error(f"[Load] Target directory not found: {target_dir}")
            return False

        local_file = _get_latest_file_in_directory(target_dir, ".parquet")

        if local_file is None:
            candidates = list(target_dir.rglob("*.parquet"))
            if not candidates:
                logger.warning(
                    f"[Load] Not found any .parquet files in {target_dir} or its subdirectories."
                )
                return False
            local_file = max(candidates, key=lambda f: f.stat().st_mtime)
    else:
        if not isinstance(local_file, Path):
            local_file = Path(local_file)

    if not local_file.exists():
        logger.error(f"[Load] File does not exist: {local_file}")
        return False

    s3_key = _build_s3_key(local_file)

    try:
        s3_client.upload_file(
            Filename=str(local_file),
            Bucket=MINIO_BUCKET_NAME,
            Key=s3_key,
        )
        logger.info(
            f"[Load] Upload successful: {local_file.name} to s3://{MINIO_BUCKET_NAME}/{s3_key}"
        )
        return True
    except ClientError as e:
        logger.error(
            f"[Load] Upload failed for {local_file.name}: {e.response['Error']['Code']}"
        )
        return False


if __name__ == "__main__":
    if not MINIO_BUCKET_NAME:
        logger.error("[Load] MINIO_BUCKET_NAME is not configured.")
    else:
        s3_client = _get_s3_client()
        if s3_client is not None:
            load_to_s3(s3_client, target_dir=AQI_DIR)
            load_to_s3(s3_client, target_dir=WEATHER_DIR)
