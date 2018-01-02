# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import reverse

from .models import UserRequest, Request, Location, Target, Window, Molecule, Constraints


class MoleculeInline(admin.TabularInline):
    model = Molecule
    extra = 0


class LocationInline(admin.TabularInline):
    model = Location
    extra = 0


class TargetInline(admin.TabularInline):
    model = Target
    extra = 0


class WindowInline(admin.TabularInline):
    model = Window
    extra = 0


class ConstraintsInline(admin.TabularInline):
    model = Constraints
    extra = 0


class UserRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'submitter',
        'proposal',
        'group_id',
        'observation_type',
        'operator',
        'ipp_value',
        'created',
        'state',
        'modified',
        'requests_count',
    )
    list_filter = ('state', 'created', 'modified')
    search_fields = ('group_id',)
    readonly_fields = ('requests', 'requests_count')

    def requests_count(self, obj):
        return obj.requests.count()

    def requests(self, obj):
        html = ''
        for request in obj.requests.all():
            html += '<a href="{0}">{1}</a></p>'.format(
                reverse('admin:userrequests_request_change', args=(request.id,)),
                request.id
            )
        return html
    requests.allow_tags = True


class RequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_request',
        'observation_note',
        'state',
        'modified',
        'fail_count',
        'scheduled_count',
        'created',
        'completed',
    )
    raw_id_fields = (
        'user_request',
    )
    list_filter = ('state', 'modified', 'created', 'completed')
    inlines = [MoleculeInline, WindowInline, TargetInline, ConstraintsInline, LocationInline]


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'telescope_class',
        'site',
        'observatory',
        'telescope',
    )
    list_filter = ('telescope_class',)


class TargetAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'request',
        'type',
        'roll',
        'pitch',
        'hour_angle',
        'ra',
        'dec',
        'altitude',
        'azimuth',
        'coordinate_system',
        'equinox',
        'proper_motion_ra',
        'proper_motion_dec',
        'epoch',
        'parallax',
        'diff_pitch_rate',
        'diff_roll_rate',
        'diff_epoch_rate',
        'diff_pitch_acceleration',
        'diff_roll_acceleration',
        'scheme',
        'epochofel',
        'orbinc',
        'longascnode',
        'longofperih',
        'argofperih',
        'meandist',
        'perihdist',
        'eccentricity',
        'meanlong',
        'meananom',
        'dailymot',
        'epochofperih',
        'rot_mode',
        'rot_angle',
    )
    list_filter = ('type',)
    search_fields = ('name',)


class WindowAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'start', 'end')
    list_filter = ('start', 'end')
    raw_id_fields = (
        'request',
    )


class MoleculeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'type',
        'args',
        'priority',
        'ag_name',
        'ag_mode',
        'ag_filter',
        'ag_exp_time',
        'instrument_name',
        'filter',
        'readout_mode',
        'spectra_lamp',
        'spectra_slit',
        'acquire_mode',
        'acquire_radius_arcsec',
        'exposure_time',
        'exposure_count',
        'bin_x',
        'bin_y',
        'sub_x1',
        'sub_x2',
        'sub_y1',
        'sub_y2',
        'defocus',
    )
    raw_id_fields = (
        'request',
    )
    list_filter = ('type',)


class ConstraintsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'max_airmass',
        'min_lunar_distance',
        'max_lunar_phase',
        'max_seeing',
        'min_transparency',
    )


admin.site.register(Constraints, ConstraintsAdmin)
admin.site.register(Molecule, MoleculeAdmin)
admin.site.register(Window, WindowAdmin)
admin.site.register(Target, TargetAdmin)
admin.site.register(UserRequest, UserRequestAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Request, RequestAdmin)
