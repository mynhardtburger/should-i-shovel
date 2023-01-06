import logging
from urllib.parse import unquote

import geocoder
import predictions
from data_management import create_urls, download_predictions, find_latest_forecast, get_s3_filelisting, download_predictions_bulk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Any

# Define connection details
pg_connection_dict = {
    "dbname": "mydb",
    "user": "myn",
    "password": r"2)2K9zJCKZv7pLUd",
    "port": "5432",
    "host": "terraform-20221222010822007100000002.c2x7llrlmsr3.us-east-2.rds.amazonaws.com",
}


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
def get_forecast(latitude: float, longitude: float):
    return predictions.get_nearest_predictions_as_df(
        pg_connection_dict, latitude, longitude
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
    latest_url = find_latest_forecast(48)
    download_urls:list[str] = []

    variables = [
        {"variable": "SNOD", "level_type": "SFC", "level": "0"}, # Snow Depth in meters
        {"variable": "APCP", "level_type": "SFC", "level": "0"}, # Accumulated Precipitation in kg m-2
        {"variable": "WEASN", "level_type": "SFC", "level": "0"}, # Accumulated Precipitation type - Snow in kg m-2
        {"variable": "TMP", "level_type": "TGL", "level": "2"}, # Temperature 2m above ground in kelvin
        {"variable": "TCDC", "level_type": "SFC", "level": "0"}, # Total Cloud in percent
        {"variable": "ALBDO", "level_type": "SFC", "level": "0"}, # Albedo in percent
        {"variable": "RH", "level_type": "TGL", "level": "2"}, # Relative humidity 2m above ground in percent
    ]

    for var  in variables:
        urls = create_urls(latest_url["baseurl"], model_run=latest_url["forecast"], **var)
        download_urls.extend(urls)

    results = download_predictions_bulk(
        download_urls=download_urls,
        aws_bucket="sto01.dev.us-east-2.aws.shouldishovel.com",
        path="gribs"
    )
    return results

@app.get("/data_management/list_s3_contents")
def list_s3_contents(prefix:str = "") -> list[dict[str,Any]]:
    """Returns list of the S3 bucket contents filtered for files starting with the prefix."""
    return get_s3_filelisting(aws_bucket="sto01.dev.us-east-2.aws.shouldishovel.com", prefix=prefix,)
