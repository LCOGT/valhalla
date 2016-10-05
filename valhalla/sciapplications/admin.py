# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Instrument, Call, ScienceApplication, TimeRequest


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


class TimeRequestAdminInline(admin.TabularInline):
    model = TimeRequest


class ScienceApplicationAdmin(admin.ModelAdmin):
    inlines = [TimeRequestAdminInline]
    list_display = (
        'call',
        'title',
        'call',
        'pi',
        'status',
    )
    list_filter = ('call', 'status', 'call__proposal_type')
    actions = ['accept', 'reject', 'port']

    def accept(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.ACCEPTED)
        self.message_user(request, '{} applications were successfully accepted'.format(rows))

    def reject(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.REJECTED)
        self.message_user(request, '{} applications were successfully rejected'.format(rows))

    def port(self, request, queryset):
        for app in queryset.filter(status=ScienceApplication.ACCEPTED):
            app.convert_to_proposal()

admin.site.register(ScienceApplication, ScienceApplicationAdmin)
