from django.contrib import admin
from valhalla.accounts.models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.contrib.admin.models import LogEntry


class LogEntryAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in LogEntry._meta.get_fields()]
    list_display = [f.name for f in LogEntry._meta.get_fields()]
    actions = None

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class UserProfileInline(admin.StackedInline):
    model = Profile
    max_num = 1
    can_delete = False


class UserAdmin(AuthUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(LogEntry, LogEntryAdmin)
