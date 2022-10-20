import math
from datetime import datetime, timedelta

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

import runs.models


class RunAddForm(forms.ModelForm):
    class Meta:
        model = runs.models.Run
        fields = (
            'name',
            'date_from',
            'date_to',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        text_field_attrs = {
            'class': 'form-control',
            'autocomplete': 'off',
        }
        date_field_attrs = {
            'class': 'form-control width-input-date-long',
            'autocomplete': 'off',
        }

        self.fields['name'].widget.attrs.update(text_field_attrs)

        self.fields['date_from'].widget.attrs.update(date_field_attrs)
        self.fields['date_from'].widget.attrs['placeholder'] = 'yyyy-mm-dd HH:MM:SS'

        self.fields['date_to'].widget.attrs.update(date_field_attrs)
        self.fields['date_to'].widget.attrs['placeholder'] = 'yyyy-mm-dd HH:MM:SS'

    def clean(self):
        super().clean()

        # Check dates
        date_from, date_to = self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        if date_from is not None and date_to is not None:
            if date_to <= date_from:
                self.add_error(None, 'date-to should be later than date-from')
