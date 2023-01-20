from typing import Any, Mapping, Optional, Sequence, TypeAlias, Union

import pandas as pd
import psycopg
from psycopg import sql

Query: TypeAlias = Union[bytes, "sql.SQL", "sql.Composed"]
Params: TypeAlias = Union[Sequence[Any], Mapping[str, Any]]


def execute_sql_as_dataframe(
    conn_details: dict[str, str],
    sql_query: Query,
    params: Optional[Params] = None,
) -> pd.DataFrame:
    """Execute SQL query and return results in a DataFrame"""
    with psycopg.connect(**conn_details, autocommit=True) as conn:
        with conn.cursor() as curr:
            res = curr.execute(sql_query, params).fetchall()
            # print(f"Rows impacted: {curr.rowcount}")

            if curr.description:
                columns = [col.name for col in curr.description]
                df = pd.DataFrame(res, columns=columns)
                return df
            return pd.DataFrame()


def get_predictions_as_dict(
    conn_details: dict[str, str], latitude: float, longitude: float
) -> list[pd.DataFrame]:
    """Obtains the nearest prediction to the coordinates provided returing the data in a dataframe."""
    query = sql.SQL(
        """
        WITH coords AS (
            SELECT
                {latitude} AS latitude,
                {longitude} AS longitude
        ),
        pt AS (
            SELECT
                ST_Transform(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), 990001) AS pt
            FROM coords
        ),
        latest as (
            SELECT
                forecast_base_string,
                max(forecast_start_timestamp) as forecast_start_timestamp
            FROM variables v
            group by forecast_base_string
        ),
        var_details AS (
        SELECT
            v2.filename ,
            v2.forecast_string ,
            v2.variable ,
            v2.model ,
            v2.leveltype ,
            v2."level" ,
            v2.forecast_start_timestamp
        FROM variables v2
        INNER JOIN latest ON
            latest.forecast_start_timestamp = v2.forecast_start_timestamp
            AND latest.forecast_base_string = v2.forecast_base_string
        )
        SELECT
            b - 1 AS band,
            ST_Value(raster, b, pt.pt) as value,
            variable_definitions.unit,
            latitude,
            longitude,
            var_details.model,
            var_details.variable,
            variable_definitions.description AS "variable_description",
            leveltype ,
            var_details.level,
            forecast_start_timestamp ,
            forecast_start_timestamp + interval '1 hour' * (b -1) AS forecast_timestamp
        FROM predictions p
            CROSS JOIN coords
            CROSS JOIN pt
            CROSS JOIN generate_series(1, 48) b
            INNER JOIN var_details on var_details.filename = p.filename
            LEFT JOIN variable_definitions ON
                var_details.variable = variable_definitions.variable
                AND var_details.model = variable_definitions.model
        WHERE ST_Intersects(pt.pt, st_convexhull(raster))
        ORDER BY latitude, longitude, variable, leveltype, level, forecast_timestamp;
    """
    ).format(
        latitude=sql.Literal(latitude),
        longitude=sql.Literal(longitude),
        # table=sql.Identifier(table),
    )
    df = execute_sql_as_dataframe(conn_details, query)
    if len(df) > 0:
        df_list = []
        for var in df["variable"].unique():
            df_list.append(df.loc[df["variable"] == var])
        return df_list
    return [df]


def df_details(df: pd.DataFrame) -> dict:
    for col in ["value", "band", "forecast_timestamp"]:
        assert col in df.columns
    return df.drop(columns=["value", "band", "forecast_timestamp"]).iloc[0, :].to_dict()


def format_predictions(df_list: list[pd.DataFrame]) -> pd.DataFrame:
    """Format results and apply shoveltime algorithm"""
    if len(df_list[0]) == 0:
        return df_list[0]

    # https://en.wikipedia.org/wiki/Enthalpy_of_fusion
    LATENT_HEAT_OF_FUSION = 333.55  # joules per gram needed to change phase of water from solid to liquid with no change in temperature

    # https://glossary.ametsoc.org/wiki/Snow_density#:~:text=Freshly%20fallen%20snow%20usually%20has,American%20Meteorological%20Society%20(AMS).
    SNOW_DENSITY = 0.2  # Conservative estimate.

    # Rough estimate based on little to no airflow. https://www.engineeringtoolbox.com/convective-heat-transfer-d_430.html
    HEAT_TRANSFER_COEFFICIENT = (
        25  # joules per second per square meter for each K of temperature difference.
    )

    SHOVEL_DEPTH_THRESHOLD = 10  # millimeters

    def df_format(df: pd.DataFrame) -> pd.DataFrame:
        for col in ["band", "forecast_timestamp", "value", "unit"]:
            assert col in df.columns

        return (
            df.loc[:, ["band", "forecast_timestamp", "value"]]
            .rename(columns={"value": df_details(df)["unit"]})
            .set_index(["band", "forecast_timestamp"])
        )

    def energy_balance(df: pd.DataFrame) -> list:
        for col in ["snow_latent_heat_equivalent", "interval_heat_transfer_potential"]:
            assert col in df.columns

        energy_balance = []
        for row in combined_df.itertuples():
            incremental_latent_energy = row.snow_latent_heat_equivalent + min(
                row.interval_heat_transfer_potential, 0
            )
            if not energy_balance:
                energy_balance.append(max(incremental_latent_energy, 0))
                continue
            energy_balance.append(
                max(energy_balance[-1] + incremental_latent_energy, 0)
            )
        return energy_balance

    # Main logic starts here
    combined_df = pd.concat([df_format(df) for df in df_list], axis="columns")
    # 1 mm of precipitation over 1 sqm = 1 liter which is approx 1kg. Snow has a lower density and we want the result in grams.
    combined_df["snow_weight"] = combined_df["mm"] * SNOW_DENSITY * 1000
    combined_df["snow_latent_heat_equivalent"] = (
        combined_df["snow_weight"] * LATENT_HEAT_OF_FUSION
    )
    combined_df["interval_heat_transfer_potential"] = (
        60 * 60 * HEAT_TRANSFER_COEFFICIENT * combined_df["C"] * -1
    )
    combined_df = combined_df.assign(
        snow_latent_heat_balance=energy_balance(combined_df)
    )
    combined_df["estimated_snow_height"] = (
        combined_df["snow_latent_heat_balance"]
        / LATENT_HEAT_OF_FUSION
        / SNOW_DENSITY
        / 1000
    )
    combined_df["shovel_time"] = (
        combined_df["estimated_snow_height"] >= SHOVEL_DEPTH_THRESHOLD
    )

    return combined_df.reset_index()
