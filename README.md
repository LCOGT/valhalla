# Valhalla Observation Portal
[![Build Status](https://travis-ci.org/LCOGT/valhalla.svg?branch=master)](https://travis-ci.org/LCOGT/valhalla)
[![Coverage Status](https://coveralls.io/repos/github/LCOGT/valhalla/badge.svg?branch=master)](https://coveralls.io/github/LCOGT/valhalla?branch=master)
[![Code Health](https://landscape.io/github/LCOGT/valhalla/master/landscape.svg?style=flat)](https://landscape.io/github/LCOGT/valhalla/master)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/6da4827702214bcf9c798ebe788110d9/badge.svg)](https://www.quantifiedcode.com/app/project/6da4827702214bcf9c798ebe788110d9)
[![Dependency Status](https://www.versioneye.com/user/projects/589df7f4940b230036768664/badge.svg)](https://www.versioneye.com/user/projects/589df7f4940b230036768664)

## Getting Started

### Setting up the django backend

1. Clone this repo
2. `./manage.py migrate`
3. `./manage.py runserver`

That's it! Check out [local_settings.sample](local_settings.sample) if you'd
like to customize your development settings.

### Setting up the frontend
We use webpack + vue.js to manage some of the more complex frontend code.
Make sure you have npm installed, and in the root directory:

1. `npm install`
2. `npm run watch`

The last commannd will run a hot reload server which will automatically keep the javascript
bundles up to date as you develop.

## Environmental variables
The default settings should be sufficient for development. Below are the list of environmental variables
taht should be set for deploymet or customization.

### General
`SECRET_KEY` The secret key used for sessions. Default: radom characters

### Database
`DB_ENGINE` The database engine to use. Default: `django.db.backends.sqlite3`

`DB_NAME` The name of the databse. Default: `db.sqlite3`

`DB_USER` The database user. Default: blank

`DB_PASSWORD` The database password. Default: blank

`DB_HOST` The database host to connec to. Default: blank

`DB_PORT` The database port. Defaut: blank

### Cache
`CACHE_BACKEND` The django cache backend to use. Default: `django.core.cache.backends.locmem.LocMemCache`

`CACHE_LOCATION` The cache location (or connection string). Default: `unique-snowflake`

### Email
`EMAIL_HOST` The SMTP host. Default: `localhost`

`EMAIL_HOST_USER` SMTP user. Default: blank

`EMAIL_HOST_PASSWORD` SMTP password. Default: blank

`EMAIL_PORT` SMTP port to use. Default: `587`

### External Services
`ELASTICSEARCH_URL` The url to the elasticsearch cluster. Default: `http://localhost`

`POND_URL` The url to the pond (http). Default: `http://localhost`

`CONFIGDB_URL` The url to configdb3. Default: `http://localhost`

### Celery
`CELERY_ENABLED` Whether or not to execute celery tasks asynchronusly. Default: `False`

`CELERY_BROKER_URL` The broker url for celery. Default: `memory://localhost`
