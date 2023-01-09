from django.contrib import admin

from runs.admin import RunInline

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'get_str',
        'user',
        'sequence_id',
        'name',
        'date_added',
    )
    list_display_links = list_display
    list_filter = (
        'user',
    )
    fields_create = (
        'user',
        'name',
    )
    fields_modify = (
        'user',
        'name',
        'token',
        'date_added',
    )
    readonly_fields = (
        'token',
        'date_added',
    )
    inlines = (
        RunInline,
    )

    def get_str(self, obj):
        return str(obj)
    get_str.short_description = 'str'

    def get_fields(self, request, obj=None):
        return self.fields_create if obj is None else self.fields_modify

