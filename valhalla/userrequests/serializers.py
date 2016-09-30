from rest_framework import serializers

from valhalla.userrequests.models import Request, Target, Window, UserRequest, Location, Molecule, Constraints


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
        read_only_fields = ('site', 'observatory', 'telescope')
        exclude = ('request', 'id')


class WindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Window
        exclude = ('request', 'id')


class TargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        exclude = ('request', 'id')


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


class UserRequestSerializer(serializers.ModelSerializer):
    requests = RequestSerializer(many=True, source='request_set')

    class Meta:
        model = UserRequest
        fields = '__all__'
        read_only_fields = (
            'id', 'submitter', 'created', 'state', 'modified'
        )

    def create(self, validated_data):
        request_data = validated_data.pop('request_set')

        user_request = UserRequest.objects.create(submitter=self.context['request'].user, **validated_data)

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
