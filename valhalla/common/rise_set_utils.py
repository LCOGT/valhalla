from math import cos, radians
from rise_set.astrometry import make_ra_dec_target, make_satellite_target, make_minor_planet_target, make_comet_target, calculate_airmass_at_times
from rise_set.angle import Angle
from rise_set.rates import ProperMotion
from rise_set.utils import coalesce_adjacent_intervals
from rise_set.visibility import Visibility

from valhalla.common.configdb import ConfigDB

HOURS_PER_DEGREES = 15.0


def visibility_details(site):
    for enclosure in site['enclosure_set']:
        for telescope in enclosure['telescope_set']:
            return {
                'latitude': telescope['lat'],
                'longitude': telescope['long'],
                'horizon': telescope['horizon'],
                'altitude':  site['elevation'],
                'ha_limit_pos': telescope['ha_limit_pos'],
                'ha_limit_neg': telescope['ha_limit_neg']
            }


def rise_set_site(site):
    details = visibility_details(site)
    details['latitude'] = Angle(degrees=details['latitude'])
    details['longitude'] = Angle(degrees=details['longitude'])
    details['horizon'] = Angle(degrees=details['horizon'])
    details['ha_limit_pos'] = Angle(degrees=details['ha_limit_pos'] * HOURS_PER_DEGREES)
    details['ha_limit_neg'] = Angle(degrees=details['ha_limit_neg'] * HOURS_PER_DEGREES)
    return details


def get_rise_set_intervals(instrument_type, target_dict, constraints_dict, location_dict, window_list):
    airmass = constraints_dict['max_airmass']
    moon_distance = constraints_dict['min_lunar_distance']

    configdb = ConfigDB()
    sites = configdb.get_sites_with_instrument_type_and_location(
        instrument_type,
        location_dict.get('site', ''),
        location_dict.get('observatory', ''),
        location_dict.get('telescope', '')
    )
    intervals = []
    for site in sites:
        intervals.extend(
            get_rise_set_interval_for_target_and_site(target_dict, site, window_list, airmass, moon_distance)
        )

    intervals = coalesce_adjacent_intervals(intervals)

    return intervals


def get_rise_set_interval_for_target_and_site(target_dict, site, windows, airmass, moon_distance):
    site_detail = visibility_details(site)
    rs_target = get_rise_set_target(target_dict)
    rs_site = rise_set_site(site)
    intervals = []
    for window in windows:
        v = Visibility(site=rs_site,
                       start_date=window['start'],
                       end_date=window['end'],
                       horizon=site_detail['horizon'],
                       ha_limit_neg=site_detail['ha_limit_neg'],
                       ha_limit_pos=site_detail['ha_limit_pos'],
                       twilight='nautical'
                       )
        intervals.extend(v.get_observable_intervals(
            rs_target, airmass=airmass, moon_distance=Angle(degrees=moon_distance))
        )

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
    configdb = ConfigDB()
    site = configdb.get_site(site_code)
    site_detail = visibility_details(site)
    rs_site = rise_set_site(site)
    v = Visibility(
        site=rs_site,
        start_date=start,
        end_date=end,
        horizon=site_detail['horizon'],
        ha_limit_neg=site_detail['ha_limit_neg'],
        ha_limit_pos=site_detail['ha_limit_pos'],
        twilight='nautical'
    )
    return v.get_dark_intervals()


def calculate_airmass(night_times, target, site):
    rs_target = get_rise_set_target(target)
    rs_site = rise_set_site(site)
    return calculate_airmass_at_times(
        night_times, rs_target, rs_site['latitude'], rs_site['longitude'], rs_site['altitude']
    )
