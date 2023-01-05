import os
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile
from typing import List, Tuple

import requests
from airflow.providers.amazon.aws.transfers.local_to_s3 import (
    LocalFilesystemToS3Operator,
)
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def query_latest(
    forecast_hour: int,
    url_path: str = "WXO-DD/model_hrdps/continental/grib2",
    domain: str = "https://hpfx.collab.science.gc.ca",
) -> Tuple[str, str, str]:
    """Find the latest model run.
    Starting at the current date working backwards 5 days, for each day and for each forecasts [18, 12, 06, 00] a HEAD request is sent to the forecast_hour.
    First 200 OK response is returned."""
    current_date = datetime.now(timezone.utc)

    # url parameters
    forecasts = [f"{i:02}" for i in range(0, 24, 6)][::-1]
    dates = [(current_date - timedelta(days=i)).strftime("%Y%m%d") for i in range(5)]

    for date in dates:
        for forecast in forecasts:
            baseurl = f"{domain.strip('/')}/{date}/{url_path.strip('/')}/{forecast}/"
            request_url = f"{baseurl}{forecast_hour:03}/"
            res = requests.head(request_url)
            if res.status_code == 200:
                print("Success:", baseurl, date, forecast)
                return baseurl, date, forecast
            else:
                print("Status code:", res.status_code, request_url)

    return "", "", ""


def create_urls(
    base_url: str = "https://hpfx.collab.science.gc.ca/20221221/WXO-DD/model_hrdps/continental/grib2/06/",
    forecast_hours: List[str] = [f"{(i):03}" for i in range(49)],
    prefix: str = "CMC",
    model: str = "hrdps",
    domain: str = "continental",
    variable: str = "SNOD",
    level_type: str = "SFC",
    level: str = "0",
    resolution: str = "ps2.5km",
    date: str = datetime.now(timezone.utc).strftime("%Y%m%d"),
    model_run: str = "00",
    minutes: str = "00",
    extension: str = "grib2",
) -> List[str]:
    """Create list of URLs given inputs.
    URL structure: {base_url}/{forecast_hour}/{filename}
    Filename structure: {prefix}_{model}_{domain}_{variable}_{level_type}_{level}_{resolution}_{date}{model_run}_P{forecast_hour}-{minutes}.{extension}"""
    urls = []
    for forecast_hour in forecast_hours:
        filename = f"{prefix}_{model}_{domain}_{variable}_{level_type}_{level}_{resolution}_{date}{int(model_run):02}_P{int(forecast_hour):03}-{int(minutes):02}.{extension}"
        download_url = f"{base_url.strip('/')}/{forecast_hour.strip('/')}/{filename}"
        urls.append(download_url)

    return urls


def download_predictions(download_urls: List[str], savepath: str = "./") -> List[str]:
    """Download list of urls to savepath."""
    filepaths = []

    retry_strategy = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[404, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    for url in download_urls:
        filename = url.split("/")[-1]
        print(f"Downloading {url}", end=" | ")
        res = http.get(url)
        with NamedTemporaryFile() as f:
            f.write(res.content)
            create_local_to_s3_job = LocalFilesystemToS3Operator(
                task_id="create_local_to_s3_job",
                filename=f.name,
                dest_key=S3_KEY,
                dest_bucket=S3_BUCKET,
                replace=True,
            )
        # filepath = os.path.join(savepath, filename)
        # with open(filepath, "wb") as f:
        #     f.write(res.content)
        # print("File size:", res.headers["Content-Length"])
        # filepaths.append(filepath)

    # return filepaths
