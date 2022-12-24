from fastapi import FastAPI
import predictions

# Define connection details
pg_connection_dict = {
    'dbname': "mydb",
    'user': "myn",
    'password': r"2)2K9zJCKZv7pLUd",
    'port': "5432",
    'host': "terraform-20221222010822007100000002.c2x7llrlmsr3.us-east-2.rds.amazonaws.com"
}



app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/forecast/")
def get_forecast(latitude: float, longitude: float):
    return predictions.get_nearest_predictions_as_df(pg_connection_dict, latitude, longitude)
