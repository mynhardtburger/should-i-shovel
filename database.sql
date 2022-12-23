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
	latitude float8 NOT NULL,
	longitude float8 NOT NULL,
	cube_coordinate public."cube" NULL,
	coord_point point NULL,
	CONSTRAINT coordinates_pk PRIMARY KEY (coord_id)
);
CREATE INDEX idx_spgist_coordinates_point ON public.coordinates USING spgist (coord_point);

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
CREATE INDEX predictions_coord_id_idx ON public.predictions USING btree (coord_id);


-- public.predictions foreign keys


-- Permissions

ALTER TABLE public.predictions OWNER TO myn;
GRANT ALL ON TABLE public.predictions TO myn;

-- public.test definition

-- Drop table

-- DROP TABLE public.test;

CREATE TABLE public.test (
	coord_id int4 NOT NULL,
	forecast_id int4 NOT NULL,
	variable_id int4 NOT NULL,
	"value 00" float4,
	"value 01" float4,
	"value 02" float4,
	"value 03" float4,
	"value 04" float4,
	"value 05" float4,
	"value 06" float4,
	"value 07" float4,
	"value 08" float4,
	"value 09" float4,
	"value 10" float4,
	"value 11" float4,
	"value 12" float4,
	"value 13" float4,
	"value 14" float4,
	"value 15" float4,
	"value 16" float4,
	"value 17" float4,
	"value 18" float4,
	"value 19" float4,
	"value 20" float4,
	"value 21" float4,
	"value 22" float4,
	"value 23" float4,
	"value 24" float4,
	"value 25" float4,
	"value 26" float4,
	"value 27" float4,
	"value 28" float4,
	"value 29" float4,
	"value 30" float4,
	"value 31" float4,
	"value 32" float4,
	"value 33" float4,
	"value 34" float4,
	"value 35" float4,
	"value 36" float4,
	"value 37" float4,
	"value 38" float4,
	"value 39" float4,
	"value 40" float4,
	"value 41" float4,
	"value 42" float4,
	"value 43" float4,
	"value 44" float4,
	"value 45" float4,
	"value 46" float4,
	"value 47" float4,
	"value 48" float4,
    CONSTRAINT test_pk PRIMARY KEY (coord_id, forecast_id, variable_id)
);
CREATE INDEX test_coord_id_idx ON public.test USING btree (coord_id);

-- Permissions

ALTER TABLE public.test OWNER TO myn;
GRANT ALL ON TABLE public.test TO myn;


-- public.test foreign keys

ALTER TABLE public.test ADD CONSTRAINT test_coord_fk FOREIGN KEY (coord_id) REFERENCES public.coordinates(coord_id) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE public.test ADD CONSTRAINT test_forecast_fk FOREIGN KEY (forecast_id) REFERENCES public.forecasts(forecast_id) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE public.test ADD CONSTRAINT test_variable_fk FOREIGN KEY (variable_id) REFERENCES public.variables(variable_id) ON DELETE CASCADE ON UPDATE CASCADE;


-- Permissions

GRANT ALL ON SCHEMA public TO myn;
GRANT ALL ON SCHEMA public TO public;
