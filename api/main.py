import logging
import os
import subprocess
from datetime import datetime
from typing import Any
from urllib.parse import unquote

import geocoder
import predictions
from data_management import (
    delete_objects_from_bucket,
    delete_variables_record,
    file_name_info,
    find_latest_forecast,
    full_refresh,
    get_s3_filelisting,
    list_variables_records,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Define connection details
# password is read from .pgpass in home directory.
pg_connection_dict = {
    "dbname": os.environ["AWS_RDS_DB"],
    "user": os.environ["AWS_RDS_USER"],
    "port": os.environ["AWS_RDS_PORT"],
    "host": os.environ["AWS_RDS_HOST"],
}
aws_bucket = os.environ["AWS_BUCKET"]

app = FastAPI()

origins = ["http://localhost:1234"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/forecast/")
def get_forecast(table: str, latitude: float, longitude: float):
    """Returns the forecast from a specified table for a set of coordiantes in a pandas DataFrame"""
    return predictions.get_nearest_predictions_as_df(
        pg_connection_dict, table, latitude, longitude
    )


@app.get("/address/")
def get_address_coordinates(address: str) -> tuple[float, float]:
    """Queries geocoding API to get coordinates from address. Returns tuple of nulls if no single result was found"""
    address_unquoted = unquote(address)
    g = geocoder.google(address_unquoted)
    if g.error == "ZERO_RESULTS":
        logging.warn(f"{g.error}: {address_unquoted}")
    if g.error == "REQUEST_DENIED":
        logging.critical(f"API error: {g.error}")

    return g.lat, g.lng


@app.get("/data_mangement/find_latest_forecast")
def return_latest_forecast(
    forecast_hour: int,
    url_path: str = "WXO-DD/model_hrdps/continental/grib2",
    domain: str = "https://hpfx.collab.science.gc.ca",
) -> dict[str, str]:
    """Queries the canadian weather service to determine what is the most recent forecast set available based on the folders which exists."""
    return find_latest_forecast(
        forecast_hour=forecast_hour,
        url_path=url_path,
        domain=domain,
    )


@app.get("/data_mangement/refresh_weather_data")
def refresh_weather_data():
    """Redownloads the latest available weather forecasts."""
    variables = [
        {"variable": "SNOD", "level_type": "SFC", "level": "0"},  # Snow Depth in meters
        # {
        #     "variable": "APCP",
        #     "level_type": "SFC",
        #     "level": "0",
        # },  # Accumulated Precipitation in kg m-2
        # {
        #     "variable": "WEASN",
        #     "level_type": "SFC",
        #     "level": "0",
        # },  # Accumulated Precipitation type - Snow in kg m-2
        {
            "variable": "TMP",
            "level_type": "TGL",
            "level": "2",
        },  # Temperature 2m above ground in kelvin
        # {
        #     "variable": "TCDC",
        #     "level_type": "SFC",
        #     "level": "0",
        # },  # Total Cloud in percent
        # {"variable": "ALBDO", "level_type": "SFC", "level": "0"},  # Albedo in percent
        # {
        #     "variable": "RH",
        #     "level_type": "TGL",
        #     "level": "2",
        # },  # Relative humidity 2m above ground in percent
    ]

    db_conn_status = test_db_connection()
    if db_conn_status.returncode != 0:
        return db_conn_status

    results = full_refresh(
        variables,
        aws_bucket=aws_bucket,
        conn_details=pg_connection_dict,
        last_forecast_hour=48,
    )
    return results


@app.get("/data_management/list_s3_contents")
def list_s3_contents(prefix: str = "") -> list[dict[str, Any]]:
    """Returns list of the S3 bucket contents filtered for files starting with the prefix."""
    return get_s3_filelisting(
        aws_bucket=aws_bucket,
        prefix=prefix,
    )


@app.get("/data_management/test_db_connection")
def test_db_connection():
    """Executes pg_isready to test connection to DB"""
    status = subprocess.run(
        [
            "pg_isready",
            "-h",
            pg_connection_dict["host"],
            "-d",
            pg_connection_dict["dbname"],
            "-p",
            pg_connection_dict["port"],
            "-U",
            pg_connection_dict["user"],
        ],
        capture_output=True,
    )
    return status


@app.get("/data_management/delete_objects")
def delete_objects_with_prefix(prefix: str) -> dict[str, Any]:
    """Delete files matching the provided prefix from the AWS S3 bucket.

    DANGEROUS: Make sure your prefix is correct."""
    files_to_delete = get_s3_filelisting(
        aws_bucket=aws_bucket,
        prefix=prefix,
    )

    return delete_objects_from_bucket(
        aws_bucket=aws_bucket,
        file_list=files_to_delete,
    )


@app.get("/data_management/filename_components")
def get_filename_components(fullpath: str) -> dict[str, str]:
    """Segments the fullpath into its components."""
    return file_name_info(fullpath)


@app.get("/data_management/delete_variable")
def delete_variable(file_name: str):
    """Deletes the variable with the given filename."""
    return delete_variables_record(file_name=file_name, conn_details=pg_connection_dict)


@app.get("/data_management/list_variables")
def list_variables():
    """Returns the full variables table."""
    return list_variables_records(conn_details=pg_connection_dict)
