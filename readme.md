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
* Based front end using chart.js and leaflet for maps
* GitHub Actions CI/CD

## Status

### Todo
- [ ] Finalize terraform/docker structure so that updates can be pushed via git commits
- [ ] Setup auto data refresh schedule
- [ ] Implement map in front end
- [ ] Implement graphs for all weather variables in front end
- [ ] Finalize API queries to PostGIS to retrieve data
- [ ] Complete data refresh logic
    - [ ] Data clean up after successful load
    - [x] Load raster data to PostGIS
    - [x] Retrieve latest grib2 files
    - [x] Determine latest forecast


### 2023-01-12
First public commit. The repo is still quite messy, but the structure of the infrastructure and roughly defined and many of the API functions have been coded.
