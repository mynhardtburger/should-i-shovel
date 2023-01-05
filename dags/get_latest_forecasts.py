import os
from datetime import datetime

from airflow import DAG
from airflow.decorators import dag, task
from airflow.utils.dates import cron_presets

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["airflow@shouldishovel.com"],
    "email_on_failure": True,
    "email_on_retry": False,
}


@dag(
    dag_id="download_latest_forecasts",
    default_args=default_args,
    description="Downlod the most recent forecasts for the configured variables from https://hpfx.collab.science.gc.ca",
    schedule_interval="@hourly",  # Hourly
    start_date=datetime(2023, 1, 4),
    catchup=False,
)
def my_dag():
    @task(task_id="download_latest_forecasts")
    def determine_latest_forecast():
        from common_packages.forecasts import (
            create_urls,
            download_predictions,
            query_latest,
        )

        baseurl, date, model_run = query_latest(48)
        download_urls = create_urls(base_url=baseurl, date=date, model_run=model_run)
        return os.getcwd(), download_urls
        # paths = download_predictions(download_urls, "../data/")

    determine_latest_forecast()


my_dag()
