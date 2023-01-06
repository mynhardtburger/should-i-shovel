# https://stackoverflow.com/questions/68826336/how-to-setup-s3-connection-using-env-variables-in-airflow-using-docker

import json
import os

from airflow.exceptions import AirflowFailException
from airflow.models.connection import Connection


def _create_connection(**context):
    """
    Sets the connection information about the environment using the Connection
    class instead of doing it manually in the Airflow UI
    """
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    # AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    credentials = [
        # AWS_SESSION_TOKEN,
        AWS_ACCESS_KEY_ID,
        AWS_SECRET_ACCESS_KEY,
        AWS_DEFAULT_REGION,
    ]
    if not credentials or any(not credential for credential in credentials):
        raise AirflowFailException("Environment variables were not passed")

    extras = json.dumps(
        dict(
            # aws_session_token=AWS_SESSION_TOKEN,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_DEFAULT_REGION,
        ),
    )
    try:
        Connection(
            conn_id="s3_con",
            conn_type="S3",
            extra=extras,
        )
    except Exception as e:
        raise AirflowFailException(
            f"Error creating connection to Airflow :{e}",
        )
