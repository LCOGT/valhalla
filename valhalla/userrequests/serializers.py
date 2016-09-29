from rest_framework import serializers

from valhalla.userrequests.models import Request, Target, Window, UserRequest, Location, Molecule, Constraints


class ConstraintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraints
        fields = ('__all__')

class MoleculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Molecule
        fields = ('__all__')

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('__all__')
        read_only_fields = ('site', 'observatory', 'telescope')


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        fields = ('__all__')


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = (
            'name', 'type', 'ra', 'dec', 'coordinate_system', 'equinox',
            'proper_motion_ra', 'proper_motion_dec', 'epoch', 'parallax', 'epochofel',
            'orbinc', 'longascnode', 'longofperih', 'argofperih', 'meandist', 'perihdist',
            'eccentricity', 'meanlong', 'meananom', 'dailymot', 'epochofperih', 'acquire_mode'
        )


class RequestSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    constraints = ConstraintsSerializer()
    target = TargetSerializer()
    molecules = MoleculeSerializer(many=True, source='molecule_set')
    windows = WindowSerializer(many=True, source='window_set')

    class Meta:
        model = Request
        fields = (
            'id', 'fail_count', 'created', 'scheduled_count',
            'completed', 'target', 'molecules', 'windows', 'location',
            'constraints',
        )
        read_only_fields = (
            'id', 'fail_count', 'scheduled_count', 'created', 'completed'
        )


class UserRequestSerializer(serializers.ModelSerializer):
    requests = RequestSerializer(many=True)

    class Meta:
        model = UserRequest
        fields = (
            'id', 'submitter', 'group_id',
            'operator', 'ipp_value', 'created',
            'state', 'modified', 'requests',
        )
        read_only_fields = (
            'id', 'submitter', 'group_id',
            'created', 'state', 'modified'
        )

    def create(self, validated_data):
        requests_data = validated_data.pop('requests')

        user_request = UserRequest.objects.create(**validated_data)

        for r in requests_data:
            target_data = r.pop('target')
            constraints_data = r.pop('constraints')
            window_data = r.pop('windows')
            molecule_data = r.pop('molecules')
            location_data = r.pop('location')

            request = Request.objects.create(user_request=user_request, **r)

            Location.objects.create(**location_data, request=request)
            Target.objects.create(**target_data, request=request)
            Constraints.objects.create(**constraints_data, request=request)

            for _ in window_data:
                Window.objects.create(**_, request=request)
            for _ in molecule_data:
                Molecule.objects.create(**_, request=request)

        return user_request
