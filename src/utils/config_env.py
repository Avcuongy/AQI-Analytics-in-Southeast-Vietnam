import os
from dotenv import load_dotenv

load_dotenv()

# Airflow
AIRFLOW_UID = os.getenv("AIRFLOW_UID", "50000")
AIRFLOW_FERNET_KEY = os.getenv("AIRFLOW_FERNET_KEY")
AIRFLOW_JWT_SECRET = os.getenv("AIRFLOW_JWT_SECRET")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD", "admin")

# Postgres
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")

# AWS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
