# Should I Shovel?

## Introduction
I wanted to know when I would need to shovel snow. Will there be sufficient snowfall in the near future to need shoveling considering that it might melt shortly after falling?
To answer this I'm building a small web app. My focus is not on the forecasting element, which is very difficult even for the professionals, but rather the infrastructure:
* Working with weather data (raster formats) using PostGIS
* AWS RDS, S3, EC2
* Terraform infrastructure as code
* Docker containers
* Orchestration and scheduling of data refreshes (currently Airflow, but might use something simpler)
* Basic python api backend using FastAPI
* Based front end using chart.js and google maps
* GitHub Actions CI/CD

## Status

### Todo
- [ ] Finalize terraform/docker structure so that updates can be pushed via git commits
- [ ] Setup auto data refresh schedule
- [ ] Implement graphs for all weather variables in front end
    - [ ] Text verbage of should I shovel? No, likely & when
    - [x] Highlight timeband during which shoveling is likely necessary "shovel time"
    - [x] Added shoveltime flag to data set which API makes available
    - [x] Graph labels/colors/legends are correct
    - [x] Graphs updates with data
- [x] Implement map in front end
- [x] Finalize API queries to PostGIS to retrieve data
- [x] Complete data refresh logic
    - [x] Data clean up after successful load
    - [x] Load raster data to PostGIS
    - [x] Retrieve latest grib2 files
    - [x] Determine latest forecast

### 2023-01-20
* Back end:
    * Removed unnecessary variables from refresh code
    * implemented shoveltime algorithm

* Front end:
    * updates to be compatible with new api data structure
    * graphs updated to show shoveltime

### 2023-01-19
* Back end:
    * Finalized variable selection
    * Updated import procedures and API to be compatible with the slighly different source.

* Front end:
    * Graph lables, colors, scales, legends corrected.

### 2023-01-18
* Front end:
    * Graphs are created for each variable and updates with data as you click on the map.

### 2023-01-17
* Refresh logic:
    * Implemented api endpoints to perform the data cleanup to ensure that the S3 bucket only holds live data.
    * Now checks the DB to see if the existing forecast is stale before attempting to download the new forecast.
    * get_forecast api end point data structure updated to return list of forecasts split by forecast variable to simplify front end logic.
* Front end:
    * Implemented google maps map. Was simpler to implement compared to leaflet.
    * On load centers at user's location using browser's geolocation.
    * clicking on the map triggers API call to fetch forecast for the location.
    * Graphs of results still work in progress.
    * Switch to webpack for bundling from parcel.
### 2023-01-12
First public commit. The repo is still quite messy, but the structure of the infrastructure and roughly defined and many of the API functions have been coded.
