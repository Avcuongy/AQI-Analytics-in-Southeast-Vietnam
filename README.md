# Setup

## Initial:

```bash
git clone https://github.com/Avcuongy/AQI-Analytics-in-Southeast-Vietnam.git

cd AQI-Analytics-in-Southeast-Vietnam

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

pip install -e .

python scripts/config.py
```

## Note:

Crawl historical for testing:

```bash
# Local
python scripts/all/dowloader.py
python scripts/all/load_to_storage.py
python scripts/all/sync_duckdb_to_postgres.py
```

```bash
# Docker
docker exec -it airflow-scheduler python /opt/airflow/project/scripts/all/dowloader.py
docker exec -it airflow-scheduler python /opt/airflow/project/scripts/all/load_to_duckdb.py
docker exec -it airflow-scheduler python /opt/airflow/project/src/elt/sync_duckdb_to_postgres.py
```
