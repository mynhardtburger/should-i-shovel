import os
import subprocess
from datetime import datetime, timedelta, timezone
import boto3

import requests
from typing import Any

from io import BytesIO
from tempfile import TemporaryDirectory


def find_latest_forecast(
    forecast_hour: int,
    url_path: str = "WXO-DD/model_hrdps/continental/grib2",
    domain: str = "https://hpfx.collab.science.gc.ca",
) -> dict[str, str]:
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
                return {"baseurl": baseurl, "date": date, "forecast": forecast}
            else:
                print("Status code:", res.status_code, request_url)

    return {"baseurl": "", "date": "", "forecast": ""}


def create_urls(
    base_url: str = "https://hpfx.collab.science.gc.ca/20221221/WXO-DD/model_hrdps/continental/grib2/06/",
    forecast_hours: list[str] = [f"{(i):03}" for i in range(1, 49)],
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
) -> list[str]:
    """Create list of URLs given inputs.
    URL structure: {base_url}/{forecast_hour}/{filename}
    Filename structure: {prefix}_{model}_{domain}_{variable}_{level_type}_{level}_{resolution}_{date}{model_run}_P{forecast_hour}-{minutes}.{extension}"""
    urls = []
    for forecast_hour in forecast_hours:
        filename = f"{prefix}_{model}_{domain}_{variable}_{level_type}_{level}_{resolution}_{date}{int(model_run):02}_P{int(forecast_hour):03}-{int(minutes):02}.{extension}"
        download_url = f"{base_url.strip('/')}/{forecast_hour.strip('/')}/{filename}"
        urls.append(download_url)

    return urls

def download_predictions(
    download_urls: list[str], aws_bucket: str, path: str
) -> dict[str, Any]:
    """Download list of urls to aws bucket.
    Executed via CLI using wget and AWS CLI.

    If successful returns true.
    On error return list of exceptions."""

    errors: list[Exception] = []
    completed_downloads:list[str] = []

    for url in download_urls:
        filename = url.split("/")[-1]
        s3_bucket_path = "s3://" + os.path.join(aws_bucket, path, filename)
        try:
            downloader = subprocess.run(["wget", "-O", "-", url], capture_output=True, check=True)
            s3_upload = subprocess.run(
                ["aws", "s3", "cp", "-", s3_bucket_path], input=downloader.stdout, check=True
            )
        except subprocess.CalledProcessError as e:
            print("Error:", url, s3_bucket_path)
            print(e)
            errors.append(e)
        else:
            print("Upload done:", s3_bucket_path)
            completed_downloads.append(s3_bucket_path)

    return {
        "download count": len(completed_downloads),
        "error count": len(errors),
        "download urls": completed_downloads,
        "errors": errors
    }

def download_predictions_bulk(
    download_urls: list[str], aws_bucket: str, path: str
):
    """Download list of urls to aws bucket.
    Executed via CLI using wget and AWS CLI.

    If successful returns true.
    On error return list of exceptions."""
    errors: list[Exception] = []

    download_list = BytesIO("\n".join(download_urls).encode())
    s3_bucket_path = "s3://" + os.path.join(aws_bucket, path)
    with TemporaryDirectory() as tmp_dir_name:
        try:
            downloader = subprocess.run(["wget", "-i", "-", "-P", tmp_dir_name], input=download_list.read(), check=True, capture_output=True)
            print("files downloaded:", os.listdir(tmp_dir_name))
            s3_upload = subprocess.run(
                ["aws", "s3", "cp", "--recursive", "--no-progress", tmp_dir_name, s3_bucket_path], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(e)
            errors.append(e)
        else:
            print("Upload done:", len(download_urls), "files")
            return s3_upload.stdout
    return errors

def get_s3_filelisting(aws_bucket:str, prefix:str) -> list[dict[str,Any]]:
    contents = []

    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator("list_objects_v2")
    response = paginator.paginate(Bucket=aws_bucket, Prefix=prefix, PaginationConfig={"PageSize": 1000})

    for page in response:
        files = page.get("Contents")
        if not files:
            return contents

        for file in files:
            print(f"file_name: {file['Key']}, size: {file['Size']}")
            contents.append(file)

    return contents
