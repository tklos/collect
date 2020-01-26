from django.contrib import admin

from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'device',
        'get_user',
        'get_device',
        'date_added',
        'data',
    )
    list_display_links = list_display
    list_filter = (
        'device__user',
        'device',
    )

    def get_user(self, obj):
        return obj.device.user.username
    get_user.short_description = 'User'

    def get_device(self, obj):
        return '{}: {}'.format(obj.device.sequence_id, obj.device.name)
    get_device.short_description = 'Device'

