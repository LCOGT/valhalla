# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.html import format_html
from django.core.urlresolvers import reverse


from .models import Instrument, Call, ScienceApplication, TimeRequest
from valhalla.proposals.models import Proposal


class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('code', 'display', 'telescope_class')
admin.site.register(Instrument, InstrumentAdmin)


class CallAdmin(admin.ModelAdmin):
    list_display = (
        'semester',
        'opens',
        'deadline',
        'proposal_type',
    )
    list_filter = ('opens', 'deadline', 'proposal_type')
admin.site.register(Call, CallAdmin)


class TimeRequestAdminInline(admin.TabularInline):
    model = TimeRequest


class ScienceApplicationAdmin(admin.ModelAdmin):
    inlines = [TimeRequestAdminInline]
    list_display = (
        'title',
        'call',
        'status',
        'submitter',
        'tac_rank',
        'preview_link',
    )
    list_filter = ('call', 'status', 'call__proposal_type')
    actions = ['accept', 'reject', 'port']

    def preview_link(self, obj):
        return format_html(
            '<a href="{}">View PDF</a> <a href="{}">View on site</a>',
            reverse('sciapplications:pdf', kwargs={'pk': obj.id}),
            reverse('sciapplications:detail', kwargs={'pk': obj.id})
        )

    def accept(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.ACCEPTED)
        self.message_user(request, '{} application(s) were successfully accepted'.format(rows))

    def reject(self, request, queryset):
        rows = queryset.filter(status=ScienceApplication.SUBMITTED).update(status=ScienceApplication.REJECTED)
        self.message_user(request, '{} application(s) were successfully rejected'.format(rows))

    def port(self, request, queryset):
        apps = queryset.filter(status=ScienceApplication.ACCEPTED)
        for app in apps:
            if Proposal.objects.filter(id=app.proposal_code).exists():
                self.message_user(
                    request,
                    'A proposal named {} already exists. Check your tac rank?'.format(app.proposal_code),
                    level='ERROR'
                )
            else:
                app.convert_to_proposal()
                self.message_user(request, 'Proposal {} successfully created.'.format(app.proposal))

admin.site.register(ScienceApplication, ScienceApplicationAdmin)
