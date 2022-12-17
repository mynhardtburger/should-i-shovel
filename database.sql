-- DROP SCHEMA public;

CREATE SCHEMA public AUTHORIZATION myn;

COMMENT ON SCHEMA public IS 'standard public schema';
-- public.variables definition

-- Drop table

-- DROP TABLE public.variables;

CREATE TABLE public.variables (
	short_name text NOT NULL, -- variable short name
	unit text NOT NULL, -- unit of measurement
	long_name text NOT NULL, -- variable long name
	variable_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	CONSTRAINT variables_pk PRIMARY KEY (variable_id)
);

-- Column comments

COMMENT ON COLUMN public.variables.short_name IS 'variable short name';
COMMENT ON COLUMN public.variables.unit IS 'unit of measurement';
COMMENT ON COLUMN public.variables.long_name IS 'variable long name';

-- Permissions

ALTER TABLE public.variables OWNER TO myn;
GRANT ALL ON TABLE public.variables TO myn;


-- public.forecasts definition

-- Drop table

-- DROP TABLE public.forecasts;

CREATE TABLE public.forecasts (
	forecast_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	forecast_reference_time timestamptz NOT NULL, -- initial time of forecast
	model text NOT NULL, -- model acronym from which the forecast originates
	CONSTRAINT forecasts_pk PRIMARY KEY (forecast_id)
);

-- Column comments

COMMENT ON COLUMN public.forecasts.forecast_reference_time IS 'initial time of forecast';
COMMENT ON COLUMN public.forecasts.model IS 'model acronym from which the forecast originates';

-- Permissions

ALTER TABLE public.forecasts OWNER TO myn;
GRANT ALL ON TABLE public.forecasts TO myn;


-- public.predictions definition

-- Drop table

-- DROP TABLE public.predictions;

CREATE TABLE public.predictions (
	coordinates point NOT NULL, -- x y coordinates of prediction
	forecast_id int4 NOT NULL,
	variable_id int4 NOT NULL,
	value float4 NULL, -- forecasted variable value
	forecast_hour int4 NOT NULL, -- hours since forecast_reference_time
	CONSTRAINT forecasts_fk FOREIGN KEY (variable_id) REFERENCES public.variables(variable_id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT predictions_fk FOREIGN KEY (forecast_id) REFERENCES public.forecasts(forecast_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Column comments

COMMENT ON COLUMN public.predictions.coordinates IS 'x y coordinates of prediction';
COMMENT ON COLUMN public.predictions.value IS 'forecasted variable value';
COMMENT ON COLUMN public.predictions.forecast_hour IS 'hours since forecast_reference_time';

-- Permissions

ALTER TABLE public.predictions OWNER TO myn;
GRANT ALL ON TABLE public.predictions TO myn;




-- Permissions

GRANT ALL ON SCHEMA public TO myn;
GRANT ALL ON SCHEMA public TO public;
