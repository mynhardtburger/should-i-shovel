import logging
from urllib.parse import unquote

import geocoder
import predictions
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
