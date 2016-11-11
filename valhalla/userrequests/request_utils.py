from django.forms.models import model_to_dict
from datetime import timedelta
from rise_set.angle import Angle
from rise_set.astrometry import calculate_airmass_at_times

from valhalla.common.configdb import ConfigDB
from valhalla.common.telescope_states import get_telescope_states, filter_telescope_states_by_intervals
from valhalla.common.rise_set_utils import get_rise_set_target, get_rise_set_interval_for_target_and_site


def get_telescope_states_for_request(request):
    instrument_type = request.molecule_set.first().instrument_name
    rs_target = get_rise_set_target(model_to_dict(request.target))
    constraints = request.constraints
    configdb = ConfigDB()
    site_intervals = {}
    # Build up the list of telescopes and their rise set intervals for the target on this request
    site_data = configdb.get_sites_with_instrument_type_and_location(instrument_type=instrument_type,
                                                                     site_code=request.location.site,
                                                                     observatory_code=request.location.observatory,
                                                                     telescope_code=request.location.telescope)
    for site, details in site_data.items():
        if site not in site_intervals:
            site_intervals[site] = get_rise_set_interval_for_target_and_site(rise_set_target=rs_target,
                                                                             site_detail=details,
                                                                             windows=[model_to_dict(w) for w in
                                                                                      request.window_set.all()],
                                                                             airmass=constraints.max_airmass,
                                                                             moon_distance=constraints.min_lunar_distance)
    # If you have no sites, return the empty dict here
    if not site_intervals:
        return {}

    # Retrieve the telescope states for that set of sites
    telescope_states = get_telescope_states(start=request.min_window_time,
                                            end=request.max_window_time,
                                            sites=list(site_intervals.keys()),
                                            instrument_types=[instrument_type])
    # Remove the empty intervals from the dictionary
    site_intervals = {site: intervals for site, intervals in site_intervals.items() if intervals}

    # Filter the telescope states list with the site intervals
    filtered_telescope_states = filter_telescope_states_by_intervals(telescope_states,
                                                                     site_intervals,
                                                                     request.min_window_time,
                                                                     request.max_window_time)

    return filtered_telescope_states


def date_range_from_interval(start_time, end_time, dt = timedelta(minutes=15)):
    time = start_time
    while time < end_time:
        yield time
        time += dt


def get_airmasses_for_request_at_sites(request):
    instrument_type = request.molecule_set.first().instrument_name
    constraints = request.constraints

    configdb = ConfigDB()
    site_data = configdb.get_sites_with_instrument_type_and_location(instrument_type=instrument_type,
                                                                     site_code=request.location.site,
                                                                     observatory_code=request.location.observatory,
                                                                     telescope_code=request.location.telescope)

    rs_target = get_rise_set_target(model_to_dict(request.target))

    data = {'airmass_data': {}}
    if request.target.type.upper() != 'SATELLITE':
        for site_id, site_details in site_data.items():
            night_times = []
            site_lat = Angle(degrees=site_details['latitude'])
            site_lon = Angle(degrees=site_details['longitude'])
            site_alt = site_details['altitude']
            intervals = get_rise_set_interval_for_target_and_site(rise_set_target=rs_target,
                                                                  site_detail=site_details,
                                                                  windows=[model_to_dict(w) for w in
                                                                           request.window_set.all()],
                                                                  airmass=constraints.max_airmass,
                                                                  moon_distance=constraints.min_lunar_distance)
            for interval in intervals:
                night_times.extend(
                    [time for time in date_range_from_interval(interval[0], interval[1], dt=timedelta(minutes=10))])

            if len(night_times) > 0:
                if site_id not in data:
                    data['airmass_data'][site_id] = {}
                data['airmass_data'][site_id]['times'] = [time.strftime('%Y-%m-%dT%H:%M') for time in night_times]
                data['airmass_data'][site_id]['airmasses'] = calculate_airmass_at_times(night_times,
                                                                                        rs_target,
                                                                                        site_lat,
                                                                                        site_lon,
                                                                                        site_alt)
                data['airmass_limit'] = constraints.max_airmass

    return data