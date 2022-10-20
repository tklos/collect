from django.contrib import admin

from .models import Run


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = (
        'get_str',
        'get_user',
        'device',
        'name',
        'date_from',
        'date_to',
    )
    list_display_links = list_display
    list_filter = (
        'device',
        'device__user',
    )
    ordering = ('date_from',)

    def get_str(self, obj):
        return str(obj)
    get_str.short_description = 'str'

    def get_user(self, obj):
        return obj.device.user.username
    get_user.short_description = 'User'
