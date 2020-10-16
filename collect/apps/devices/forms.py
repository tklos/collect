import math
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
        if not all(columns):
            raise ValidationError('Column name can\'t be empty')

        return columns


class DeviceDownloadForm(forms.Form):
    date_from = forms.CharField(max_length=19, required=False)
    date_to = forms.CharField(max_length=19, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set widget attributes
        text_field_attrs = {
            'class': 'form-control input-sm input-font-size-14 width-input-date-long',
            'autocomplete': 'off',
        }

        self.fields['date_from'].widget.attrs.update(text_field_attrs)
        self.fields['date_from'].widget.attrs['placeholder'] = 'yyyy-mm-dd HH:MM:SS'

        self.fields['date_to'].widget.attrs.update(text_field_attrs)
        self.fields['date_to'].widget.attrs['placeholder'] = 'yyyy-mm-dd HH:MM:SS'

    @staticmethod
    def _clean_date(s):
        try:
            return settings.LOCAL_TIMEZONE.localize(datetime.strptime(s, '%Y-%m-%d %H:%M:%S'))
        except Exception as exc:
            raise ValidationError(f'Can\'t parse date: {exc}')

    def clean_date_from(self):
        s = self.cleaned_data['date_from'].strip()
        return self._clean_date(s) if s else None

    def clean_date_to(self):
        s = self.cleaned_data['date_to'].strip()
        return self._clean_date(s) if s else None

    def clean(self):
        super().clean()

        # Check dates
        date_from, date_to = self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        if date_from is not None and date_to is not None:
            if date_to <= date_from:
                self.add_error(None, 'date-to should be later than date-from')


class DevicePlotDateForm(forms.Form):
    date_from = forms.CharField(max_length=16, initial='(loading..)')
    date_to = forms.CharField(max_length=16, initial='(loading..)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Current time
        self.current_time = datetime.now(settings.LOCAL_TIMEZONE)
        self.date_from_interval = None
        self.date_to_is_now = False

        # Set widget attributes
        text_field_attrs = {
            'class': 'form-control input-sm input-font-size-14 width-input-date',
            'autocomplete': 'off',
        }

        self.fields['date_from'].widget.attrs.update(text_field_attrs)
        self.fields['date_from'].widget.attrs['placeholder'] = 'datetime or offset'

        self.fields['date_to'].widget.attrs.update(text_field_attrs)
        self.fields['date_to'].widget.attrs['placeholder'] = 'datetime or "now"'

    def clean_date_from(self):
        """
        Returns timedelta if date_from is an offset, datetime otherwise
        """
        s = self.cleaned_data['date_from'].strip()

        prefix = '-'
        try:
            if s.startswith(prefix):
                if s.endswith('days'):
                    offset_h = 24. * float(s[len(prefix):-len('days')])
                elif s.endswith('hours'):
                    offset_h = float(s[len(prefix):-len('hours')])
                else:
                    raise RuntimeError('Can\'t read interval')

                # Make interval a multiple number of whole minutes
                offset_h = math.ceil(offset_h * 60) / 60

                self.date_from_interval = offset_h
                date_from = timedelta(hours=offset_h)

            else:
                date_from = settings.LOCAL_TIMEZONE.localize(datetime.strptime(s, '%Y-%m-%d %H:%M'))

        except Exception as exc:
            raise ValidationError(f'Can\'t parse date: {exc}')

        return date_from

    def clean_date_to(self):
        s = self.cleaned_data['date_to'].strip()

        try:
            if s == 'now':
                date_to = self.current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
                self.date_to_is_now = True
            else:
                date_to = settings.LOCAL_TIMEZONE.localize(datetime.strptime(s, '%Y-%m-%d %H:%M'))

        except Exception as exc:
            raise ValidationError(f'Can\'t parse date: {exc}')

        return date_to

    def clean(self):
        super().clean()

        # Check dates
        date_from, date_to = self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        if date_from is not None and date_to is not None:
            if isinstance(date_from, timedelta):
                try:
                    date_from = date_to - date_from
                except Exception as exc:
                    raise ValidationError(f'Can\'t create date-from: {exc}')

                if self.date_to_is_now:
                    date_from -= timedelta(minutes=1)

            if date_to <= date_from:
                self.add_error(None, 'date-to should be later than date-from')

            self.cleaned_data['date_from'] = date_from

