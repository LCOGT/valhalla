# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Instrument, Call, ScienceApplication


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('code',)
admin.site.register(Instrument, InstrumentAdmin)


class CallAdmin(admin.ModelAdmin):
    list_display = (
        'semester',
        'start',
        'end',
        'call_sent',
        'deadline',
        'proposal_type',
        'active',
    )
    list_filter = ('start', 'end', 'call_sent', 'deadline', 'active')
admin.site.register(Call, CallAdmin)


class ScienceApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'call',
        'title',
        'call',
        'pi',
        'status',
    )
    list_filter = ('call', 'status', 'call__proposal_type')
admin.site.register(ScienceApplication, ScienceApplicationAdmin)
