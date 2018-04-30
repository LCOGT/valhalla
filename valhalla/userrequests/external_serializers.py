from rest_framework import serializers
from django.utils import timezone
from dateutil.parser import parse

from valhalla.userrequests.request_utils import exposure_completion_percentage_from_pond_block


class EventSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    state = serializers.CharField()
    reason = serializers.CharField()
    completedExposures = serializers.IntegerField(required=False)


class BlockMoleculeSerializer(serializers.Serializer):
    event_set = EventSerializer(many=True, read_only=True)
    acquire_mode = serializers.CharField(required=False)
    mtype = serializers.CharField()
    filters = serializers.CharField()
    ag_filter = serializers.CharField()
    ag_name = serializers.CharField()
    user_id = serializers.CharField()
    defocus = serializers.CharField()
    spectra_slit = serializers.CharField(required=False)
    priority = serializers.IntegerField()
    failed = serializers.BooleanField()
    inst_name = serializers.CharField()
    attempted = serializers.BooleanField()
    exp_time = serializers.FloatField()
    completed = serializers.BooleanField()
    bin_y = serializers.IntegerField()
    bin_x = serializers.IntegerField()
    ag_exp_time = serializers.CharField()
    tag_id = serializers.CharField()
    group = serializers.CharField()
    exp_cnt = serializers.IntegerField()
    acquire_radius_arcsec = serializers.CharField(required=False)
    ag_mode = serializers.CharField()


class BlockSerializer(serializers.Serializer):
    HISTORY_FIELDS = [
        'start', 'end', 'canceled', 'aborted', 'cancel_reason', 'cancel_date',
        'site', 'observatory', 'telescope', 'completed', 'failed', 'attempted'
    ]

    molecules = BlockMoleculeSerializer(many=True, read_only=True)
    id = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    canceled = serializers.BooleanField()
    aborted = serializers.BooleanField()
    cancel_reason = serializers.CharField(allow_blank=True)
    cancel_date = serializers.CharField(allow_null=True)
    site = serializers.CharField()
    observatory = serializers.CharField()
    telescope = serializers.CharField()
    priority = serializers.IntegerField()
    is_too = serializers.BooleanField()
    completed = serializers.SerializerMethodField()
    percent_completed = serializers.SerializerMethodField()
    failed = serializers.SerializerMethodField()
    attempted = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    fail_reason = serializers.SerializerMethodField()

    def get_completed(self, obj):
        return all(m['completed'] for m in obj['molecules'])

    def get_failed(self, obj):
        return any(m['failed'] for m in obj['molecules'])

    def get_attempted(self, obj):
        return any(m['attempted'] for m in obj['molecules'])

    def get_percent_completed(self, obj):
        return exposure_completion_percentage_from_pond_block(obj)

    def get_status(self, obj):
        status = 'NOT_ATTEMPTED'
        if self.get_completed(obj):
            return 'COMPLETED'
        if self.get_percent_completed(obj) > 0:
            return 'PARTIALLY-COMPLETED'
        if obj['aborted']:
            return 'ABORTED'
        if self.get_failed(obj):
            return 'FAILED'
        if obj['canceled']:
            return 'CANCELED'
        if not obj['canceled'] and not self.get_failed(obj):
            if timezone.make_aware(parse(obj['end'])) > timezone.now():
                status = 'SCHEDULED'
                if timezone.make_aware(parse(obj['start'])) < timezone.now():
                    status = 'IN_PROGRESS'
        return status

    def get_fail_reason(self, obj):
        for molecule in obj['molecules']:
            if molecule['failed']:
                for event in molecule['event_set']:
                    return '{0}: {1}'.format(event['state'], event['reason'])
        return ''
