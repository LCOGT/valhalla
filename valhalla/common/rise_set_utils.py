from math import cos, radians
from datetime import timedelta
from rise_set.astrometry import make_ra_dec_target, make_satellite_target, make_minor_planet_target, make_comet_target
from rise_set.angle import Angle
from rise_set.rates import ProperMotion
from rise_set.utils import coalesce_adjacent_intervals
from rise_set.visibility import Visibility

from valhalla.common.configdb import configdb

HOURS_PER_DEGREES = 15.0


def get_largest_interval(intervals):
    largest_interval = timedelta(seconds=0)
    for interval in intervals:
        largest_interval = max((interval[1] - interval[0]), largest_interval)

    return largest_interval


def get_rise_set_intervals(request_dict, site=''):
    site = site if site else request_dict['location'].get('site', '')
    site_details = configdb.get_sites_with_instrument_type_and_location(
            request_dict['molecules'][0]['instrument_name'],
            site,
            request_dict['location'].get('observatory', ''),
            request_dict['location'].get('telescope', '')
    )
    intervals = []
    if not site_details:
        return intervals
    for site_detail in site_details.values():
        rise_set_site = {
            'latitude': Angle(degrees=site_detail['latitude']),
            'longitude': Angle(degrees=site_detail['longitude']),
            'horizon': Angle(degrees=site_detail['horizon']),
            'ha_limit_neg': Angle(degrees=site_detail['ha_limit_neg'] * HOURS_PER_DEGREES),
            'ha_limit_pos': Angle(degrees=site_detail['ha_limit_pos'] * HOURS_PER_DEGREES)
        }
        for window in request_dict['windows']:
            v = Visibility(
                site=rise_set_site,
                start_date=window['start'],
                end_date=window['end'],
                horizon=site_detail['horizon'],
                ha_limit_neg=site_detail['ha_limit_neg'],
                ha_limit_pos=site_detail['ha_limit_pos'],
                twilight='nautical'
            )
            intervals.extend(
                v.get_observable_intervals(
                    get_rise_set_target(
                        request_dict['target']
                    ),
                    airmass=request_dict['constraints']['max_airmass'],
                    moon_distance=Angle(degrees=request_dict['constraints']['min_lunar_distance'])
                )
            )
    intervals = coalesce_adjacent_intervals(intervals)

    return intervals


def get_rise_set_target(target_dict):
    if target_dict['type'] == 'SIDEREAL':
        pmra = (target_dict['proper_motion_ra'] / 1000.0 / cos(radians(target_dict['dec']))) / 3600.0
        pmdec = (target_dict['proper_motion_dec'] / 1000.0) / 3600.0
        return make_ra_dec_target(ra=Angle(degrees=target_dict['ra']),
                                  dec=Angle(degrees=target_dict['dec']),
                                  ra_proper_motion=ProperMotion(Angle(degrees=pmra, units='arc'), time='year'),
                                  dec_proper_motion=ProperMotion(Angle(degrees=pmdec, units='arc'), time='year'),
                                  parallax=target_dict['parallax'], rad_vel=0.0, epoch=target_dict['epoch'])

    elif target_dict['type'] == 'SATELLITE':
        return make_satellite_target(alt=target_dict['altitude'], az=target_dict['azimuth'],
                                     diff_alt_rate=target_dict['diff_pitch_rate'],
                                     diff_az_rate=target_dict['diff_roll_rate'],
                                     diff_alt_accel=target_dict['diff_pitch_acceleration'],
                                     diff_az_accel=target_dict['diff_roll_acceleration'],
                                     diff_epoch_rate=target_dict['diff_epoch_rate'])

    elif target_dict['type'] == 'NON_SIDEREAL':
        if target_dict['scheme'] == 'MPC_MINOR_PLANET':
            return make_minor_planet_target(target_type=target_dict['scheme'],
                                            epoch=target_dict['epochofel'],
                                            inclination=target_dict['orbinc'],
                                            long_node=target_dict['longascnode'],
                                            arg_perihelion=target_dict['argofperih'],
                                            semi_axis=target_dict['meandist'],
                                            eccentricity=target_dict['eccentricity'],
                                            mean_anomaly=target_dict['meananom']
                                            )
        else:
            return make_comet_target(target_type=target_dict['scheme'],
                                     epoch=target_dict['epochofel'],
                                     epochofperih=target_dict['epochofperih'],
                                     inclination=target_dict['orbinc'],
                                     long_node=target_dict['longascnode'],
                                     arg_perihelion=target_dict['argofperih'],
                                     perihdist=target_dict['perihdist'],
                                     eccentricity=target_dict['eccentricity'],
                                     )


def get_site_rise_set_intervals(start, end, site_code):
    site_details = configdb.get_sites_with_instrument_type_and_location(site_code=site_code)
    if site_code in site_details:
        site_detail = site_details[site_code]
        rise_set_site = {'latitude': Angle(degrees=site_detail['latitude']),
                         'longitude': Angle(degrees=site_detail['longitude']),
                         'horizon': Angle(degrees=site_detail['horizon']),
                         'ha_limit_neg': Angle(degrees=site_detail['ha_limit_neg'] * HOURS_PER_DEGREES),
                         'ha_limit_pos': Angle(degrees=site_detail['ha_limit_pos'] * HOURS_PER_DEGREES)}

        v = Visibility(site=rise_set_site,
                       start_date=start,
                       end_date=end,
                       horizon=site_detail['horizon'],
                       ha_limit_neg=site_detail['ha_limit_neg'],
                       ha_limit_pos=site_detail['ha_limit_pos'],
                       twilight='nautical'
                       )

        return v.get_dark_intervals()

    return []
