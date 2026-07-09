from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_PATH = "/opt/airflow/project"
PYTHON_EXEC = f"export PYTHONPATH={PROJECT_PATH}:{PROJECT_PATH}/src && python"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="elt",
    default_args=default_args,
    description="ELT",
    schedule="0 1 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["warehouse", "elt"],
) as dag:

    task_extract_1 = BashOperator(
        task_id="crawl_geocoding",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/extract/crawl_geocoding.py",
    )

    task_extract_2 = BashOperator(
        task_id="crawl_weather",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/extract/crawl_weather.py",
    )

    task_extract_3 = BashOperator(
        task_id="crawl_air_quality",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/extract/crawl_air_quality.py",
    )

    task_load_1 = BashOperator(
        task_id="convert_weather",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/convert_weather.py",
    )

    task_load_2 = BashOperator(
        task_id="convert_air_quality",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/convert_air_quality.py",
    )

    task_load_3 = BashOperator(
        task_id="load_to_s3",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/load_to_s3.py",
    )

    task_transform = BashOperator(
        task_id="transform_dbt",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/transform/transform.py",
    )

    (
        task_extract_1
        >> [task_extract_2, task_extract_3]
        >> [task_load_1, task_load_2]
        >> task_load_3
        >> task_transform
    )
