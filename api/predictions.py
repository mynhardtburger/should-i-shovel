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
            print(f"Rows impacted: {curr.rowcount}")

            if curr.description:
                columns = [col.name for col in curr.description]
                df = pd.DataFrame(res, columns=columns)
                return df
            return pd.DataFrame()


def get_nearest_predictions_as_df(
    conn_details: dict[str, str], table: str, lat: float, lon: float
) -> pd.DataFrame:
    """Obtains the nearest prediction to the coordinates provided returing the data in a dataframe."""
    query = sql.SQL(
        """
        with coords as (
        select
            {latitude} as lat,
            {longitude} as lon
        ),
        pt AS (
        SELECT ST_Transform(ST_SetSRID(ST_MakePoint(lat, lon), 4326), 990000) AS pt
        from coords
        )
        SELECT
            b as band,
            ST_Value(raster, b, pt.pt) as value,
            lat,
            lon
        FROM {table}
            cross join coords
            CROSS JOIN pt
            CROSS JOIN generate_series(1, 48) b
        WHERE ST_Intersects(pt.pt, st_convexhull(raster));
    """
    ).format(
        latitude=sql.Literal(lat),
        longitude=sql.Literal(lon),
        table=sql.Identifier(table),
    )
    return execute_sql_as_dataframe(conn_details, query)
