from rest_framework import serializers
from django.contrib.auth.models import User

from valhalla.userrequests.models import Request, Target, Window, UserRequest, Location, Molecule, Constraints
from valhalla.common.configdb_utils import get_configdb_data

class ConstraintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraints
        exclude = ('request', 'id')


class MoleculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Molecule
        exclude = ('request', 'id', 'sub_x1', 'sub_x2', 'sub_y1', 'sub_y2')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        exclude = ('request', 'id')

    def validate(self, data):
        if 'observatory' in data and not 'site' in data:
            raise serializers.ValidationError("Must specify a site with an observatory.")
        if 'telescope' in data and not 'observatory' in data:
            raise serializers.ValidationError("Must specify an observatory with a telescope.")

        site_json = get_configdb_data()
        site_data_dict = {site['code']: site for site in site_json}
        if 'site' in data:
            if data['site'] not in site_data_dict:
                msg = 'Site {} not valid. Valid choices: {}'.format(data['site'], ', '.join(site_data_dict.keys()))
                raise serializers.ValidationError(msg)
            obs_set = site_data_dict[data['site']]['enclosure_set']
            obs_dict = {obs['code']:obs for obs in obs_set}
            if 'observatory' in data:
                if data['observatory'] not in obs_dict:
                    msg = 'Observatory {} not valid. Valid choices: {}'.format(data['observatory'], ', '.join(obs_dict.keys()))
                    raise serializers.ValidationError(msg)

                tel_set = obs_dict[data['observatory']]['telescope_set']
                tel_list = [tel['code'] for tel in tel_set]
                if 'telescope' in data and data['telescope'] not in tel_list:
                    msg = 'Telescope {} not valid. Valid choices: {}'.format(data['telescope'], ', '.join(tel_list))
                    raise serializers.ValidationError(msg)

        return data


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        exclude = ('request', 'id')


class TargetSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        if fields is not None:
            allowed = ('name', 'type', 'coordinate_system', 'equinox', 'epoch')
            if fields['type'] == 'SIDEREAL' or fields['type'] == 'STATIC':
                allowed += (
                    'ra', 'dec', 'proper_motion_ra', 'proper_motion_dec', 'parallax'
                )
            elif fields['type'] == 'NON_SIDEREAL':
                allowed += ('epochofel', 'orbinc', 'longascnode', 'eccentricity', 'scheme')
                if fields['scheme'] == 'ASA_MAJOR_PLANET':
                    allowed += ('longofperih', 'meandist', 'meanlong', 'dailymot')
                elif fields['scheme'] == 'ASA_MINOR_PLANET':
                    allowed += ('argofperih', 'meandist', 'meananom')
                elif fields['scheme'] == 'ASA_COMET':
                    allowed += ('argofperih', 'perihdist', 'epochofperih')
                elif fields['scheme'] == 'JPL_MAJOR_PLANET':
                    allowed += ('argofperih', 'meandist', 'meananom', 'dailymot')
                elif fields['scheme'] == 'JPL_MINOR_PLANET':
                    allowed += ('argofperih', 'perihdist', 'epochofperih')
                elif fields['scheme'] == 'MPC_MINOR_PLANET':
                    allowed += ('argofperih', 'meandist', 'meananom')
                elif fields['scheme'] == 'MPC_COMET':
                    allowed += ('argofperih', 'perihdist', 'epochofperih')
            elif fields['type'] == 'SATELLITE':
                allowed += (
                    'altitude', 'azimuth', 'diff_pitch_rate', 'diff_roll_rate', 'diff_epoch_rate',
                    'diff_pitch_acceleration', 'diff_roll_acceleration'
                )

            # Drop any fields that are not specified in the `fields` argument.
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = Target
        exclude = ('request', 'id')

    def validate(self, data):
        if data['type'] == 'SIDEREAL' or data['type'] == 'STATIC':
            data = self._validate_sidereal_target(data)
        elif data['type'] == 'NON_SIDEREAL':
            data = self._validate_nonsidereal_target(data)
        return data

    def _validate_sidereal_target(self, data):
        # check that sidereal specific defaults are filled in
        data.setdefault('coordinate_system', default='ICRS')
        data.setdefault('equinox', default='J2000')

        # Complain if proper motion has been provided, and there is no explicit epoch
        if ( ( 'proper_motion_ra' in data ) or
             ( 'proper_motion_dec' in data ) ):
            if 'epoch' not in data:
                msg = 'Epoch required, since proper motion has been specified.'
                raise serializers.ValidationError(msg)
        # Otherwise, set epoch to 2000
        elif 'epoch' not in data:
            data['epoch'] = 2000.0

        data.setdefault('proper_motion_ra', 0.0)
        data.setdefault('proper_motion_dec', 0.0)
        data.setdefault('parallax', 0.0)

        # now check that if 'ra' exists 'dec' also exists
        if 'ra' not in data or 'dec' not in data:
            raise serializers.ValidationError('A Sidereal target must specify an `ra` and `dec`')
        return data


    def _validate_nonsidereal_target(self, data):
        # Tim wanted an eccentricity limit of 0.9 for non-comet targets
        eccentricity_limit = 0.9
        scheme = data['scheme']
        if not 'COMET' in scheme.upper() and data['eccentricity'] > eccentricity_limit:
            msg = "Non sidereal pointing of scheme {} requires eccentricity to be lower than {}. ".format(scheme, eccentricity_limit)
            msg += "Submit with scheme MPC_COMET to use your eccentricity of {}.".format(data['eccentricity'])
            raise serializers.ValidationError(msg)
        return data


class RequestSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    constraints = ConstraintsSerializer()
    target = TargetSerializer()
    molecules = MoleculeSerializer(many=True, source='molecule_set')
    windows = WindowSerializer(many=True, source='window_set')

    class Meta:
        model = Request
        read_only_fields = (
            'id', 'fail_count', 'scheduled_count', 'created', 'completed'
        )
        exclude = ('user_request',)

    def validate_molecules(self, value):
        if not value:
            raise serializers.ValidationError('You must specify at least 1 molecule')
        return value

    def validate(self, data):
        # Target special validation
        if data['molecule_set'][0]['instrument_name'].upper() == '2M0-FLOYDS-SCICAM':
            if not 'acquire_mode' in data['target']:
                # the normal default is 'OPTIONAL', but for floyds the default is 'ON'
                data['target']['acquire_mode'] = 'ON'
        return data


class UserRequestSerializer(serializers.ModelSerializer):
    requests = RequestSerializer(many=True, source='request_set', required=True)
    submitter = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = (
            'id', 'submitter', 'created', 'state', 'modified'
        )

    def create(self, validated_data):
        request_data = validated_data.pop('request_set')

        user_request = UserRequest.objects.create(**validated_data)

        for r in request_data:
            target_data = r.pop('target')
            constraints_data = r.pop('constraints')
            window_data = r.pop('window_set')
            molecule_data = r.pop('molecule_set')
            location_data = r.pop('location')

            request = Request.objects.create(user_request=user_request, **r)
            Location.objects.create(request=request, **location_data)
            Target.objects.create(request=request, **target_data)
            Constraints.objects.create(request=request, **constraints_data)

            for _ in window_data:
                Window.objects.create(request=request, **_)
            for _ in molecule_data:
                Molecule.objects.create(request=request, **_)

        return user_request

    def validate(self, data):
        # check that the user belongs to the supplied proposal
        user = User.objects.get(username=data['submitter'])
        if not user.proposal_set.filter(id=data['proposal']):
            raise serializers.ValidationError(
                'You do not belong to the proposal you are trying to submit'
            )

        return data

    def validate_requests(self, value):
        if not value:
            raise serializers.ValidationError('You must specify at least 1 request')
        return value
