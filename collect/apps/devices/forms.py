from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Device


class DeviceAddForm(forms.ModelForm):
    columns = forms.CharField(max_length=200)

    class Meta:
        model = Device
        fields = (
            'name',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        text_field_attrs = {
            'class': 'form-control',
            'autocomplete': 'off',
        }

        self.fields['name'].widget.attrs.update(text_field_attrs)

        self.fields['columns'].widget.attrs.update(text_field_attrs)

    def clean_columns(self):
        columns_s = self.cleaned_data['columns']
        columns = [s.strip() for s in columns_s.split(',')]
        return columns


class DevicePlotDateForm(forms.Form):
    date_from = forms.CharField(max_length=16, initial='(loading..)')
    date_to = forms.CharField(max_length=16, initial='(loading..)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        text_field_attrs = {
            'class': 'form-control input-sm input-font-size-14 width-input-date',
            'autocomplete': 'off',
        }

        self.fields['date_from'].widget.attrs.update(text_field_attrs)
        self.fields['date_from'].widget.attrs['placeholder'] = 'datetime'

        self.fields['date_to'].widget.attrs.update(text_field_attrs)
        self.fields['date_to'].widget.attrs['placeholder'] = 'datetime or "now"'

    def clean_date_from(self):
        s = self.cleaned_data['date_from'].strip()

        try:
            date_from = settings.LOCAL_TIMEZONE.localize(datetime.strptime(s, '%Y-%m-%d %H:%M'))

        except Exception as exc:
            raise ValidationError(f'Can\'t parse date: {exc}')

        return date_from

    def clean_date_to(self):
        s = self.cleaned_data['date_to'].strip()

        try:
            if s == 'now':
                date_to = datetime.now(settings.LOCAL_TIMEZONE).replace(second=0, microsecond=0) + timedelta(minutes=1)
            else:
                date_to = settings.LOCAL_TIMEZONE.localize(datetime.strptime(s, '%Y-%m-%d %H:%M'))

        except Exception as exc:
            raise ValidationError(f'Can\'t parse date: {exc}')

        return date_to

