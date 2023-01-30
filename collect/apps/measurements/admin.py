from django import forms
from django.contrib import admin

from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = (
        'device',
        'get_user',
        'run',
        'date_added',
        'data',
    )
    list_display_links = list_display
    list_filter = (
        'device__user',
        'device',
    )
    readonly_fields = (
        'date_added',
    )
    ordering = ('date_added',)

    def get_user(self, obj):
        return obj.device.user.username
    get_user.short_description = 'User'

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'data':
            return db_field.formfield(widget=forms.TextInput(attrs={'size': 50}))
        return super().formfield_for_dbfield(db_field, **kwargs)


class MeasurementInline(admin.TabularInline):
    model = Measurement
    fields = (
        'date_added',
        'data',
    )
    readonly_fields = fields
    ordering = ('-date_added',)
    show_change_link = True
    extra = 0

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'data':
            return db_field.formfield(widget=forms.TextInput(attrs={'size': 50}))
        return super().formfield_for_dbfield(db_field, **kwargs)
