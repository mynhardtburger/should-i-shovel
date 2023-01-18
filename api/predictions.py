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


def get_nearest_predictions_as_df(
    conn_details: dict[str, str], latitude: float, longitude: float
) -> list[pd.DataFrame]:
    """Obtains the nearest prediction to the coordinates provided returing the data in a dataframe."""
    query = sql.SQL(
        """
        with coords as (
            select
                {latitude} as latitude,
                {longitude} as longitude
        ),
        pt AS (
            SELECT
                ST_Transform(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), 990000) AS pt
            from coords
        ),
        latest as (
            select
                forecast_base_string,
                max(forecast_start_timestamp) as forecast_start_timestamp
            from variables v
            group by forecast_base_string
        ),
        var_details as (
        select
            v2.filename ,
            v2.forecast_string ,
            v2.variable ,
            v2.leveltype ,
            v2."level" ,
            v2.forecast_start_timestamp
        from variables v2
        inner join latest on
            latest.forecast_start_timestamp = v2.forecast_start_timestamp
            and latest.forecast_base_string = v2.forecast_base_string
        )
        SELECT
            b - 1 as band,
            ST_Value(raster, b, pt.pt) as value,
            latitude,
            longitude,
            variable,
            leveltype ,
            var_details.level,
            forecast_start_timestamp ,
            forecast_start_timestamp + interval '1 hour' * (b -1) as forecast_timestamp
        FROM predictions p
            cross join coords
            CROSS JOIN pt
            CROSS JOIN generate_series(1, 49) b
            inner join var_details on var_details.filename = p.filename
        WHERE ST_Intersects(pt.pt, st_convexhull(raster))
        order by latitude, longitude, variable, leveltype, level, forecast_timestamp;
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
            df_list.append(df.loc[df["variable"] == var].to_dict("list"))
        return df_list
    return [df]
