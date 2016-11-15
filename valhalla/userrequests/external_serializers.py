from rest_framework import serializers
from django.utils import timezone
from dateutil.parser import parse

"""
Serializers for external models from outside services
recieved via json, etc
"""


class EventSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    state = serializers.CharField()
    reason = serializers.CharField()


class BlockMoleculeSerializer(serializers.Serializer):
    event = EventSerializer(many=True, read_only=True)
    acquire_mode = serializers.CharField()
    sub_y1 = serializers.CharField()
    sub_y2 = serializers.CharField()
    mtype = serializers.CharField()
    filters = serializers.CharField()
    ag_filter = serializers.CharField()
    ag_name = serializers.CharField()
    user_id = serializers.CharField()
    defocus = serializers.CharField()
    spectra_slit = serializers.CharField()
    priority = serializers.IntegerField()
    failed = serializers.BooleanField()
    inst_name = serializers.CharField()
    attempted = serializers.BooleanField()
    exp_time = serializers.FloatField()
    completed = serializers.BooleanField()
    margs = serializers.CharField()
    bin_y = serializers.IntegerField()
    bin_x = serializers.IntegerField()
    sub_x2 = serializers.CharField()
    sub_x1 = serializers.CharField()
    ag_exp_time = serializers.CharField()
    expose_at = serializers.CharField()
    tag_id = serializers.CharField()
    group = serializers.CharField()
    exp_cnt = serializers.IntegerField()
    required = serializers.BooleanField()
    spectra_lamp = serializers.CharField()
    acquire_radius_arcsec = serializers.CharField()
    ag_mode = serializers.CharField()
    readout_mode = serializers.CharField()


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
    failed = serializers.SerializerMethodField()
    attempted = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_completed(self, obj):
        return all(m['completed'] for m in obj['molecules'])

    def get_failed(self, obj):
        return any(m['failed'] for m in obj['molecules'])

    def get_attempted(self, obj):
        return any(m['attempted'] for m in obj['molecules'])

    def get_status(self, obj):
        status = 'SCHEDULED-PAST'
        if self.get_completed(obj):
            return 'COMPLETED'
        if self.get_failed(obj):
            return 'FAILED'
        if not obj['canceled'] and not self.get_failed(obj):
            if timezone.make_aware(parse(obj['end'])) > timezone.now():
                status = 'SCHEDULED'
                if timezone.make_aware(parse(obj['start'])) < timezone.now():
                    status = 'IN_PROGRESS'
        return status
