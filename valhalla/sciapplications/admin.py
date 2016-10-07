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
        'title',
        'call',
        'status',
    )
    list_filter = ('call', 'status', 'call__proposal_type')
    actions = ['accept', 'reject', 'port']

    def accept(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.ACCEPTED)
        self.message_user(request, '{} application(s) were successfully accepted'.format(rows))

    def reject(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.REJECTED)
        self.message_user(request, '{} application(s) were successfully rejected'.format(rows))

    def port(self, request, queryset):
        apps = queryset.filter(status=ScienceApplication.ACCEPTED)
        for app in apps:
            app.convert_to_proposal()
        self.message_user(request, '{} application(s) were converted to proposals'.format(len(apps)))

admin.site.register(ScienceApplication, ScienceApplicationAdmin)
