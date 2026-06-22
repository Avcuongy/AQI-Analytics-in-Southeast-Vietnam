import os
from dotenv import load_dotenv

load_dotenv()

# API
SEC_API_KEY = os.getenv("SEC_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Airflow
AIRFLOW_UID = os.getenv("AIRFLOW_UID", "50000")
AIRFLOW_FERNET_KEY = os.getenv("AIRFLOW_FERNET_KEY")
AIRFLOW_JWT_SECRET = os.getenv("AIRFLOW_JWT_SECRET")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")

# Postgres
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")

# Hadoop
HDFS_USER = os.getenv("HDFS_USER", "hdfs")
HDFS_DEFAULT_FS = os.getenv("HDFS_DEFAULT_FS", "hdfs://localhost:9000")
HDFS_BASE_DIR = os.getenv("HDFS_BASE_DIR", "/data_lake")
