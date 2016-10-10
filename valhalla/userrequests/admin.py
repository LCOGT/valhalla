# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import UserRequest, Request, Location, Target, Window, Molecule, Constraints


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
    )
    list_filter = ('submitter', 'proposal', 'created', 'modified')
admin.site.register(UserRequest, UserRequestAdmin)


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
    list_filter = ('user_request', 'modified', 'created', 'completed')
admin.site.register(Request, RequestAdmin)


class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'request',
        'telescope_class',
        'site',
        'observatory',
        'telescope',
    )
    list_filter = ('request',)
admin.site.register(Location, LocationAdmin)


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
        'acquire_mode',
        'rot_mode',
        'rot_angle',
    )
    list_filter = ('request',)
    search_fields = ('name',)
admin.site.register(Target, TargetAdmin)


class WindowAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'start', 'end')
    list_filter = ('request', 'start', 'end')
admin.site.register(Window, WindowAdmin)


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
    list_filter = ('request',)
admin.site.register(Molecule, MoleculeAdmin)


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
    list_filter = ('request',)
admin.site.register(Constraints, ConstraintsAdmin)
