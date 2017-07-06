from rest_framework import serializers
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from json import JSONDecodeError
import logging
import json

from valhalla.proposals.models import TimeAllocation
from valhalla.userrequests.models import Request, Target, Window, UserRequest, Location, Molecule, Constraints
from valhalla.userrequests.models import DraftUserRequest
from valhalla.userrequests.state_changes import debit_ipp_time, TimeAllocationError, validate_ipp
from valhalla.userrequests.target_helpers import SiderealTargetHelper, NonSiderealTargetHelper, SatelliteTargetHelper
from valhalla.common.configdb import configdb
from valhalla.userrequests.request_utils import MOLECULE_TYPE_DISPLAY
from valhalla.userrequests.duration_utils import (get_request_duration, get_total_duration_dict, OVERHEAD_ALLOWANCE,
                                                  get_molecule_duration, get_num_exposures, get_semester_in)
from datetime import timedelta
from valhalla.common.rise_set_utils import get_rise_set_intervals


logger = logging.getLogger(__name__)


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
    max_airmass = serializers.FloatField(
        default=1.6, validators=[MinValueValidator(1.0), MaxValueValidator(25.0)]  # Duplicated in models.py
    )
    min_lunar_distance = serializers.FloatField(
        default=30.0, validators=[MinValueValidator(0.0), MaxValueValidator(180.0)]  # Duplicated in models.py
    )

    class Meta:
        model = Constraints
        exclude = ('request', 'id')


