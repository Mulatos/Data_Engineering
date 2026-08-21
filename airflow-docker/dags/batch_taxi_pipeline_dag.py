from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from reader import read_data
from validator import validate_data, backup_validate
from processor import process_data
from writer import write_local, write_azure
import config

def task_read(**kwargs):
    df = read_data(config.INPUT_FILE)
    df.to_parquet("/tmp/raw.parquet")

def task_validate(**kwargs):
    import pandas as pd
    df = pd.read_parquet("/tmp/raw.parquet")
    valid_df, invalid_df, report = validate_data(df, config.MANDATORY_COLUMNS)
    valid_df.to_parquet("/tmp/valid.parquet")
    invalid_df.to_parquet("/tmp/invalid.parquet")
    print(report)

def task_process(**kwargs):
    import pandas as pd
    df = pd.read_parquet("/tmp/valid.parquet")
    processed = process_data(df, config.COLUMNS_TO_DROP)
    backup_validate(processed)
    processed.to_parquet("/tmp/processed.parquet")

def task_write(**kwargs):
    import pandas as pd
    df = pd.read_parquet("/tmp/processed.parquet")
    output_file = config.OUTPUT_DIR / "processed_taxi_data.parquet"
    write_local(df, output_file)
    write_azure(
        output_file,
        config.AZURE_CONTAINER_NAME,
        "processed_taxi_data.parquet",
        os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    )

with DAG(
    dag_id="batch_taxi_pipeline",
    start_date=datetime(2026, 8, 20),
    schedule="55 10 21 8 *",  # set to your defence date/cron
    catchup=False,
    tags=["de_project"],
) as dag:

    read_task = PythonOperator(task_id="read_data", python_callable=task_read)
    validate_task = PythonOperator(task_id="validate_data", python_callable=task_validate)
    process_task = PythonOperator(task_id="process_data", python_callable=task_process)
    write_task = PythonOperator(task_id="write_data", python_callable=task_write)

    read_task >> validate_task >> process_task >> write_task