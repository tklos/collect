from django.contrib import admin

from measurements.admin import MeasurementInline

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
    # inlines = (
    #     MeasurementInline,
    # )

    def get_str(self, obj):
        return str(obj)
    get_str.short_description = 'str'

    def get_user(self, obj):
        return obj.device.user.username
    get_user.short_description = 'User'


class RunInline(admin.TabularInline):
    model = Run
    fields = (
        'name',
        'date_from',
        'date_to',
        'get_num_measurements',
    )
    readonly_fields = fields
    ordering = ('-date_from',)
    show_change_link = True
    extra = 0

    def get_num_measurements(self, obj):
        return obj.num_measurements
    get_num_measurements.short_description = 'Num meas.'
