import requests
from django.core.cache import cache
from django.utils.translation import ugettext as _
from django.conf import settings
from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

CONFIGDB_ERROR_MSG = _(("ConfigDB connection is currently down, please wait a few minutes and try again."
                       " If this problem persists then please contact support."))


class ConfigDBException(Exception):
    pass


class TelescopeKey(namedtuple('TelescopeKey', ['site', 'observatory', 'telescope'])):
    __slots__ = ()

    def __str__(self):
        return ".".join(s for s in [self.site, self.observatory, self.telescope] if s)


class ConfigDB(object):

    def __init__(self):
        self.site_data = self._get_configdb_data()

    def _get_configdb_data(self):
        ''' Gets all the data from configdb (the sites structure with everything in it)
        :return: list of dictionaries of site data
        '''

        site_data = cache.get('site_data')
        if not site_data:
            try:
                r = requests.get(settings.CONFIGDB_URL + '/sites/')
                r.raise_for_status()
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                msg = "{}: {}".format(e.__class__.__name__, CONFIGDB_ERROR_MSG)
                raise ConfigDBException(msg)
            try:
                site_data = r.json()['results']
            except KeyError:
                raise ConfigDBException(CONFIGDB_ERROR_MSG)
            # cache the results for 15 minutes
            cache.set('site_data', site_data, 900)

        return site_data

    def get_sites_with_instrument_type_and_location(self, instrument_type='', site_code='',
                                                    observatory_code='', telescope_code=''):
        site_data = self.site_data
        site_details = {}
        for site in site_data:
            if not site_code or site_code == site['code']:
                for enclosure in site['enclosure_set']:
                    if not observatory_code or observatory_code == enclosure['code']:
                        for telescope in enclosure['telescope_set']:
                            if not telescope_code or telescope_code == telescope['code']:
                                for instrument in telescope['instrument_set']:
                                    if instrument['state'] == 'SCHEDULABLE':
                                        camera_type = instrument['science_camera']['camera_type']['code']
                                        if not instrument_type or instrument_type.upper() == camera_type.upper():
                                            if site['code'] not in site_details:
                                                site_details[site['code']] = {
                                                    'latitude': telescope['lat'],
                                                    'longitude': telescope['long'],
                                                    'horizon': telescope['horizon'],
                                                    'altitude': site['elevation'],
                                                    'ha_limit_pos': telescope['ha_limit_pos'],
                                                    'ha_limit_neg': telescope['ha_limit_neg']
                                                }

        return site_details

    def get_instruments(self, only_schedulable=False):
        instruments = []
        for site in self.site_data:
            for enclosure in site['enclosure_set']:
                for telescope in enclosure['telescope_set']:
                    for instrument in telescope['instrument_set']:
                        if only_schedulable and instrument['state'] != 'SCHEDULABLE':
                            pass
                        else:
                            telescope_key = TelescopeKey(
                                site=site['code'],
                                observatory=enclosure['code'],
                                telescope=telescope['code']
                            )
                            instrument['telescope_key'] = telescope_key
                            instruments.append(instrument)

        return instruments

    def get_instrument_types_per_telescope(self, only_schedulable=False):
        '''
            Function uses the configdb to get a set of available instrument types per telescope
        :return: set of available instrument types per TelescopeKey
        '''
        telescope_instrument_types = {}
        for instrument in self.get_instruments(only_schedulable=only_schedulable):
            if instrument['telescope_key'] not in telescope_instrument_types:
                telescope_instrument_types[instrument['telescope_key']] = []
            instrument_type = instrument['science_camera']['camera_type']['code'].upper()
            if instrument_type not in telescope_instrument_types[instrument['telescope_key']]:
                telescope_instrument_types[instrument['telescope_key']].append(instrument_type)

        return telescope_instrument_types

    def get_filters(self, instrument_type):
        '''
        Function creates a set of available filters for instruments of the instrument_type specified using the configdb
        :param instrument_type:
        :return: returns the available set of filters for an instrument_type
        '''
        instruments = self.get_instruments()
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
        instruments = self.get_instruments()
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
        instruments = self.get_instruments()
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
        instruments = self.get_instruments()
        for instrument in instruments:
            split_string = instrument['__str__'].lower().split('.')
            if (location.get('site', '').lower() in split_string[0]
                    and location.get('observatory', '').lower() in split_string[1]
                    and location.get('telescope', '').lower() in split_string[2]):
                instrument_types.add(instrument['science_camera']['camera_type']['code'].upper())
        return instrument_types

    def get_exposure_overhead(self, instrument_type, binning):
        # using the instrument type, build an instrument with the correct configdb parameters
        instruments = self.get_instruments()
        for instrument in instruments:
            camera_type = instrument['science_camera']['camera_type']
            if camera_type['code'].upper() == instrument_type.upper():
                # get the binnings and put them into a dictionary
                for mode in camera_type['mode_set']:
                    if mode['binning'] == binning:
                        return mode['readout'] + camera_type['fixed_overhead_per_exposure']

        raise ConfigDBException("Instrument type {} not found in configdb.".format(instrument_type))

    def get_request_overheads(self, instrument_type):
        instruments = self.get_instruments()
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
