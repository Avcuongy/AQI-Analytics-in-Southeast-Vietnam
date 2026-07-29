import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_PATH = "/opt/airflow/project"
DBT_PROJECT_PATH = f"{PROJECT_PATH}/src/elt/transform"
DBT_BIN = "/opt/airflow/dbt_venv/bin/dbt"
PYTHON_ENV = {
    **os.environ,
    "PYTHONPATH": f"{PROJECT_PATH}:{PROJECT_PATH}/src",
    "PROJECT_ROOT": PROJECT_PATH,
}

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=30),
}

with DAG(
    dag_id="elt",
    default_args=default_args,
    description="ELT",
    schedule="0 1 * * *",
    start_date=datetime(2026, 7, 7),
    catchup=False,
    tags=["warehouse", "elt"],
) as dag:

    task_extract_1 = BashOperator(
        task_id="crawl_geocoding",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/extract/crawl_geocoding.py",
        env=PYTHON_ENV,
    )

    task_extract_2 = BashOperator(
        task_id="crawl_weather",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/extract/crawl_weather.py",
        env=PYTHON_ENV,
    )

    task_extract_3 = BashOperator(
        task_id="crawl_air_quality",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/extract/crawl_air_quality.py",
        env=PYTHON_ENV,
    )

    task_load_1 = BashOperator(
        task_id="convert_weather",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/load/convert_weather.py",
        env=PYTHON_ENV,
    )

    task_load_2 = BashOperator(
        task_id="convert_air_quality",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/load/convert_air_quality.py",
        env=PYTHON_ENV,
    )

    task_load_3 = BashOperator(
        task_id="load_to_storage",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/load/load_to_storage.py",
        env=PYTHON_ENV,
    )

    task_transform = BashOperator(
        task_id="transform_dbt",
        bash_command=f"{DBT_BIN} run --project-dir {DBT_PROJECT_PATH} --profiles-dir {DBT_PROJECT_PATH}",
        env=PYTHON_ENV,
    )

    task_sync_duckdb_to_postgres = BashOperator(
        task_id="sync_duckdb_to_postgres",
        bash_command=f"cd {PROJECT_PATH} && python src/elt/sync_duckdb_to_postgres.py",
        env=PYTHON_ENV,
    )

    task_extract_1 >> [task_extract_2, task_extract_3]

    task_extract_2 >> task_load_1
    task_extract_3 >> task_load_2

    (
        [task_load_1, task_load_2]
        >> task_load_3
        >> task_transform
        >> task_sync_duckdb_to_postgres
    )
