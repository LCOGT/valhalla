# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Semester, TimeAllocationGroup, Proposal, TimeAllocation, Membership, ProposalInvite, ProposalNotification


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'start', 'end')
    list_filter = ('start', 'end')
    raw_id_fields = ('proposals',)


class TimeAllocationGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    raw_id_fields = ['admin']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('id',)
        return self.readonly_fields


class TimeAllocationAdminInline(admin.TabularInline):
    model = TimeAllocation


class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'active',
        'title',
        'tac_priority',
        'tag',
        'public',
        'semesters',
        'pi',
        'created',
        'modified'
    )

    list_filter = ('active', 'tag', 'public')
    raw_id_fields = ('users',)
    inlines = [TimeAllocationAdminInline]
    search_fields = ['id', 'title', 'abstract']
    readonly_fields = []
    actions = ['activate_selected']

    def semesters(self, obj):
        return [semester.id for semester in obj.semester_set.all().distinct()]
    semesters.ordering = ''

    def activate_selected(self, request, queryset):
        activated = queryset.filter(active=False).update(active=True)
        self.message_user(request, 'Successfully activated {} proposal(s)'.format(activated))
    activate_selected.short_description = 'Activate selected inactive proposals'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['id']
        else:
            return self.readonly_fields

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'proposal_title', 'user', 'role')
    list_filter = ('role',)
    search_fields = ['proposal__id', 'user__username', 'user__email', 'proposal__title']
    raw_id_fields = ['user', 'proposal']

    def proposal_title(self, obj):
        return obj.proposal.title


class ProposalInviteAdmin(admin.ModelAdmin):
    model = ProposalInvite


class ProposalNotificationAdmin(admin.ModelAdmin):
    model = ProposalNotification


admin.site.register(Semester, SemesterAdmin)
admin.site.register(TimeAllocationGroup, TimeAllocationGroupAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(Membership, MembershipAdmin)
admin.site.register(ProposalInvite, ProposalInviteAdmin)
admin.site.register(ProposalNotification, ProposalNotificationAdmin)
