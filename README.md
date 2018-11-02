# Valhalla Observation Portal
[![Build Status](https://travis-ci.org/LCOGT/valhalla.svg?branch=master)](https://travis-ci.org/LCOGT/valhalla)
[![Coverage Status](https://coveralls.io/repos/github/LCOGT/valhalla/badge.svg?branch=master)](https://coveralls.io/github/LCOGT/valhalla?branch=master)
[![Code Health](https://landscape.io/github/LCOGT/valhalla/master/landscape.svg?style=flat)](https://landscape.io/github/LCOGT/valhalla/master)
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

The last command will run a hot reload server which will automatically keep the javascript
bundles up to date as you develop.

## Environment variables
The default settings should be sufficient for development. Below are the list of environment variables
that should be set for deployment or customization.

### General
`SECRET_KEY` The secret key used for sessions. Default: random characters

`DEBUG` Whether the application should run in djangos debug mode or not. Default: `False`

### Database
`DB_ENGINE` The database engine to use. Default: `django.db.backends.sqlite3`

`DB_NAME` The name of the database. Default: `db.sqlite3`

`DB_USER` The database user. Default: blank

`DB_PASSWORD` The database password. Default: blank

`DB_HOST` The database host to connect to. Default: blank

`DB_PORT` The database port. Default: blank

### Cache
`CACHE_BACKEND` The remote django cache backend to use. Default: `django.core.cache.backends.locmem.LocMemCache`

`CACHE_LOCATION` The cache location (or connection string). Default: `unique-snowflake`

`LOCAL_CACHE_BACKEND` The local django cache backend to use. Default: `django.core.cache.backends.locmem.LocMemCache`

### Email
`EMAIL_BACKEND` The django SMTP backend to use. Default: `django.core.mail.backends.console.EmailBackend`

`EMAIL_HOST` The SMTP host. Default: `localhost`

`EMAIL_HOST_USER` SMTP user. Default: blank

`EMAIL_HOST_PASSWORD` SMTP password. Default: blank

`EMAIL_PORT` SMTP port to use. Default: `587`

### External Services
`ELASTICSEARCH_URL` The url to the elasticsearch cluster. Default: `http://localhost`

`POND_URL` The url to the pond (http). Default: `http://localhost`

`CONFIGDB_URL` The url to configdb3. Default: `http://localhost`

`DOWNTIMEDB_URL` The url to downtimedb. Default: `http://localhost`

### Static and Media Files
`STATIC_STORAGE` The django staticfiles storage backend. Default: `django.contrib.staticfiles.storage.StaticFilesStorage`

`MEDIA_STORAGE` The django media files storage backend. Default: `django.core.files.storage.FileSystemStorage`

`AWS_ACCESS_KEY_ID` The AWS user access key with read/write/permissions priveleges on the s3 bucket. Default: None

`AWS_SECRET_ACCESS_KEY` The AWS user secret key to use with the access key. Default: None

`AWS_BUCKET_NAME` The name of the AWS bucket to store static and media files. Default: `observe.lco.global`

### Celery
`CELERY_ENABLED` Whether or not to execute celery tasks asynchronously. Default: `False`

`CELERY_BROKER_URL` The broker url for celery. Default: `memory://localhost`

To run valhalla with local staticfiles, simply omit settings the `AWS_*` env variables and set `DEBUG` to `True`.  