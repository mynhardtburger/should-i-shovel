import logging
import os
import subprocess
from datetime import datetime
from typing import Any
from urllib.parse import unquote

import data_management
import geocoder
import predictions

# from data_management import (
#     delete_objects_from_bucket,
#     delete_variable_record,
#     does_prediction_data_exist,
#     file_name_info,
#     find_latest_forecast,
#     full_refresh,
#     get_s3_filelisting,
#     list_latest_variable_records,
#     list_orphan_bucket_objects,
#     list_variables_records,
#     list_old_variable_records,
# )
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

origins = ["http://localhost:8080"]

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


@app.get("/forecast/coordinates")
def get_forecast(
    latitude: float,
    longitude: float,
):
    """Returns the forecast for a set of coordiantes"""
    dfs = predictions.get_predictions_as_dfs(
        conn_details=pg_connection_dict,
        latitude=latitude,
        longitude=longitude,
    )

    # no results
    if len(dfs[0]) == 0:
        return "no results"

    df = predictions.format_predictions(dfs)
    results = predictions.df_details(dfs[0])
    del results["unit"]
    del results["variable"]
    del results["variable_description"]
    results.update({"data": df.to_dict("list")})

    return results


@app.get("/forecast/address")
def get_forecast_from_address(address: str):
    """Returns the forecast for an address"""
    latitude, longitude = get_address_coordinates(address=address)
    if (not latitude) or (not longitude):
        return f"Coordinates not found for address. Try being more specific."

    return get_forecast(latitude, longitude)


@app.get("/address/")
def get_address_coordinates(address: str) -> tuple[float, float]:
    """Queries geocoding API to get coordinates from address. Returns tuple of nulls if no single result was found"""
    address_unquoted = unquote(address)
    g = geocoder.google(address_unquoted)
    if g.error == "ZERO_RESULTS":
        logging.warn(f"{g.error}: {address_unquoted}")
    if g.error == "REQUEST_DENIED":
        logging.critical(f"API error: {g.error}")

    if (not g.lat) or (not g.lng):
        print("Coordinates not found for address. Try being more specific.")
    print(f"Latitude: {g.lat} Longitude: {g.lng}")
    return g.lat, g.lng


@app.get("/data_mangement/find_latest_forecast")
def return_latest_forecast(
    forecast_hour: int,
    url_path: str = "WXO-DD/model_hrdps/continental/2.5km/grib2",
    domain: str = "https://hpfx.collab.science.gc.ca",
) -> dict[str, str]:
    """Queries the canadian weather service to determine what is the most recent forecast set available based on the folders which exists."""
    return data_management.find_latest_forecast(
        forecast_hour=forecast_hour,
        url_path=url_path,
        domain=domain,
    )


@app.get("/data_mangement/refresh_weather_data")
def refresh_weather_data():
    """Redownloads the latest available weather forecasts."""
    variables_hrdps_polar = [
        {"variable": "SNOD", "level_type": "SFC", "level": "0"},  # Snow Depth in meters
        {
            "variable": "TMP",
            "level_type": "TGL",
            "level": "2",
        },  # Temperature 2m above ground in kelvin
    ]

    variables_hrdps_rotated_lat_lon = [
        {"variable": "TMP", "level_type": "Sfc", "level": ""},  # Temperature
        {
            "variable": "CONDASNOW",
            "level_type": "Sfc",
            "level": "",
        },  # Conditional amount of snow
        # {"variable": "CSNOW", "level_type": "Sfc", "level": ""}, # Probability of snow
    ]

    db_conn_status = test_db_connection()
    if db_conn_status.returncode != 0:
        return db_conn_status

    results = data_management.full_refresh(
        variables_hrdps_rotated_lat_lon,
        aws_bucket=aws_bucket,
        conn_details=pg_connection_dict,
        last_forecast_hour=48,
    )

    # delete old variables
    delete_old_variables()

    # delete orphaned files
    delete_orphan_objects()

    return results


@app.get("/data_management/list_s3_contents")
def list_s3_contents(prefix: str = "") -> list[dict[str, Any]]:
    """Returns list of the S3 bucket contents filtered for files starting with the prefix."""
    return data_management.get_s3_filelisting(
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
    files_to_delete = data_management.get_s3_filelisting(
        aws_bucket=aws_bucket,
        prefix=prefix,
    )

    return data_management.delete_objects_from_bucket(
        aws_bucket=aws_bucket,
        file_list=files_to_delete,
    )


@app.get("/data_management/filename_components")
def get_filename_components(fullpath: str, format: str) -> dict[str, str]:
    """Segments the fullpath into its components.

    available formats:
        "polar_stereo"\n
        "rotated_lat_lon"
    """
    return data_management.file_name_info(fullpath, format)


@app.get("/data_management/delete_variable")
def delete_variable(file_name: str):
    """Deletes the variable with the given filename."""
    return data_management.delete_variable_record(
        file_name=file_name, conn_details=pg_connection_dict
    )


@app.get("/data_management/delete_old_variables")
def delete_old_variables():
    """Deletes all old variables leaving only the latest version of each variable."""
    results = []
    for var in list_old_variables():
        results.append(delete_variable(var["filename"]))
    return results


@app.get("/data_management/list_variables")
def list_variables():
    """Returns the full variables table."""
    return data_management.list_variables_records(
        conn_details=pg_connection_dict
    ).to_dict("records")


@app.get("/data_management/list_orphaned_bucket_objects")
def list_orphan_objects(filter_pattern: str = ""):
    """Finds all orphaned bucket objects and returns the orphans containing the filter_pattern."""
    return data_management.list_orphan_bucket_objects(
        filter_pattern=filter_pattern,
        aws_bucket=aws_bucket,
        conn_details=pg_connection_dict,
    )


@app.get("/data_management/delete_orphaned_bucket_objects")
def delete_orphan_objects(filter_pattern: str = ""):
    """Deletes all orphaned bucket objects."""
    orphaned_objects = data_management.list_orphan_bucket_objects(
        filter_pattern=filter_pattern,
        aws_bucket=aws_bucket,
        conn_details=pg_connection_dict,
    )

    if not orphaned_objects:
        return f"No orphaned objects found to be deleted."

    return data_management.delete_objects_from_bucket(
        aws_bucket=aws_bucket, file_list=orphaned_objects
    )


@app.get("/data_management/list_latest_variables")
def list_latest_variables():
    """Return the most recent instance of each variable loaded."""
    return data_management.list_latest_variable_records(
        conn_details=pg_connection_dict
    ).to_dict("records")


@app.get("/data_management/list_old_variables")
def list_old_variables():
    """Return the most recent instance of each variable loaded."""
    return data_management.list_old_variable_records(
        conn_details=pg_connection_dict
    ).to_dict("records")


@app.get("/data_management/prediction_data_exists")
def prediction_data_exists(forecast_string: str):
    """Returns True if the prediction data already exists within the DB."""
    return data_management.does_prediction_data_exist(
        conn_details=pg_connection_dict, forecast_string=forecast_string
    )
