import os
from datetime import datetime
from textwrap import dedent

from airflow import DAG
from airflow.decorators import dag, task
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.utils.dates import cron_presets

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["airflow@shouldishovel.com"],
    "email_on_failure": True,
    "email_on_retry": False,
}


@dag(
    dag_id="refresh_weather_data",
    default_args=default_args,
    description="Downlod the most recent forecasts for the configured variables from https://hpfx.collab.science.gc.ca",
    schedule="@hourly",  # Hourly
    start_date=datetime(2023, 1, 4),
    catchup=False,
)
def my_dag():

    task_get_op = SimpleHttpOperator(
    task_id="refresh_weather_data",
    method="GET",
    endpoint="get",
    data={"param1": "value1", "param2": "value2"},
    headers={},
    dag=dag,
)


my_dag()
