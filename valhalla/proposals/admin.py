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


class TimeAllocationAdminInline(admin.TabularInline):
    model = TimeAllocation


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
    inlines = [TimeAllocationAdminInline]
admin.site.register(Proposal, ProposalAdmin)


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'user', 'role')
    list_filter = ('proposal', 'user')
admin.site.register(Membership, MembershipAdmin)
