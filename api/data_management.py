import os
import subprocess
from datetime import datetime, timedelta, timezone
from fileinput import filename
from io import BytesIO
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any

import boto3
import pandas as pd
import psycopg
import requests
from predictions import execute_sql_as_dataframe
from psycopg import sql


def find_latest_forecast(
    forecast_hour: int,
    url_path: str = "WXO-DD/model_hrdps/continental/2.5km/grib2",
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
                print(
                    "Latest forecast is:",
                    baseurl,
                    "date:",
                    date,
                    "forecast hour:",
                    forecast,
                )
                return {"baseurl": baseurl, "date": date, "forecast": forecast}
            # else:
            # print("Status code:", res.status_code, request_url)

    return {"baseurl": "", "date": "", "forecast": ""}


def create_urls_polar_stereo(
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


def create_urls_rotated_lat_lon(
    base_url: str = "https://hpfx.collab.science.gc.ca/20221221/WXO-DD/model_hrdps/continental/2.5km/grib2/06/",
    forecast_hours: list[str] = [f"{(i):03}" for i in range(1, 49)],
    prefix: str = "MSC",
    model: str = "HRDPS-WEonG",
    variable: str = "TMP",
    level_type: str = "Sfc",
    level: str = "",
    grille: str = "RLatLon",
    resolution: str = "0.0225",
    date: str = datetime.now(timezone.utc).strftime("%Y%m%d"),
    model_run: str = "00",
    extension: str = "grib2",
) -> list[str]:
    """Create list of URLs given inputs.
    URL structure: {base_url}/{forecast_hour}/{filename}
    Filename structure: {date}T{model_run}Z_{prefix}_{model}_{variable}_{level_type}-{level}_{grille}{resolution}_PT{forecast_hour}H.{extension}"""
    urls = []
    for forecast_hour in forecast_hours:
        filename = f"""{date}T{int(model_run):02}Z_{prefix}_{model}_{variable}_{level_type}{"-" if level else ""}{level}_{grille}{resolution}_P{"T" if model == "HRDPS-WEonG" else ""}{forecast_hour}{"H" if model == "HRDPS-WEonG" else ""}.{extension}"""
        download_url = (
            f"""{base_url.strip('/')}/{forecast_hour.strip('/')}/{filename}"""
        )
        urls.append(download_url)

    return urls


def download_predictions(
    download_urls: list[str], aws_bucket: str, path: str
) -> dict[str, Any]:
    """Download list of urls to aws bucket.
    Executed via CLI using wget and AWS CLI.

    Returns dictionary containing download results and file paths.
    """

    errors: list[Exception] = []
    completed_downloads: list[str] = []

    for url in download_urls:
        filename = url.split("/")[-1]
        s3_bucket_path = "s3://" + os.path.join(aws_bucket, path, filename)
        try:
            downloader = subprocess.run(
                ["wget", "-O", "-", url], capture_output=True, check=True
            )
            s3_upload = subprocess.run(
                ["aws", "s3", "cp", "-", s3_bucket_path],
                input=downloader.stdout,
                check=True,
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
        "errors": errors,
    }


def download_predictions_bulk(
    download_urls: list[str], aws_bucket: str, prefix: str
) -> list[Exception] | str:
    """Download list of urls to aws bucket.
    Executed via CLI using wget and AWS CLI.

    If successful returns aws cli std output.
    On error return list of exceptions."""
    errors: list[Exception] = []
    # print("\n".join(download_urls))

    download_list = BytesIO("\n".join(download_urls).encode())
    s3_bucket_path = "s3://" + os.path.join(aws_bucket, prefix)
    with TemporaryDirectory() as tmp_dir_name:
        try:
            downloader = subprocess.run(
                ["wget", "-i", "-", "-P", tmp_dir_name],
                input=download_list.read(),
                check=True,
                capture_output=True,
            )
            print("files downloaded:", os.listdir(tmp_dir_name))
            s3_upload = subprocess.run(
                [
                    "aws",
                    "s3",
                    "cp",
                    "--recursive",
                    "--no-progress",
                    tmp_dir_name,
                    s3_bucket_path,
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(e)
            errors.append(e)
        else:
            print("Upload done:", len(download_urls), "files")
            return s3_upload.stdout.decode()
    return errors


def get_s3_filelisting(aws_bucket: str, prefix: str = "") -> list[dict[str, Any]]:
    """Fetches list of S3 objects from the specified bucket filtered for the provided prefix.
    Credentials are read from the environmental variables.

    Each item in the list is a dictionary.
    """
    contents = []

    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator("list_objects_v2")
    response = paginator.paginate(
        Bucket=aws_bucket, Prefix=prefix, PaginationConfig={"PageSize": 1000}
    )

    print("Retriving AWS S3 file listing...", end=" ")
    for page in response:
        files = page.get("Contents")
        if not files:
            # print("None")
            return contents

        for file in files:
            # print(f"file_name: {file['Key']}, size: {file['Size']}")
            contents.append(file)
    print(f"{len(contents)} files")
    return contents


def file_name_info(full_path: str, format: str) -> dict[str, str]:
    """Returns a dictionary of the filename split into its component parts.

    available formats:
        "polar_stereo"\n
        "rotated_lat_lon"
    """
    format_map = {
        "polar_stereo": name_format_polar_stereographic_grid,
        "rotated_lat_lon": name_format_rotated_lat_lon_grid,
    }

    return format_map[format](full_path)


def name_format_polar_stereographic_grid(full_path: str) -> dict[str, str]:
    """Split the filename into its parts based on the polar-stereographic
    nomenclature as defined here:
    https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/

    CMC_hrdps_domain_Variable_LevelType_level_ps2.5km_YYYYMMDDHH_Phhh-mm.grib2

    Returns a dictionary of the components."""

    fullpath, sep_period, file_extension = full_path.rpartition(".")
    assert file_extension == "grib2"

    base_path, sep_slash, filename = fullpath.rpartition("/")
    filename_parts = filename.split("_")
    assert len(filename_parts) == 9

    forecast_start_timestamp = datetime.strptime(
        f"{filename_parts[7]}00 +0000", "%Y%m%d%H%M %z"
    )
    forecast_interval_offset = timedelta(
        hours=int(filename_parts[8].split("-")[0][1:]),
        minutes=int(filename_parts[8].split("-")[1]),
    )
    forecast_timestamp = forecast_start_timestamp + forecast_interval_offset

    components = {
        "full_path": full_path,
        "base_path": base_path + sep_slash,
        "filename": filename + file_extension,
        "base_filename": filename,
        "file_extension": sep_period + file_extension,
        "forecast_base_string": "_".join(filename_parts[:7]),
        "forecast_string": "_".join(filename_parts[:8]),
        "source": filename_parts[0],
        "model": filename_parts[1],
        "domain": filename_parts[2],
        "variable": filename_parts[3],
        "leveltype": filename_parts[4],
        "level": filename_parts[5],
        "resolution": filename_parts[6],
        "forecast_start_timestamp": forecast_start_timestamp,
        "forecast_interval_offset": forecast_interval_offset,
        "forecast_timestamp": forecast_timestamp,
        "forecast_startdate": filename_parts[7][:-2],
        "run_time_hour": filename_parts[7][-2:],
        "forecast_hour": filename_parts[8].split("-")[0][1:],
        "forecast_minute": filename_parts[8].split("-")[1],
    }

    return components


def name_format_rotated_lat_lon_grid(full_path: str) -> dict[str, str]:
    """Split the filename into its parts based on the polar-stereographic
    nomenclature as defined here:
    https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/

    {YYYYMMDD}T{HH}Z_MSC_HRDPS_{VAR}_{LVLTYPE-LVL}_{Grille}{resolution}_P{hhh}.grib2
    {YYYYMMDD}T{HH}Z_MSC_HRDPS-WEonG_{VAR}_{LVLTYPE-LVL}_{Grille}{resolution}_PT{hhh}H.grib2

    Returns a dictionary of the components."""

    fullpath, sep_period, file_extension = full_path.rpartition(".")
    assert file_extension == "grib2"

    base_path, sep_slash, filename = fullpath.rpartition("/")
    filename_parts = filename.split("_")
    assert len(filename_parts) == 7

    lvltype, _, lvl = filename_parts[4].partition("-")
    forecast_startdate = filename_parts[0][:8]
    forecast_starthour = filename_parts[0][9:11]
    forecast_hour = "".join([s for s in filename_parts[-1] if s.isdigit()])

    forecast_start_timestamp = datetime.strptime(
        f"{forecast_startdate}{forecast_starthour}00 +0000", "%Y%m%d%H%M %z"
    )
    forecast_interval_offset = timedelta(
        hours=int(forecast_hour),
    )
    forecast_timestamp = forecast_start_timestamp + forecast_interval_offset

    components = {
        "full_path": full_path,
        "base_path": base_path + sep_slash,
        "filename": filename + sep_period + file_extension,
        "base_filename": filename,
        "file_extension": sep_period + file_extension,
        "forecast_base_string": "_".join(filename_parts[1:-1]),
        "forecast_string": "_".join(filename_parts[:-1]),
        "source": filename_parts[1],
        "model": filename_parts[2],
        "variable": filename_parts[3],
        "leveltype": lvltype,
        "level": lvl,
        "grille": "RLatLon",
        "resolution": filename_parts[5].removeprefix("RLatLon"),
        "forecast_start_timestamp": forecast_start_timestamp,
        "forecast_interval_offset": forecast_interval_offset,
        "forecast_timestamp": forecast_timestamp,
        "forecast_startdate": forecast_startdate,
        "run_time_hour": forecast_starthour,
        "forecast_hour": forecast_hour,
    }

    return components


def create_vrt(
    input_file_listing: list[dict[str, Any]], output_path: str, bucket: str
) -> list[Exception] | str:
    """Executes gdalbuildvrt to create virtual dataset.
    Returns the GDAL path the output file, or a list of errors."""

    errors: list[Exception] = []
    file_list = [f"/vsis3/{bucket}/{file['Key']}\n" for file in input_file_listing]
    vrt_path = f"/vsis3/{bucket}/{output_path}"

    with NamedTemporaryFile(mode="w+t") as input_list:
        input_list.writelines(file_list)
        input_list.seek(0)
        try:
            print("Creating virtual dataset:")
            buildvrt = subprocess.run(
                [
                    "gdalbuildvrt",
                    "-separate",
                    "-input_file_list",
                    input_list.name,
                    vrt_path,
                ],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print("Error:", e)
            errors.append(e)
        else:
            print(buildvrt.args)
            print(buildvrt.stdout.decode())
            return vrt_path
    return errors


def load_to_postgis(
    vrt_path: str,
    schema: str,
    table_name: str,
    conn_details: dict[str, str],
    srid: str = "990000",
) -> list[Exception] | str:
    """Using raster2pgsql and the virtual dataset (VRT), insert the data into PostGIS.

    Return psql stdout"""
    assert vrt_path[:7] == "/vsis3/"

    errors: list[Exception] = []
    schema_table = f"{schema}.{table_name}"
    try:
        print("raster2pgsql creating VRT")
        vrt = subprocess.Popen(
            [
                "raster2pgsql",
                "-a",  # Append to the existing table
                "-I",  # Create a GIST spatial index on the raster column.
                "-q",  # Wrap PostgreSQL identifiers in quotes.
                "-t",  # Cut raster into tiles to be inserted one per table row.
                "auto",
                "-s",  # Set the raster's SRID.
                srid,
                "-f",  # Specify the name of the raster column
                "raster",
                "-F",  # Add filename column
                "-Y",  # Use copy statements instead of insert statements.
                vrt_path,
                schema_table,
            ],
            stdout=subprocess.PIPE,
        )
        psql = subprocess.run(
            [
                "psql",
                "-d",
                conn_details["dbname"],
                "-h",
                conn_details["host"],
                "-p",
                conn_details["port"],
                "-U",
                conn_details["user"],
            ],
            capture_output=True,
            check=True,
            stdin=vrt.stdout,
        )

    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)
        errors.append(e.stderr)
        return errors
    else:
        print(psql.stdout)
        return psql.stdout.decode()


def full_refresh(
    variables: list[dict[str, str]],
    aws_bucket: str,
    last_forecast_hour: int,
    conn_details: dict[str, str],
):
    print("Refreshing weather data...")

    # get latest forecast hour
    latest_url = find_latest_forecast(last_forecast_hour)
    results: list[str] = []

    # cycle through variables and update each
    for var in variables:
        download_urls = create_urls_rotated_lat_lon(
            latest_url["baseurl"],
            model_run=latest_url["forecast"],
            date=latest_url["date"],
            **var,
        )
        assert len(download_urls) > 0

        forecast_info = file_name_info(download_urls[0], "rotated_lat_lon")
        # print("forecast_info:", forecast_info)
        s3_prefix = f"""gribs/{forecast_info["forecast_base_string"]}"""

        if does_prediction_data_exist(
            conn_details=conn_details, forecast_string=forecast_info["forecast_string"]
        ):
            message = f"""Prediction data already exists. Skipping: {forecast_info["forecast_string"]}"""
            print(message)
            results.append(message)
            continue

        print("Downloading prediction data for:", forecast_info["forecast_string"])

        prior_folder_contents = get_s3_filelisting(
            aws_bucket=aws_bucket, prefix=s3_prefix
        )  # to be delete if update was successful.

        download_results = download_predictions_bulk(
            download_urls=download_urls,
            aws_bucket=aws_bucket,
            prefix=s3_prefix,
        )
        assert isinstance(download_results, str)

        after_folder_contents = get_s3_filelisting(
            aws_bucket=aws_bucket, prefix=s3_prefix
        )

        downloaded_files = []
        for file in after_folder_contents:
            try:
                prior_folder_contents.index(file)
            except ValueError as e:
                downloaded_files.append(file)
            else:
                pass
        assert len(downloaded_files) > 0

        vrt = create_vrt(
            downloaded_files,
            f"""{forecast_info["forecast_string"]}.vrt""",
            bucket=aws_bucket,
        )
        print(vrt)
        assert isinstance(vrt, str)

        insert_variables = insert_variables_record_rotated_lat_lon(
            forecast_info, conn_details
        )
        print(insert_variables)

        psql = load_to_postgis(
            vrt, "public", "predictions", conn_details, srid="990001"
        )
        assert isinstance(psql, str)
        print(psql)
        results.append(psql)

    print("Done.")
    return results


def delete_objects_from_bucket(
    aws_bucket: str, file_list: list[dict[str, Any]]
) -> dict[str, Any]:
    """Delete list of files from AWS bucket."""
    print("Deleting AWS S3 objects...")
    s3_client = boto3.client("s3")
    response = s3_client.delete_objects(
        Bucket=aws_bucket,
        Delete={"Objects": [{"Key": file["Key"]} for file in file_list]},
    )
    return response


def insert_variables_record_polar_stereo(
    file_name_info: dict[str, str], conn_details: dict[str, str]
) -> dict[str, Any]:
    columns = [
        "filename",
        "forecast_base_string",
        "forecast_string",
        "forecast_start_timestamp",
        "source",
        "model",
        "variable",
        "leveltype",
        "level",
        "resolution",
    ]
    on_conflict_columns = columns[1:]

    sql_statement = sql.SQL(
        """INSERT INTO {table} ({columns}) VALUES (
        {val_filename},
        {val_forecast_base_string},
        {val_forecast_string},
        {val_forecast_start_timestamp},
        {val_source},
        {val_model},
        {val_variable},
        {val_leveltype},
        {val_level},
        {val_resolution}
        )
        ON CONFLICT ("filename") DO UPDATE
        SET ({conflict_columns}) = (
            {val_forecast_base_string},
            {val_forecast_string},
            {val_forecast_start_timestamp},
            {val_source},
            {val_model},
            {val_variable},
            {val_leveltype},
            {val_level},
            {val_resolution})
        WHERE "variables"."filename" = {val_filename}
        """
    ).format(
        table=sql.Identifier("public", "variables"),
        columns=sql.SQL(", ").join(sql.Identifier(col) for col in columns),
        val_filename=sql.Literal(file_name_info["forecast_string"] + ".vrt"),
        val_forecast_base_string=sql.Literal(file_name_info["forecast_base_string"]),
        val_forecast_string=sql.Literal(file_name_info["forecast_string"]),
        val_forecast_start_timestamp=sql.Literal(
            file_name_info["forecast_start_timestamp"]
        ),
        val_source=sql.Literal(file_name_info["source"]),
        val_model=sql.Literal(file_name_info["model"]),
        val_variable=sql.Literal(file_name_info["variable"]),
        val_leveltype=sql.Literal(file_name_info["leveltype"]),
        val_level=sql.Literal(file_name_info["level"]),
        val_resolution=sql.Literal(file_name_info["resolution"]),
        conflict_columns=sql.SQL(", ").join(
            sql.Identifier(col) for col in on_conflict_columns
        ),
    )

    with psycopg.connect(**conn_details, autocommit=True) as conn:
        with conn.cursor() as curr:
            res = curr.execute(sql_statement)

    return {
        "statusmessage": res.statusmessage,
        "rowcount": res.rowcount,
    }


def insert_variables_record_rotated_lat_lon(
    file_name_info: dict[str, str], conn_details: dict[str, str]
) -> dict[str, Any]:
    columns = [
        "filename",
        "forecast_base_string",
        "forecast_string",
        "forecast_start_timestamp",
        "source",
        "model",
        "variable",
        "leveltype",
        "level",
        "resolution",
    ]
    on_conflict_columns = columns[1:]

    sql_statement = sql.SQL(
        """INSERT INTO {table} ({columns}) VALUES (
        {val_filename},
        {val_forecast_base_string},
        {val_forecast_string},
        {val_forecast_start_timestamp},
        {val_source},
        {val_model},
        {val_variable},
        {val_leveltype},
        {val_level},
        {val_resolution}
        )
        ON CONFLICT ("filename") DO UPDATE
        SET ({conflict_columns}) = (
            {val_forecast_base_string},
            {val_forecast_string},
            {val_forecast_start_timestamp},
            {val_source},
            {val_model},
            {val_variable},
            {val_leveltype},
            {val_level},
            {val_resolution})
        WHERE "variables"."filename" = {val_filename}
        """
    ).format(
        table=sql.Identifier("public", "variables"),
        columns=sql.SQL(", ").join(sql.Identifier(col) for col in columns),
        val_filename=sql.Literal(file_name_info["forecast_string"] + ".vrt"),
        val_forecast_base_string=sql.Literal(file_name_info["forecast_base_string"]),
        val_forecast_string=sql.Literal(file_name_info["forecast_string"]),
        val_forecast_start_timestamp=sql.Literal(
            file_name_info["forecast_start_timestamp"]
        ),
        val_source=sql.Literal(file_name_info["source"]),
        val_model=sql.Literal(file_name_info["model"]),
        val_variable=sql.Literal(file_name_info["variable"]),
        val_leveltype=sql.Literal(file_name_info["leveltype"]),
        val_level=sql.Literal(file_name_info["level"]),
        val_resolution=sql.Literal(file_name_info["resolution"]),
        conflict_columns=sql.SQL(", ").join(
            sql.Identifier(col) for col in on_conflict_columns
        ),
    )

    with psycopg.connect(**conn_details, autocommit=True) as conn:
        with conn.cursor() as curr:
            res = curr.execute(sql_statement)

    return {
        "statusmessage": res.statusmessage,
        "rowcount": res.rowcount,
    }


def delete_variable_record(file_name: str, conn_details: dict[str, str]) -> list[tuple]:
    """Deletes the records matching the VRT file name"""
    sql_statement = sql.SQL(
        """DELETE FROM public.variables WHERE filename = {val_filename}
        RETURNING *"""
    ).format(
        val_filename=sql.Literal(file_name),
    )

    with psycopg.connect(**conn_details, autocommit=True) as conn:
        with conn.cursor() as curr:
            res = curr.execute(sql_statement).fetchall()

    return res


def list_variables_records(
    conn_details: dict[str, str], forecast_string_like_pattern: str = ""
) -> pd.DataFrame:
    if forecast_string_like_pattern == "":
        sql_statement = sql.SQL(
            """
                SELECT * FROM {table}
            """
        ).format(table=sql.Identifier("public", "variables"))
    else:
        sql_statement = sql.SQL(
            """
                SELECT * FROM {table}
                WHERE {col_forecast_string} LIKE {val_forecast_string_filter}
            """
        ).format(
            table=sql.Identifier("public", "variables"),
            col_forecast_string=sql.Identifier("forecast_string"),
            val_forecast_string_filter=sql.Literal(forecast_string_like_pattern),
        )

    return execute_sql_as_dataframe(conn_details, sql_statement)


def list_orphan_bucket_objects(
    filter_pattern: str, aws_bucket: str, conn_details: dict[str, str]
):
    """Finds all orphaned bucket objects and returns the orphans containing the filter_pattern"""
    print("Searching for orphaned objects...")
    complete_object_listing = get_s3_filelisting(aws_bucket=aws_bucket)

    variables_in_postgis = list_variables_records(
        conn_details=conn_details,
        forecast_string_like_pattern=f"%{filter_pattern}%",
    )
    # print(f"""{len(variables_in_postgis["filename"])} variables in PostGIS.""")

    orphaned_objects = []
    for file in complete_object_listing:
        orphan = True
        if filter_pattern not in file["Key"]:
            # print(
            #     "Excluded by filter pattern. object name:",
            #     file["Key"],
            #     "filter_pattern:",
            #     filter_pattern,
            # )
            continue
        for forecast_string in variables_in_postgis["forecast_string"].values:
            if forecast_string in file["Key"]:
                # print(
                #     "Valid. object name:",
                #     file["Key"],
                #     "forecast_string:",
                #     forecast_string,
                # )
                orphan = False
                break
        if orphan:
            print(
                "Orphan. object name:",
                file["Key"],
                # "filter_pattern:",
                # filter_pattern,
            )
            orphaned_objects.append(file)

    print(f"{len(orphaned_objects)} orphaned objects.")
    return orphaned_objects


def list_latest_variable_records(conn_details: dict[str, str]) -> pd.DataFrame:
    """Return the most recent instance of each variable loaded."""
    sql_statement = sql.SQL(
        """
        with latest as (
            select
                forecast_base_string ,
                max(forecast_start_timestamp) as forecast_start_timestamp
            from variables v
            group by forecast_base_string
        )
        select
            v.*
        from variables v
        inner join latest on
            v.forecast_base_string = latest.forecast_base_string
            and v.forecast_start_timestamp = latest.forecast_start_timestamp
    """
    )
    return execute_sql_as_dataframe(conn_details=conn_details, sql_query=sql_statement)


def list_old_variable_records(conn_details: dict[str, str]) -> pd.DataFrame:
    """Return out-dated instances of each variable loaded."""
    sql_statement = sql.SQL(
        """
        with latest as (
            select
                forecast_base_string ,
                max(forecast_start_timestamp) as forecast_start_timestamp
            from variables v
            group by forecast_base_string
        )
        select
            v.*
        from variables v
        inner join latest on
            v.forecast_base_string = latest.forecast_base_string
            and v.forecast_start_timestamp != latest.forecast_start_timestamp
    """
    )
    return execute_sql_as_dataframe(conn_details=conn_details, sql_query=sql_statement)


def does_prediction_data_exist(
    conn_details: dict[str, str], forecast_string: str
) -> bool:
    sql_statement = sql.SQL(
        """
        select distinct
	        filename
        from predictions p
        where filename = {forecast_string}
        """
    ).format(forecast_string=sql.Literal(f"{forecast_string}.vrt"))
    predictions = execute_sql_as_dataframe(
        conn_details=conn_details, sql_query=sql_statement
    )

    return len(predictions) > 0
