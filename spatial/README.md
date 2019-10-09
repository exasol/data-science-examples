# Exasol Spatial Demo with Jupyter Notebook

[
Geospatial data](https://docs.exasol.com/sql_references/geospatialdata.htm) can be stored and analyzed in the Exasol database using the GEOMETRY datatype. In this solution, we will show you some examples of how to work with geospatial data inside a Jupyter Notebook with the help of SQL inline magic and visualize geospatial data on map using Python libraries. 

# Table of contents

<!-- toc -->

- [Prerequisites](#prerequisites)
- [Datasets](#datasets)
- [Use Cases](#use-cases)
- [External Resources](#external-resources)

<!-- tocstop -->

### Prerequisites  

To run this demo a working [Jupyter notebook](https://jupyter.org/install) is required with python version 2.7 or greater.  After Python and Jupyter notebook installation, we need; [ipython-sql library](#ipython-sql-library) to run SQL from Jupyter notebook, [SQL Alchemy](https://www.sqlalchemy.org/) dialect to [connect to EXASOL](#connection-to-exasol) and some additional [python libraries](#additional-python-libraries) for data visualization. GeoJSON files containing spatial data for New York City needs to be downloaded in the [geojsonfiles](geojsonfiles) folder. 

#### GeoJSON files

Download the following GeoJSON files in [geojsonfiles](geojsonfiles) folder:

1. New York City Streets data:- https://storage.googleapis.com/exasol_data_science_examples_data/visualizing_spatial_queries/geojsonfiles/nyc_street_data.geojson
2. New York City Borough boundaries data:- https://storage.googleapis.com/exasol_data_science_examples_data/visualizing_spatial_queries/geojsonfiles/nycboroughboundaries.geojson
3. New York City Neighborhood boundaries data:- https://storage.googleapis.com/exasol_data_science_examples_data/visualizing_spatial_queries/geojsonfiles/nycneighborhoods.geojson

#### IPython-sql library

[IPython-sql libraray](https://github.com/catherinedevlin/ipython-sql) enables the use of Jupyter magic functions. With Jupyter magic functions, Jupyter notebooks can be used for data analysis with SQL on a database. Magic functions are pre-defined functions in Jupyter kernel that executes supplied commands. They are prefaced with `%` character. Usage and installation instructions can be found [here](https://github.com/catherinedevlin/ipython-sql).  After installation run the following command:

```mysql
%load_ext sql
```

#### Connection to EXASOL

To connect to EXASOL install the [SQLAlchemy](https://www.sqlalchemy.org/) dialect for EXASOL database. Installation instructions and project details can be found [here](https://pypi.org/project/sqlalchemy-exasol/)

After installation, connect to EXASOL using the following command:

```mysql
%sql exa+pyodbc://USER:PASSWORD@DSN
```

DSN should point to your ODBC installation. For EXASOL6.2 ODBC download and installation details visit [EXASOL ODBC installation](https://www.exasol.com/portal/display/DOWNLOAD/6.2) 

#### Additional Python libraries

Additional python libraries are used to process and visualize geospatial data. We make use of the following python libraries for this demo:

1. [Folium](https://pypi.org/project/folium/)
2. [Pandas](https://pandas.pydata.org/pandas-docs/stable/install.html)
3. [GeoJSON](https://pypi.org/project/geojson/)
4. [JSON](https://docs.python.org/3/library/json.html)
5. [Requests](https://pypi.org/project/requests/)

#### Jupter Notebook extensions

Extensions allow to enhance features of Jupyter Notebook. They are easy to install and configure using the `Nbextensions configuration` page. We have used two extensions in our demo. Remember that the purpose of these extensions is to help visualize the results and are not required to run the [visualizing_spatial_queries.ipynb](visualizing_spatial_queries.ipynb) demo. 

Installation and configuration details for these extensions can be found [here](https://github.com/ipython-contrib/jupyter_contrib_nbextensions)

##### Hide Input

This extension allows hiding of an individual cell. All the code segments that are not necessary for this particular demo are hidden for better visualization and usability. 

##### Limit Output

Limits the output of a cell. This comes in handy as large result outputs can break the notebook. Limiting the output makes it easy to render results. 

### Datasets

For the purpose of this demo we use `NYC_UBER` and `NYC_TAXI` schemas from `demodb.exasol.com`. 

Use the following command to open a schema 

```mysql
%sql open schema SCHEMA_NAME
```

Uber pickups data is stored in `UBER_TAXI_DATA` table in `NYC_UBER` schema. Use `DESCRIBE` to get an overview of this table

```mysql 
%sql describe NYC_UBER.UBER_TAXI_DATA
```

New York City Taxi pickups data is stored in `TRIPS`  table in `NYC_TAXI schema`. Use `DESCRIBE` to get an overview of this table

```mysql 
%sql describe NYC_TAXI.TRIPS
```

### Use Cases 

Let's go briefly through the use cases implemented in [visualizing_spatial_queries.ipynb](visualizing_spatial_queries.ipynb)

#### Uber pickups grouped by New York City Boroughs

In the first use case, we use New York City data in `NYC_UBER` schema to show Uber pickups per borough in New York City. We use Uber pickups data and NYC borough data to query the total number of Uber pickups per borough using inline SQL magic. To visualize New York City borough boundaries we use [New York City Borough boundaries](#GeoJSON-files) dataset. 

#### Uber pickups grouped by New York City Neighborhoods

In the second use case, we use New York City data in `NYC_UBER` schema  to show Uber pickups per neighborhood in New York City. We use Uber pickups data and NYC neighborhood data to query the total number of Uber pickups per neighborhood using inline SQL magic. To visualize New York City neighborhood boundaries we use [New York City Neighborhood boundaries](#GeoJSON-files) dataset. 

#### New York City Streets with highest Uber pickups

In the third use case, we use NYC street data and NYC Uber pickup data to visualize top streets according to number of pickups. This data is stored in our demo database in `NYC_UBER` schema.  To visualize New York City neighborhood boundaries we use [New York City Streets](#GeoJSON-files) dataset. Example in this query can be parameterized to view different results on the map by providing a value for variable `NumberOfStreets` 

#### Comparison of Yellow Taxi and Uber pickups within a certain radius of a location in New York City 

In the fourth use case, we make a comparison between the number of Uber and Yellow Taxi pickups. For this example we have selected **Museum of the New York City** in Manhattan as a pickup point. We have used geocoding to find the latitude and longitude values of a given location. We have Uber data from April-Sept 2014. By changing the value for `month` within this range we can visualize different sets of geospatial data on map. Radius defines the `radius` value of given lat/long point. For speed purposes its recommended to keep radius value small. 

### External Resources

GeoJSON files used for this demo were obtained from the following sources:

- NYC borough boundary polygons:  http://data.beta.nyc/dataset/nyc-borough-boundaries
- NYC neighborhood boundary polygons:  http://data.beta.nyc/dataset/nyc-neighborhood-boundaries
- NYC streets multi-line data: https://data.cityofnewyork.us/City-Government/NYC-Street-Centerline-CSCL-/exjm-f27b

Currently the following external resources are unavailable therefore you need to download required [GeoJSON files](#GeoJSON-files).

