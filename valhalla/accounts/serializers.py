from rest_framework import serializers
from django.contrib.auth.models import User
from valhalla.accounts.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ('id', 'user')


class UserSerializer(serializers.ModelSerializer):
    proposals = serializers.SerializerMethodField()
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ('username', 'profile', 'proposals')

    def get_proposals(self, obj):
        return [proposal.id for proposal in obj.proposal_set.all()]
