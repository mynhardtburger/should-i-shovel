from typing import Union, Optional, TypeAlias, Sequence, Mapping, Any
import psycopg
from psycopg import sql
import pandas as pd

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
                return pd.DataFrame(res, columns=columns)
            return pd.DataFrame()

def get_nearest_predictions_as_df(conn_details: dict[str, str], lat: float, lon: float) -> pd.DataFrame:
    """Obtains the nearest prediction to the coordinates provided returing the data in a dataframe."""
    query = sql.SQL(
        """
        with coord as (
            select
                c.coord_id ,
                c.latitude ,
                c.longitude
            from public.coordinates c
            order by c.coord_point <-> '({latitude}, {longitude})'
            limit 1
        )
        select
            f.forecast_reference_time ,
            f.forecast_reference_time + f.forecast_step as forecast_time ,
            c.latitude ,
            c.longitude ,
            v.short_name ,
            v.long_name ,
            value ,
            v.unit
        FROM predictions p
        inner join coord c on p.coord_id = c.coord_id
        inner join public.forecasts f on p.forecast_id = f.forecast_id
        inner join public.variables v on p.variable_id = v.variable_id
        order by forecast_time asc;
    """
    ).format(
        latitude=sql.Literal(lat),
        longitude=sql.Literal(lon),
    )
    return execute_sql_as_dataframe(conn_details, query)
