FROM apache/airflow:3.0.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN mkdir -p /opt/airflow/project && chown -R airflow:0 /opt/airflow/project

USER airflow

COPY requirements.txt /tmp/requirements.txt

ARG AIRFLOW_VERSION=3.0.0
ARG PYTHON_VERSION=3.12

RUN pip install --no-cache-dir \
    -r /tmp/requirements.txt \
    "apache-airflow-providers-fab" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

RUN python -m venv /opt/airflow/dbt_venv \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/airflow/dbt_venv/bin/pip install --no-cache-dir \
    dbt-core==1.10.0 \
    dbt-duckdb==1.8.0

ENV PYTHONPATH="/opt/airflow/project/src:/opt/airflow/project"