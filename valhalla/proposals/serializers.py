from rest_framework import serializers

from valhalla.proposals.models import Proposal, TimeAllocation, Semester


class TimeAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeAllocation
        fields = '__all__'


class ProposalSerializer(serializers.ModelSerializer):
    timeallocation_set = TimeAllocationSerializer(many=True)
    users = serializers.StringRelatedField(many=True)
    pi = serializers.StringRelatedField()

    class Meta:
        model = Proposal
        fields = '__all__'


class SemesterSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ('id', 'start', 'end')
