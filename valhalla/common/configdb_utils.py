__author__ = 'jnation'

import requests
from django.core.cache import caches
from os import getenv
import logging

logger = logging.getLogger(__name__)


class ConfigDBException(Exception):
    pass


CONFIGDB_ERROR_MSG = "ConfigDB connection is currently down, please wait a few minutes and try again." \
                    " If this problem persists then please contact support."

CONFIGDB_URL = getenv('CONFIGDB_URL', 'http://configdb.lco.gtn/')
if not CONFIGDB_URL.endswith('/'):
    CONFIGDB_URL += "/"

default_cache = caches['default']

def get_configdb_data():
    ''' Gets all the data from configdb (the sites structure with everything in it)
    :return: list of dictionaries of site data
    '''

    json_results = default_cache.get('configdb_data', None)
    if not json_results:
        try:
            r = requests.get(CONFIGDB_URL + 'sites/')
        except requests.exceptions.RequestException as e:
            msg = "{}: {}".format(e.__class__.__name__, CONFIGDB_ERROR_MSG)
            raise ConfigDBException(msg)
        r.encoding = 'UTF-8'
        if not r.status_code == 200:
            raise ConfigDBException(CONFIGDB_ERROR_MSG)
        json_results = r.json()
        if 'results' not in json_results:
            raise ConfigDBException(CONFIGDB_ERROR_MSG)
        json_results = json_results['results']
        # cache the results for 15 minutes
        default_cache.set('configdb_data', json_results, 900)

    return json_results
