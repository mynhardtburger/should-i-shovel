#!/bin/bash

set -e

echo "Apply custom setup to $POSTGRES_DB"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis_raster;
    INSERT INTO spatial_ref_sys (srid, proj4text) values (990000, '+proj=stere +lat_0=90 +lat_ts=60 +lon_0=252 +x_0=0 +y_0=0 +R=6371229 +units=m +no_defs');

    CREATE TABLE public.predictions (
        rid serial PRIMARY KEY,
	    raster raster NOT NULL,
	    filename text NOT NULL
    );
    CREATE INDEX ON "public"."predictions" USING gist (st_convexhull("raster"));

    CREATE TABLE public.variables (
        filename text NOT NULL,
        forecast_string text NOT NULL,
        forecast_start_timestamp timestamptz NOT NULL,
        source text NOT NULL,
        model text NOT NULL,
        domain text NOT NULL,
        variable text NOT NULL,
        leveltype text NOT NULL,
        level text NOT NULL,
        resolution text NOT NULL,
        CONSTRAINT variables_pk PRIMARY KEY (filename)
    );

    ALTER TABLE public.predictions ADD CONSTRAINT predictions_fk FOREIGN KEY (filename) REFERENCES public.variables(filename) ON DELETE CASCADE ON UPDATE CASCADE;
EOSQL