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
