from math import cos, radians
from rise_set.astrometry import make_ra_dec_target, make_satellite_target, make_minor_planet_target, make_comet_target
from rise_set.angle import Angle
from rise_set.rates import ProperMotion
from rise_set.utils import coalesce_adjacent_intervals
from rise_set.visibility import Visibility

from valhalla.common.configdb import ConfigDB

HOURS_PER_DEGREES = 15.0


def get_rise_set_intervals(request_model):
    target = request_model.target.rise_set_target()
    airmass = request_model.constraints.max_airmass
    moon_distance = Angle(degrees=request_model.constraints.min_lunar_distance)

    instrument_type = request_model.molecule_set.first().instrument_name
    configdb = ConfigDB()
    site_details = configdb.get_sites_with_instrument_type_and_location(instrument_type,
                                                                        request_model.location.site,
                                                                        request_model.location.observatory,
                                                                        request_model.location.telescope)
    intervals = []
    for site_code, site_detail in site_details.items():
        intervals.extend(_get_rise_set_interval_for_target_and_site(target, site_detail,
                                                                    request_model.window_set.all(),
                                                                    airmass, moon_distance))

    intervals = coalesce_adjacent_intervals(intervals)

    return intervals


def _get_rise_set_interval_for_target_and_site(rise_set_target, site_detail, windows, airmass, moon_distance):
    rise_set_site = {'latitude': Angle(degrees=site_detail['latitude']),
                     'longitude': Angle(degrees=site_detail['longitude']),
                     'horizon': Angle(degrees=site_detail['horizon']),
                     'ha_limit_neg': Angle(degrees=site_detail['ha_limit_neg'] * HOURS_PER_DEGREES),
                     'ha_limit_pos': Angle(degrees=site_detail['ha_limit_pos'] * HOURS_PER_DEGREES)}
    intervals = []
    for window in windows:
        v = Visibility(site=rise_set_site,
                       start_date=window.start,
                       end_date=window.end,
                       horizon=site_detail['horizon'],
                       ha_limit_neg=site_detail['ha_limit_neg'],
                       ha_limit_pos=site_detail['ha_limit_pos'],
                       twilight='nautical'
                       )
        intervals.extend(v.get_observable_intervals(rise_set_target, airmass=airmass,
                                                    moon_distance=moon_distance))

    return intervals


def get_rise_set_target(target_model):
    if target_model.type == 'SIDEREAL':
        pmra = (target_model.proper_motion_ra / 1000.0 / cos(radians(target_model.dec))) / 3600.0
        pmdec = (target_model.proper_motion_dec / 1000.0) / 3600.0
        return make_ra_dec_target(ra=Angle(degrees=target_model.ra),
                                  dec=Angle(degrees=target_model.dec),
                                  ra_proper_motion=ProperMotion(Angle(degrees=pmra, units='arc'), time='year'),
                                  dec_proper_motion=ProperMotion(Angle(degrees=pmdec, units='arc'), time='year'),
                                  parallax=target_model.parallax, rad_vel=0.0, epoch=target_model.epoch)

    elif target_model.type == 'SATELLITE':
        return make_satellite_target(alt=target_model.altitude, az=target_model.azimuth,
                                     diff_alt_rate=target_model.diff_pitch_rate,
                                     diff_az_rate=target_model.diff_roll_rate,
                                     diff_alt_accel=target_model.diff_pitch_acceleration,
                                     diff_az_accel=target_model.diff_roll_acceleration,
                                     diff_epoch_rate=target_model.diff_epoch_rate)

    elif target_model.type == 'NON_SIDEREAL':
        if target_model.scheme == 'MPC_MINOR_PLANET':
            return make_minor_planet_target(target_type=target_model.scheme,
                                            epoch=target_model.epochofel,
                                            inclination=target_model.orbinc,
                                            long_node=target_model.longascnode,
                                            arg_perihelion=target_model.argofperih,
                                            semi_axis=target_model.meandist,
                                            eccentricity=target_model.eccentricity,
                                            mean_anomaly=target_model.meananom
                                            )
        else:
            return make_comet_target(target_type=target_model.scheme,
                                     epoch=target_model.epochofel,
                                     epochofperih=target_model.epochofperih,
                                     inclination=target_model.orbinc,
                                     long_node=target_model.longascnode,
                                     arg_perihelion=target_model.argofperih,
                                     perihdist=target_model.perihdist,
                                     eccentricity=target_model.eccentricity,
                                     )

