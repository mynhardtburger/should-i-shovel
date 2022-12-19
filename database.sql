DROP SCHEMA IF EXISTS public CASCADE;

CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION myn;

COMMENT ON SCHEMA public IS 'standard public schema';
-- public.variables definition

-- Drop table

DROP TABLE IF EXISTS public.variables;

CREATE TABLE IF NOT EXISTS public.variables (
	variable_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	short_name text NOT NULL UNIQUE, -- variable short name
	long_name text NOT NULL, -- variable long name
	unit text NOT NULL, -- unit of measurement
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

DROP TABLE IF EXISTS public.forecasts;

CREATE TABLE IF NOT EXISTS public.forecasts (
	forecast_id int4 NOT NULL GENERATED ALWAYS AS IDENTITY,
	model text NOT NULL, -- model acronym from which the forecast originates
	forecast_reference_time timestamptz NOT NULL, -- initial time of forecast
	forecast_step interval NOT NULL, -- time since forecast_reference_time
	CONSTRAINT forecasts_pk PRIMARY KEY (forecast_id),
    UNIQUE(model, forecast_reference_time, forecast_step)
);

-- Column comments

COMMENT ON COLUMN public.forecasts.forecast_reference_time IS 'initial time of forecast';
COMMENT ON COLUMN public.forecasts.model IS 'model acronym from which the forecast originates';
COMMENT ON COLUMN public.forecasts.forecast_step IS 'time since forecast_reference_time';

-- Permissions

ALTER TABLE public.forecasts OWNER TO myn;
GRANT ALL ON TABLE public.forecasts TO myn;


-- public.predictions definition

-- Drop table

DROP TABLE IF EXISTS public.predictions;

CREATE TABLE IF NOT EXISTS public.predictions (
	forecast_id int4 NOT NULL,
	variable_id int4 NOT NULL,
	longitude float4 NOT NULL, -- x y coordinates of prediction
	latitude float4 NOT NULL, -- x y coordinates of prediction
	-- coordinates point NOT NULL, -- x y coordinates of prediction
	value float4 NULL, -- forecasted variable value
	CONSTRAINT forecasts_fk FOREIGN KEY (variable_id) REFERENCES public.variables(variable_id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT predictions_fk FOREIGN KEY (forecast_id) REFERENCES public.forecasts(forecast_id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE(forecast_id, variable_id, longitude, latitude)
);

-- Column comments

-- COMMENT ON COLUMN public.predictions.coordinates IS 'x y coordinates of prediction';
COMMENT ON COLUMN public.predictions.value IS 'forecasted variable value';

-- Permissions

ALTER TABLE public.predictions OWNER TO myn;
GRANT ALL ON TABLE public.predictions TO myn;




-- Permissions

GRANT ALL ON SCHEMA public TO myn;
GRANT ALL ON SCHEMA public TO public;
