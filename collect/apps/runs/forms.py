import math
from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Run


class DeviceDatesForm(forms.Form):
    date_from = forms.CharField(max_length=19, required=False)
    date_to = forms.CharField(max_length=19, required=False)

    def __init__(self, id_prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set widget attributes
        text_field_attrs = {
            'class': 'form-control input-sm input-font-size-14 width-input-date-long',
            'autocomplete': 'off',
        }

        self.fields['date_from'].widget.attrs.update(text_field_attrs)
        self.fields['date_from'].widget.attrs['id'] = f'id_{id_prefix}_date_from'
        self.fields['date_from'].widget.attrs['placeholder'] = 'yyyy-mm-dd HH:MM:SS'

        self.fields['date_to'].widget.attrs.update(text_field_attrs)
        self.fields['date_to'].widget.attrs['id'] = f'id_{id_prefix}_date_to'
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


class DeviceDeleteDataForm(DeviceDatesForm):

    def __init__(self, *args, **kwargs):
        super().__init__('delete', *args, **kwargs)

