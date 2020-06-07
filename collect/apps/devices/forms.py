from django import forms

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