class MoleculeSerializer(serializers.ModelSerializer):
    fill_window = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = Molecule
        exclude = ('request', 'id', 'sub_x1', 'sub_x2', 'sub_y1', 'sub_y2', 'priority')

    def validate_instrument_name(self, value):
        if value and value not in configdb.get_active_instrument_types({}):
            raise serializers.ValidationError(
                _("Invalid instrument name {}. Valid instruments may include: {}").format(
                    value, ', '.join(configdb.get_active_instrument_types({}))
                )
            )
        return value

    def validate(self, data):
        # set special defaults if it is a spectrograph
        if configdb.is_spectrograph(data['instrument_name']):
            if 'ag_mode' not in data:
                data['ag_mode'] = 'ON'
            if 'acquire_mode' not in data:
                data['acquire_mode'] = 'WCS'

            if data['acquire_mode'] == 'BRIGHTEST' and not data.get('acquire_radius_arcsec'):
                raise serializers.ValidationError({'acquire_radius_arcsec': 'Acquire radius must be positive.'})

        types_that_require_filter = ['expose', 'auto_focus', 'zero_pointing', 'standard', 'sky_flat']
        types_that_require_slit = ['spectrum', 'arc', 'lamp_flat']

        # check that the filter is available in the instrument type specified
        available_filters = configdb.get_filters(data['instrument_name'])
        if configdb.is_spectrograph(data['instrument_name']):
            if (data['type'].lower() in types_that_require_slit
                    and data.get('spectra_slit', '').lower() not in available_filters):
                raise serializers.ValidationError(
                    {'spectra_slit': _("Invalid spectra slit {} for instrument {}. Valid slits are: {}").format(
                        data.get('spectra_slit', ''), data['instrument_name'], ", ".join(available_filters)
                    )}
                )
        elif data['type'].lower() in types_that_require_filter:
            if not data.get('filter'):
                raise serializers.ValidationError(
                    {'filter': _("You must specify a filter for {} exposures.").format(
                        MOLECULE_TYPE_DISPLAY[data['type']]
                    )}
                )
            elif data['filter'].lower() not in available_filters:
                raise serializers.ValidationError(
                    {'filter': _("Invalid filter {} for instrument {}. Valid filters are: {}").format(
                        data['filter'], data['instrument_name'], ", ".join(available_filters)
                    )}
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

        site_data_dict = {site['code']: site for site in configdb.get_site_data()}
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

    def to_representation(self, instance):
        '''
        This method is overridden to remove blank fields from serialized output. We could put this into a subclassed
        ModelSerializer if we want it to apply to all our Serializers.
        :param instance:
        :return:
        '''
        rep = super(serializers.ModelSerializer, self).to_representation(instance)
        return {key: val for key, val in rep.items() if val}


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        exclude = ('request', 'id')

    def validate(self, data):
        if data['end'] <= data['start']:
            msg = _("Window end '{}' cannot be earlier than window start '{}'.").format(data['start'], data['end'])
            raise serializers.ValidationError(msg)

        if not get_semester_in(data['start'], data['end']):
            raise serializers.ValidationError('The observation window does not fit within any defined semester.')
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
        extra_kwargs = {
            'name': {'error_messages': {'blank': 'Please provide a name.'}}
        }

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
    duration = serializers.ReadOnlyField()

    class Meta:
        model = Request
        read_only_fields = (
            'id', 'fail_count', 'scheduled_count', 'created', 'completed', 'duration', 'state',
        )
        exclude = ('user_request',)

    def validate_molecules(self, value):
        if not value:
            raise serializers.ValidationError(_('You must specify at least 1 molecule'))

        # Set the relative priority of molecules in order
        for i, molecule in enumerate(value):
            molecule['priority'] = i + 1

        # Make sure each molecule has the same instrument name
        if len(set(molecule['instrument_name'] for molecule in value)) > 1:
            raise serializers.ValidationError(_('Each Molecule must specify the same instrument name'))

        if sum([mol.get('fill_window', False) for mol in value]) > 1:
            raise serializers.ValidationError(_('Only one molecule can have `fill_window` set'))

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
        if configdb.is_spectrograph(data['molecules'][0]['instrument_name']) and 'rot_mode' not in data['target']:
                data['target']['rot_mode'] = 'VFLOAT'

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
        if data.get('windows'):
            duration = get_request_duration(data)
            rise_set_intervals = get_rise_set_intervals(data)
            largest_interval = timedelta(seconds=0)
            for interval in rise_set_intervals:
                largest_interval = max((interval[1] - interval[0]), largest_interval)

            for molecule in data['molecules']:
                if molecule.get('fill_window'):
                    molecule_duration = get_molecule_duration(molecule_dict=molecule)
                    num_exposures = get_num_exposures(
                        molecule, largest_interval - timedelta(seconds=duration - molecule_duration)
                    )
                    molecule['exposure_count'] = num_exposures
                    duration = get_request_duration(data)
                # delete the fill window attribute, it is only used for this validation
                try:
                    del molecule['fill_window']
                except KeyError:
                    pass
            if largest_interval.total_seconds() <= 0:
                raise serializers.ValidationError(
                    _(
                        'According to the constraints of the request, the target is never visible within the time '
                        'window. Check that the target is in the nighttime sky. Consider modifying the time '
                        'window or loosening the airmass or lunar separation constraints. '
                    )
                )
            if largest_interval.total_seconds() <= duration:
                raise serializers.ValidationError(
                    (
                        'According to the constraints of the request, the target is visible for a maximum of {0:.2f} '
                        'hours within the time window. This is less than the duration of your request {1:.2f} hours. Consider '
                        'expanding the time window or loosening the airmass or lunar separation constraints.'
                    ).format(
                        largest_interval.total_seconds() / 3600.0,
                        duration / 3600.0
                    )
                )
        return data


class CadenceRequestSerializer(RequestSerializer):
    cadence = CadenceSerializer()
    windows = WindowSerializer(required=False, many=True)

    def validate_cadence(self, value):
        return value

    def validate_windows(self, value):
        if value:
            raise serializers.ValidationError(_('Cadence requests may not contain windows'))

        return value


class UserRequestSerializer(serializers.ModelSerializer):
    requests = RequestSerializer(many=True)
    submitter = serializers.StringRelatedField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = (
            'id', 'submitter', 'created', 'state', 'modified'
        )
        extra_kwargs = {
            'proposal': {'error_messages': {'null': 'Please provide a proposal.'}},
            'group_id': {'error_messages': {'blank': 'Please provide a title.'}}
        }

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

        logger.info('UserRequest created', extra={'tags': {'user': user_request.submitter.username,
                                                           'tracking_num': user_request.id,
                                                           'group_id': user_request.group_id}})

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
            total_duration_dict = get_total_duration_dict(data)
            for tak, duration in total_duration_dict.items():
                time_allocation = TimeAllocation.objects.get(
                    semester=tak.semester,
                    telescope_class=tak.telescope_class,
                    proposal=data['proposal'],
                )
                time_available = 0
                if data['observation_type'] == UserRequest.NORMAL:
                    time_available = time_allocation.std_allocation - time_allocation.std_time_used
                elif data['observation_type'] == UserRequest.TOO:
                    time_available = time_allocation.too_allocation - time_allocation.too_time_used

                if time_available <= 0.0:
                    raise serializers.ValidationError(
                        _("Proposal {} does not have any time left allocated in semester {} on {} telescopes").format(
                            data['proposal'], tak.semester, tak.telescope_class)
                    )
                elif time_available * OVERHEAD_ALLOWANCE < (duration / 3600.0):
                    raise serializers.ValidationError(
                        _("Proposal {} does not have enough time allocated in semester {} on {} telescopes").format(
                            data['proposal'], tak.semester, tak.telescope_class)
                    )
            # validate the ipp debitting that will take place later
            validate_ipp(data, total_duration_dict)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                _("You do not have sufficient time allocated on the resource you're requesting for this proposal.")
            )
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
