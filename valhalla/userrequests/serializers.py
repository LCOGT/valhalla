from rest_framework import serializers
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.core.validators import MinValueValidator
from json import JSONDecodeError
import json

from valhalla.proposals.models import TimeAllocation
from valhalla.userrequests.models import Request, Target, Window, UserRequest, Location, Molecule, Constraints
from valhalla.userrequests.models import DraftUserRequest
from valhalla.userrequests.state_changes import debit_ipp_time, TimeAllocationError, validate_ipp
from valhalla.userrequests.target_helpers import SiderealTargetHelper, NonSiderealTargetHelper, SatelliteTargetHelper
from valhalla.common.configdb import ConfigDB
from valhalla.userrequests.duration_utils import (get_request_duration, get_total_duration_dict,
                                                  get_time_allocation_key)
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval


class CadenceSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    period = serializers.FloatField(validators=[MinValueValidator(0.02)])
    jitter = serializers.FloatField(validators=[MinValueValidator(0.02)])

    def validate_end(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('End time must be in the future')
        return value

    def validate(self, data):
        if data['start'] >= data['end']:
            msg = _("Cadence end '{}' cannot be earlier than cadence start '{}'.").format(data['start'], data['end'])
            raise serializers.ValidationError(msg)
        return data


class ConstraintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraints
        exclude = ('request', 'id')


class MoleculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Molecule
        exclude = ('request', 'id', 'sub_x1', 'sub_x2', 'sub_y1', 'sub_y2')

    def validate_instrument_name(self, value):
        configdb = ConfigDB()
        if value and value not in configdb.get_active_instrument_types({}):
            raise serializers.ValidationError(
                _("Invalid instrument name {}. Valid instruments may include: {}").format(
                    value, ', '.join(configdb.get_active_instrument_types({}))
                )
            )
        return value

    def validate(self, data):
        # set special defaults if it is a spectrograph
        configdb = ConfigDB()
        if configdb.is_spectrograph(data['instrument_name']):
            if 'ag_mode' not in data:
                data['ag_mode'] = 'ON'
            if 'spectra_slit' not in data:
                data['spectra_slit'] = 'floyds_slit_default'

        types_that_require_filter = ['expose', 'auto_focus', 'zero_pointing', 'standard', 'sky_flat']

        # check that the filter is available in the instrument type specified
        available_filters = configdb.get_filters(data['instrument_name'])
        if configdb.is_spectrograph(data['instrument_name']):
            if data['spectra_slit'] not in available_filters:
                raise serializers.ValidationError(
                    _("Invalid spectra slit {} for instrument {}. Valid slits are: {}").format(
                        data['spectra_slit'], data['instrument_name'], ", ".join(available_filters)
                    )
                )
        elif data['type'].lower() in types_that_require_filter:
            if 'filter' not in data:
                raise serializers.ValidationError(
                    _("Molecule type {} with instrument {} must specify a filter.").format(
                        data['type'], data['instrument_name']
                    )
                )
            elif data['filter'] not in available_filters:
                raise serializers.ValidationError(
                    _("Invalid filter {} for instrument {}. Valid filters are: {}").format(
                        data['filter'], data['instrument_name'], ", ".join(available_filters)
                    )
                )

        # check that the binning is available for the instrument type specified
        if 'bin_x' not in data and 'bin_y' not in data:
            data['bin_x'] = configdb.get_default_binning(data['instrument_name'])
            data['bin_y'] = data['bin_x']
        elif 'bin_x' in data and 'bin_y' in data:
            available_binnings = configdb.get_binnings(data['instrument_name'])
            if data['bin_x'] not in available_binnings:
                msg = _("Invalid binning of {} for instrument {}. Valid binnings are: {}").format(
                    data['bin_x'], data['instrument_name'].upper(), ", ".join([str(b) for b in available_binnings])
                )
                raise serializers.ValidationError(msg)
        else:
            raise serializers.ValidationError(_("Missing one of bin_x or bin_y. Specify both or neither."))

        return data


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        exclude = ('request', 'id')

    def validate(self, data):
        if 'observatory' in data and 'site' not in data:
            raise serializers.ValidationError(_("Must specify a site with an observatory."))
        if 'telescope' in data and 'observatory' not in data:
            raise serializers.ValidationError(_("Must specify an observatory with a telescope."))

        configdb = ConfigDB()
        site_data_dict = {site['code']: site for site in configdb.site_data}
        if 'site' in data:
            if data['site'] not in site_data_dict:
                msg = _('Site {} not valid. Valid choices: {}').format(data['site'], ', '.join(site_data_dict.keys()))
                raise serializers.ValidationError(msg)
            obs_set = site_data_dict[data['site']]['enclosure_set']
            obs_dict = {obs['code']: obs for obs in obs_set}
            if 'observatory' in data:
                if data['observatory'] not in obs_dict:
                    msg = _('Observatory {} not valid. Valid choices: {}').format(
                        data['observatory'],
                        ', '.join(obs_dict.keys())
                    )
                    raise serializers.ValidationError(msg)

                tel_set = obs_dict[data['observatory']]['telescope_set']
                tel_list = [tel['code'] for tel in tel_set]
                if 'telescope' in data and data['telescope'] not in tel_list:
                    msg = _('Telescope {} not valid. Valid choices: {}').format(data['telescope'], ', '.join(tel_list))
                    raise serializers.ValidationError(msg)

        return data


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        exclude = ('request', 'id')

    def validate(self, data):
        if data['end'] <= data['start']:
            msg = _("Window end '{}' cannot be earlier than window start '{}'.").format(data['start'], data['end'])
            raise serializers.ValidationError(msg)
        return data

    def validate_end(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('Window end time must be in the future')
        return value


class TargetSerializer(serializers.ModelSerializer):
    TYPE_HELPER_MAP = {
        'SIDEREAL': SiderealTargetHelper,
        'NON_SIDEREAL': NonSiderealTargetHelper,
        'SATELLITE': SatelliteTargetHelper,
        'STATIC': SiderealTargetHelper,
    }

    class Meta:
        model = Target
        exclude = ('request', 'id')

    def to_representation(self, instance):
        # Only return data for the speific target type
        data = super().to_representation(instance)
        target_helper = self.TYPE_HELPER_MAP[data['type']](data)
        return {k: data.get(k) for k in target_helper.fields}

    def validate(self, data):
        target_helper = self.TYPE_HELPER_MAP[data['type']](data)
        if target_helper.is_valid():
            data.update(target_helper.data)
        else:
            raise serializers.ValidationError(target_helper.error_dict)
        return data


class RequestSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    constraints = ConstraintsSerializer()
    target = TargetSerializer()
    molecules = MoleculeSerializer(many=True)
    windows = WindowSerializer(many=True)
    cadence = CadenceSerializer(required=False)

    class Meta:
        model = Request
        read_only_fields = (
            'id', 'fail_count', 'scheduled_count', 'created', 'completed'
        )
        exclude = ('user_request',)

    def validate_molecules(self, value):
        if not value:
            raise serializers.ValidationError(_('You must specify at least 1 molecule'))

        # Make sure each molecule has the same instrument name
        if len(set(molecule['instrument_name'] for molecule in value)) > 1:
            raise serializers.ValidationError(_('Each Molecule must specify the same instrument name'))
        return value

    def validate_windows(self, value):
        if not value:
            raise serializers.ValidationError(_('You must specify at least 1 window'))

        return value

    def validate_cadence(self, value):
        if value:
            raise serializers.ValidationError(_('Please use the cadence endpoint to expand your cadence request'))
        return value

    def validate(self, data):
        # Target special validation
        if data['molecules'][0]['instrument_name'].upper() == '2M0-FLOYDS-SCICAM':
            if 'acquire_mode' not in data['target']:
                # the normal default is 'OPTIONAL', but for floyds the default is 'ON'
                data['target']['acquire_mode'] = 'ON'

        configdb = ConfigDB()

        # check if the instrument specified is allowed
        valid_instruments = configdb.get_active_instrument_types(data['location'])
        for molecule in data['molecules']:
            if molecule['instrument_name'] not in valid_instruments:
                msg = _("Invalid instrument name '{}' at site={}, obs={}, tel={}. \n").format(
                    molecule['instrument_name'], data['location'].get('site', 'Any'),
                    data['location'].get('observatory', 'Any'), data['location'].get('telescope', 'Any'))
                msg += _("Valid instruments include: ")
                for inst_name in valid_instruments:
                    msg += inst_name + ', '
                raise serializers.ValidationError(msg)

        # check that the requests window has enough rise_set visible time to accomodate the requests duration
        if data['windows']:
            duration = get_request_duration(data)
            rise_set_intervals = get_rise_set_intervals(data)
            largest_interval = get_largest_interval(rise_set_intervals)
            if largest_interval.total_seconds() <= duration:
                raise serializers.ValidationError(
                    _("The request duration {} did not fit into any visible intervals. "
                      "The largest visible interval within your window was {}").format(
                        duration / 3600.0, largest_interval.total_seconds() / 3600.0))

        return data


class CadenceRequestSerializer(RequestSerializer):
    cadence = CadenceSerializer()

    def validate_cadence(self, value):
        return value

    def validate_windows(self, value):
        if value:
            raise serializers.ValidationError(_('Cadence requests may not contain windows'))

        return value


class UserRequestSerializer(serializers.ModelSerializer):
    requests = RequestSerializer(many=True)
    submitter = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = (
            'id', 'submitter', 'created', 'state', 'modified'
        )

    @transaction.atomic
    def create(self, validated_data):
        request_data = validated_data.pop('requests')

        user_request = UserRequest.objects.create(**validated_data)

        for r in request_data:
            target_data = r.pop('target')
            constraints_data = r.pop('constraints')
            window_data = r.pop('windows')
            molecule_data = r.pop('molecules')
            location_data = r.pop('location')

            request = Request.objects.create(user_request=user_request, **r)
            Location.objects.create(request=request, **location_data)
            Target.objects.create(request=request, **target_data)
            Constraints.objects.create(request=request, **constraints_data)

            for data in window_data:
                Window.objects.create(request=request, **data)
            for data in molecule_data:
                Molecule.objects.create(request=request, **data)

        debit_ipp_time(user_request)

        return user_request

    def validate(self, data):
        # check that the user belongs to the supplied proposal
        if data['proposal'] not in data['submitter'].proposal_set.all():
            raise serializers.ValidationError(
                _('You do not belong to the proposal you are trying to submit')
            )

        # validation on the operator matching the number of requests
        if data['operator'] == 'SINGLE':
            if len(data['requests']) > 1:
                raise serializers.ValidationError(
                    _("'Single' type user requests must have exactly one child request.")
                )
        elif len(data['requests']) == 1:
            raise serializers.ValidationError(
                _("'{}' type user requests must have more than one child request.".format(data['operator'].title()))
            )

        try:
            request_durations = []
            for request in data['requests']:
                min_window_time = min([window['start'] for window in request['windows']])
                max_window_time = max([window['end'] for window in request['windows']])
                tak = get_time_allocation_key(request['location']['telescope_class'],
                                              data['proposal'],
                                              min_window_time,
                                              max_window_time
                                              )
                duration = get_request_duration(request)
                request_durations.append((tak, duration))

            total_duration_dict = get_total_duration_dict(data['operator'], request_durations)
            # TODO Add 10% rule
            # check the proposal has a time allocation with enough time for all requests depending on operator
            for tak, duration in total_duration_dict.items():
                time_allocation = TimeAllocation.objects.get(
                    semester=tak.semester,
                    telescope_class=tak.telescope_class,
                    proposal=data['proposal'],
                )
                enough_time = False
                if (data['observation_type'] == UserRequest.NORMAL and
                        (time_allocation.std_allocation - time_allocation.std_time_used)) >= (duration / 3600.0):
                    enough_time = True
                elif (data['observation_type'] == UserRequest.TOO and
                        (time_allocation.too_allocation - time_allocation.too_time_used)) >= (duration / 3600.0):
                    enough_time = True
                if not enough_time:
                    raise serializers.ValidationError(
                        _("Proposal {} does not have enough time allocated in semester {} on {} telescopes").format(
                            data['proposal'], tak.semester, tak.telescope_class)
                    )
            # validate the ipp debitting that will take place later
            validate_ipp(data, total_duration_dict)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(_("Time Allocation not found."))
        except TimeAllocationError as e:
            raise serializers.ValidationError(repr(e))

        return data

    def validate_requests(self, value):
        if not value:
            raise serializers.ValidationError(_('You must specify at least 1 request'))
        return value


class DraftUserRequestSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = DraftUserRequest
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        if data['proposal'] not in data['author'].proposal_set.all():
            raise serializers.ValidationError('You are not a member of that proposal')
        return data

    def validate_content(self, data):
        try:
            json.loads(data)
        except JSONDecodeError:
            raise serializers.ValidationError('Content must be valid JSON')
        return data
