__author__ = 'jnation'

import requests
from django.core.cache import caches
from django.utils.translation import ugettext as _
from os import getenv
import logging

logger = logging.getLogger(__name__)


class ConfigDBException(Exception):
    pass

CONFIGDB_ERROR_MSG = _("ConfigDB connection is currently down, please wait a few minutes and try again." \
                       " If this problem persists then please contact support.")

CONFIGDB_URL = getenv('CONFIGDB_URL', 'http://configdb.lco.gtn/')
if not CONFIGDB_URL.endswith('/'):
    CONFIGDB_URL += "/"

default_cache = caches['default']


class ConfigDB(object):

    def __init__(self):
        self.site_data = self._get_configdb_data()

    def _get_configdb_data(self):
        ''' Gets all the data from configdb (the sites structure with everything in it)
        :return: list of dictionaries of site data
        '''

        json_results = default_cache.get('configdb_data', None)
        if not json_results:
            try:
                r = requests.get(CONFIGDB_URL + 'sites/')
            except requests.exceptions.RequestException as e:
                msg = "{}: {}".format(e.__class__.__name__, self.CONFIGDB_ERROR_MSG)
                raise ConfigDBException(msg)
            r.encoding = 'UTF-8'
            if not r.status_code == 200:
                raise ConfigDBException(self.CONFIGDB_ERROR_MSG)
            json_results = r.json()
            if 'results' not in json_results:
                raise ConfigDBException(self.CONFIGDB_ERROR_MSG)
            json_results = json_results['results']
            # cache the results for 15 minutes
            default_cache.set('configdb_data', json_results, 900)

        return json_results

    def get_site_data(self):
        return self.site_data

    def get_schedulable_instruments(self):
        schedulable_instruments = []
        for site in self.site_data:
            for enclosure in site['enclosure_set']:
                for telescope in enclosure['telescope_set']:
                    for instrument in telescope['instrument_set']:
                        if instrument['state'] == 'SCHEDULABLE':
                            schedulable_instruments.append(instrument)

        return schedulable_instruments

    def get_filters(self, instrument_type):
        '''
        Function creates a set of available filters for instruments of the instrument_type specified using the configdb
        :param instrument_type:
        :return: returns the available set of filters for an instrument_type
        '''
        instruments = self.get_schedulable_instruments()
        available_filters = set()
        for instrument in instruments:
            if instrument_type.upper() == instrument['science_camera']['camera_type']['code'].upper():
                for camera_filter in instrument['science_camera']['filters'].split(','):
                    available_filters.add(camera_filter.lower())

        return available_filters

    def get_binnings(self, instrument_type):
        '''
            Function creates a set of available binning modes for the instrument_type specified
        :param instrument_type:
        :return: returns the available set of binnings for an instrument_type
        '''
        instruments = self.get_schedulable_instruments()
        available_binnings = set()
        for instrument in instruments:
            if instrument_type.upper() == instrument['science_camera']['camera_type']['code'].upper():
                for mode in instrument['science_camera']['camera_type']['mode_set']:
                    available_binnings.add(mode['binning'])
                # Once the instrument type is found, we  have the binnings and are done
                break
        return available_binnings

    def get_default_binning(self, instrument_type):
        '''
            Function returns the default binning for the instrument type specified
        :param instrument_type:
        :return: binning default
        '''
        instruments = self.get_schedulable_instruments()
        for instrument in instruments:
            if instrument_type.upper() == instrument['science_camera']['camera_type']['code'].upper():
                return instrument['science_camera']['camera_type']['default_mode']['binning']
        return None

    def get_active_instrument_types(self, location):
        '''
            Function uses the configdb to get a set of the available instrument_types.
            Location should be a dictionary of the location, with site, observatory, and telescope fields
        :return: Set of available instrument_types (i.e. 1M0-SCICAM-SBIG, etc.)
        '''
        instrument_types = set()
        instruments = self.get_schedulable_instruments()
        for instrument in instruments:
            split_string = instrument['__str__'].lower().split('.')
            if (location.get('site', '').lower() in split_string[0]
                    and location.get('observatory', '').lower() in split_string[1]
                    and location.get('telescope', '').lower() in split_string[2]):
                instrument_types.add(instrument['science_camera']['camera_type']['code'].upper())
        return instrument_types

    def get_exposure_overhead(self, instrument_type, binning):
        # using the instrument type, build an instrument with the correct configdb parameters
        instruments = self.get_schedulable_instruments()
        for instrument in instruments:
            camera_type = instrument['science_camera']['camera_type']
            if camera_type['code'].upper() == instrument_type.upper():
                # get the binnings and put them into a dictionary
                for mode in camera_type['mode_set']:
                    if mode['binning'] == binning:
                        return mode['readout'] + camera_type['fixed_overhead_per_exposure']

        raise ConfigDBException("Instrument type {} not found in configdb.".format(instrument_type))

    def get_request_overheads(self, instrument_type):
        instruments = self.get_schedulable_instruments()
        for instrument in instruments:
            camera_type = instrument['science_camera']['camera_type']
            if camera_type['code'].upper() == instrument_type.upper():
                return {'config_change_time': camera_type['config_change_time'],
                        'acquire_processing_time': camera_type['acquire_processing_time'],
                        'acquire_exposure_time': camera_type['acquire_exposure_time'],
                        'front_padding': camera_type['front_padding'],
                        'filter_change_time': camera_type['filter_change_time']}

        raise ConfigDBException("Instrument type {} not found in configdb.".format(instrument_type))

    @staticmethod
    def is_spectrograph(instrument_type):
        return instrument_type.upper() in ['2M0-FLOYDS-SCICAM', '0M8-NRES-SCICAM']







