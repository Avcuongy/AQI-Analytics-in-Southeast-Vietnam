from pathlib import Path
import os
import duckdb
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DUCKDB_PATH = PROJECT_ROOT / "data_warehouse.duckdb"
PG_USER = os.getenv("POSTGRES_USER", "admin")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
PG_HOST = "postgres"  # "localhost" if running locally, "postgres" if running in docker-compose
PG_PORT = "5432"
PG_DB = "airflow"


def sync_duckdb_to_postgres():
    if not DUCKDB_PATH.exists():
        print(f"Not found: {DUCKDB_PATH}")
        return

    conn = duckdb.connect(str(DUCKDB_PATH))

    conn.execute("INSTALL postgres;")
    conn.execute("LOAD postgres;")

    pg_conn_str = f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={PG_PASSWORD}"
    conn.execute(f"ATTACH '{pg_conn_str}' AS pg_db (TYPE POSTGRES);")

    conn.execute("CREATE SCHEMA IF NOT EXISTS pg_db.main_marts;")

    tables_df = conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main_marts';
    """).df()

    table_names = tables_df["table_name"].tolist()

    if not table_names:
        print("Not found any tables in schema")
        conn.close()
        return

    for table in table_names:
        conn.execute(f"DROP TABLE IF EXISTS pg_db.main_marts.{table};")
        conn.execute(f"""
            CREATE TABLE pg_db.main_marts.{table} AS 
            SELECT * FROM data_warehouse.main_marts.{table};
        """)

    conn.close()

    print("Sync completed successfully")


if __name__ == "__main__":
    sync_duckdb_to_postgres()
