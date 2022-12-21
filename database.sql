DROP SCHEMA public CASCADE;

CREATE SCHEMA public AUTHORIZATION myn;

-- DROP SEQUENCE public.forecasts_forecast_id_seq;

CREATE SEQUENCE public.forecasts_forecast_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.forecasts_forecast_id_seq OWNER TO myn;
GRANT ALL ON SEQUENCE public.forecasts_forecast_id_seq TO myn;

-- DROP SEQUENCE public.variables_variable_id_seq;

CREATE SEQUENCE public.variables_variable_id_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 2147483647
	START 1
	CACHE 1
	NO CYCLE;

-- Permissions

ALTER SEQUENCE public.variables_variable_id_seq OWNER TO myn;
GRANT ALL ON SEQUENCE public.variables_variable_id_seq TO myn;
-- public.forecasts definition

-- Drop table

-- DROP TABLE public.forecasts;

CREATE TABLE public.forecasts (
	forecast_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	model text NOT NULL,
	forecast_reference_time timestamptz NOT NULL,
	forecast_step interval NOT NULL,
	CONSTRAINT forecasts_model_forecast_reference_time_forecast_step_key UNIQUE (model, forecast_reference_time, forecast_step),
	CONSTRAINT forecasts_pk PRIMARY KEY (forecast_id)
);

-- Permissions

ALTER TABLE public.forecasts OWNER TO myn;
GRANT ALL ON TABLE public.forecasts TO myn;


-- public.variables definition

-- Drop table

-- DROP TABLE public.variables;

CREATE TABLE public.variables (
	variable_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	short_name text NOT NULL,
	long_name text NOT NULL,
	unit text NOT NULL,
	CONSTRAINT variables_pk PRIMARY KEY (variable_id),
	CONSTRAINT variables_short_name_key UNIQUE (short_name)
);

-- Permissions

ALTER TABLE public.variables OWNER TO myn;
GRANT ALL ON TABLE public.variables TO myn;


-- public.coordinates definition

-- Drop table

-- DROP TABLE public.coordinates;

CREATE TABLE public.coordinates (
	coord_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	latitude float4 NOT NULL,
	longitude float4 NOT NULL,
	CONSTRAINT coordinates_pk PRIMARY KEY (coord_id),
	CONSTRAINT lonlat UNIQUE (latitude, longitude)
);

-- Permissions

ALTER TABLE public.coordinates OWNER TO myn;
GRANT ALL ON TABLE public.coordinates TO myn;


-- public.predictions definition

-- Drop table

-- DROP TABLE public.predictions;

CREATE TABLE public.predictions (
	forecast_id int4 NOT NULL,
	variable_id int4 NOT NULL,
	value float4 NULL,
	coord_id int4 NOT NULL,
	CONSTRAINT coord_fk FOREIGN KEY (coord_id) REFERENCES public.coordinates(coord_id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT forecasts_fk FOREIGN KEY (variable_id) REFERENCES public.variables(variable_id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT predictions_fk FOREIGN KEY (forecast_id) REFERENCES public.forecasts(forecast_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Permissions

ALTER TABLE public.predictions OWNER TO myn;
GRANT ALL ON TABLE public.predictions TO myn;




-- Permissions

GRANT ALL ON SCHEMA public TO myn;
GRANT ALL ON SCHEMA public TO public;
