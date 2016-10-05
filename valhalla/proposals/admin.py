# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Semester, TimeAllocationGroup, Proposal, TimeAllocation, Membership


class SemesterAdmin(admin.ModelAdmin):
    list_display = ('id', 'start', 'end')
    list_filter = ('start', 'end')
    raw_id_fields = ('proposals',)
admin.site.register(Semester, SemesterAdmin)


class TimeAllocationGroupAdmin(admin.ModelAdmin):
    list_display = ('id',)
admin.site.register(TimeAllocationGroup, TimeAllocationGroupAdmin)


class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'active',
        'title',
        'abstract',
        'tac_priority',
        'tag',
        'public',
    )
    list_filter = ('active', 'tag', 'public')
    raw_id_fields = ('users',)
admin.site.register(Proposal, ProposalAdmin)


class TimeAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'std_allocation',
        'std_time_used',
        'ipp_limit',
        'ipp_time_available',
        'too_allocation',
        'too_time_used',
        'semester',
        'proposal',
        'telescope_class',
    )
    list_filter = ('semester', 'proposal')
admin.site.register(TimeAllocation, TimeAllocationAdmin)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'proposal', 'user', 'role')
    list_filter = ('proposal', 'user')
admin.site.register(Membership, MembershipAdmin)
