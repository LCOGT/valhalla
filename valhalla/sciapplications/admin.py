# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Instrument, Call, ScienceApplication


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('code',)
admin.site.register(Instrument, InstrumentAdmin)


class CallAdmin(admin.ModelAdmin):
    list_display = (
        'semestercode',
        'start',
        'end',
        'callsent',
        'deadline',
        'ptype',
        'active',
    )
    list_filter = ('start', 'end', 'callsent', 'deadline', 'active')
admin.site.register(Call, CallAdmin)


class ScienceApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'app_type',
        'title',
        'semester',
        'pi',
        'status',
    )
    list_filter = ('semester', 'status', 'app_type')
admin.site.register(ScienceApplication, ScienceApplicationAdmin)
