## description of project

## required components
* What data is available?
    * Fromat: GRIB2 / NetCDF
    * Frequency: Multiple refreshes a day
    * Volume: 2576x1456 grid * 49 predication slices * float4 = approx 700MB of raw data. This excludes indexes, overhead and metadata. Prior to compression. Single variable (eg. temperature at surface level)
    * Description: A variable represents a measurement type (eg. temperature) usually at some altitude (surface/water level vs above ground measured in air pressure).
    * Types of data sets: Determinastic = 1 answer for each variable at each coordinate point. Probabalistic = multiple possible results for each variable at each coordinate point.
    * [Raster data](https://datacarpentry.org/organization-geospatial//01-intro-raster-data/index.html)

* GUI tools:
    * [QGIS](https://eccc-msc.github.io/open-data/usage/tutorial_raw-data_QGIS_en/)

* CLI tools:
    * [GDAL](https://gdal.org/index.html) which is a translator library for raster and vector geospatial data formats. Installable via the *gdal-bin* package on ubuntu/debian based systems.
        * [gdalinfo](https://gdal.org/programs/gdalinfo.html#gdalinfo) lists information about a raster dataset (eg. GRIB).
    * [eCcodes](https://confluence.ecmwf.int/display/ECC/What+is+ecCodes) is an API and set of tools for decoding and encoding messages in the GRIB and BUFR formats. Installable via the *libgrib-api-tools* package on ubuntu/debian based systems.
        * [grib_ls](https://confluence.ecmwf.int/display/ECC/grib_ls) lists the content of GRIB files printing values of some keys.
        * [grib_get_data](https://confluence.ecmwf.int/display/ECC/grib_get_data) prints a latitude, longitude, data values list. Note: Rotated grids are first unrotated.
    * [raster2pgsql](https://postgis.net/docs/using_raster_dataman.html) is a raster loader executable that loads GDAL supported raster formats into sql suitable for loading into a PostGIS raster table. Installable via the *postgis* package on ubuntu/debian systems.
    * [gdalbuildvrt](https://gdal.org/programs/gdalbuildvrt.html) builds a virtual dataset (VRT) from separate input gdal datasets. This can be used to combine multiple GRIB files into a tiled mosaic or a single raster stacked with each file representing a different band (-separate option).

* Data retrieval method
    * Advanced Message Queuing Protocol - specifically [Sarracenia](https://metpx.github.io/sarracenia/)
    * HTTP download

* Data storage
    * S3 for raw GRIB2 data files
    * PostgreSQL as query source
    * PostgreSQL extension to import directly from S3
    * [PostGIS](https://postgis.net/) is an extension for PostgreSQL enabling spatial databases (eg. raster tables)

* Data loading
    * [Optimized bulk loading in Amazon RDS for PostgreSQL](https://aws.amazon.com/blogs/database/optimized-bulk-loading-in-amazon-rds-for-postgresql/)
    * Naive approach:
        * [pygrib](https://jswhit.github.io/pygrib/) to read GRIB2. Approx 2 seconds per file.
        Also tested [xarray using the cfgrib engin](https://docs.xarray.dev/en/stable/examples/ERA5-GRIB-example.html) but found that it was slightly slower tha pygrib. Both approaches uses the ecCodes library under the hood.
        * [psycopg](https://www.psycopg.org/psycopg3/docs/index.html) to write to Postgres DB
            * [cursor.executemany()](https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.Cursor.executemany) is unusably slow.
            * [copy.write_row()](https://www.psycopg.org/psycopg3/docs/api/copy.html#psycopg.Copy.write_row) works but is still slow. I used a pandas.DataFrame.intertuples(index=False) as input.
            * [copy.write()](https://www.psycopg.org/psycopg3/docs/api/copy.html#psycopg.Copy.write) performs similar to write_row().
    * Filesystem load:
        1. [Extract GRIB2 to csv](https://confluence.ecmwf.int/display/CKB/How+to+convert+GRIB+to+CSV)
            * grib_get_data -L "%.6f %.6f" -F "%.4f" CMC_hrdps_continental_SNOD_SFC_0_ps2.5km_2022122000_P021-00.grib2 > temp.csv
            * Note that longitude coordinates are given in [0, 360] range. Need to convert it to a [-180, 180] range. All our latitudes are in the western hemisphere hence we can 360 - latitude = negative degrees west. There are some challanges with rounding errors.
        2. PostgreSQL copy statement to load to temp table
        3. SQL to format and load to main table
    * PostGIS load:
        1. If required register your custom SRID:
            ```sql
            insert into spatial_ref_sys (srid, proj4text)
            values (
                990000,
                '+proj=stere +lat_0=90 +lat_ts=60 +lon_0=252 +x_0=0 +y_0=0 +R=6371229 +units=m +no_defs'
            );
            ```
        2. Optionally create a multiband VRT using gdalbuildvrt:
            ```shell
            gdalbuildvrt -separate test.vrt CMC_hrdps_continental_SNOD_SFC_0_ps2.5km_2022122000_P0*.grib2
            ```
        3. Using [raster2pgsql](https://postgis.net/docs/using_raster_dataman.html) to load directly from GRIB2 to PostGIS raster table.
            ```shell
            raster2pgsql -d -I -q -t "auto" -s 990000 CMC_hrdps_continental_SNOD_SFC_0_ps2.5km_2022122000_P021-00.grib2 public.raster > test.sql
            ```

* Data modeling
   * Naive approach:
        * ![ERD](/images/ERD.png)
        * Using <@> operator for [point based earth distances](https://www.postgresql.org/docs/current/earthdistance.html)
        * Correct use of index makes a big difference: btree on lat/lng coordiantes is slow. spgist on point data is very fast.
        * Does work for queries. Given a coordinate, returning the nearest set of results is <30ms
        * Challanges:
            * Very large data storage. Close to 1GB for coordinates and 9GB for predication data.
            * Significant overhead/wastage due to 4byte data in 8byte page + 24bytes of row overhead + large indexes due to row count. There ends up being much more overhead than actual data.
            * Slow updates/refresh of data due to volume