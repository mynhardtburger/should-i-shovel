#!/bin/bash

set -e

echo "Apply custom setup to $POSTGRES_DB"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis_raster;
    INSERT INTO spatial_ref_sys (srid, proj4text) values (990000, '+proj=stere +lat_0=90 +lat_ts=60 +lon_0=252 +x_0=0 +y_0=0 +R=6371229 +units=m +no_defs');
    INSERT INTO spatial_ref_sys (srid, proj4text) values (990001, '+proj=ob_tran +o_proj=longlat +o_lon_p=0 +o_lat_p=36.08852 +lon_0=-114.694858 +R=6371229 +no_defs');

    CREATE TABLE public.predictions (
        rid serial PRIMARY KEY,
	    raster raster NOT NULL,
	    filename text NOT NULL
    );
    CREATE INDEX ON "public"."predictions" USING gist (st_convexhull("raster"));

    CREATE TABLE public.variable_definitions (
        model text NOT NULL,
        variable text NOT NULL,
        description text NULL,
        unit text NOT NULL,
        notes text NULL,
        CONSTRAINT variable_definitions_pk PRIMARY KEY (model,variable)
    );

    COPY variable_definitions("model", "variable", "description", "unit", "notes")
    FROM '/var/lib/postgresql/variables.csv' (delimiter ',', header TRUE);

    CREATE TABLE public.variables (
        filename text NOT NULL,
        forecast_base_string text NOT NULL,
        forecast_string text NOT NULL,
        forecast_start_timestamp timestamptz NOT NULL,
        source text NOT NULL,
        model text NOT NULL,
        variable text NOT NULL,
        leveltype text NOT NULL,
        level text NOT NULL,
        resolution text NOT NULL,
        CONSTRAINT variables_pk PRIMARY KEY (filename)
    );

    ALTER TABLE public.predictions ADD CONSTRAINT predictions_fk FOREIGN KEY (filename) REFERENCES public.variables(filename) ON DELETE CASCADE ON UPDATE CASCADE;
    ALTER TABLE public.variables ADD CONSTRAINT variables_fk FOREIGN KEY (model,variable) REFERENCES public.variable_definitions(model,variable);
EOSQL