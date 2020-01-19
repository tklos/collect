import string
import random

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, CreateView, DetailView

from .models import Device
from .forms import DeviceAddForm
from .functions import calculate_hash
from . import const


class DeviceAddView(CreateView):
    form_class = DeviceAddForm
    template_name = 'profiles/home.html'
    success_url = reverse_lazy('profile:home')

    API_KEY_CHARS = string.ascii_letters + string.digits

    def form_valid(self, form):
        user = form.instance.user = self.request.user
        name = form.cleaned_data['name']

        # Check if name is correct
        if Device.objects.filter(user=user, name=name).first() is not None:
            form.add_error('name', 'Device with this name already exists')
            return self.form_invalid(form)

        # Number of columns
        form.instance.num_columns = 0 if form.instance.columns is None else len(form.instance.columns.split(','))

        # Create API key
        api_key = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_API_KEY_LEN))
        token = api_key[:const.DEVICE_TOKEN_LEN]
        salt = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_SALT_LEN))
        api_key_hash = calculate_hash(api_key, salt)

        form.instance.token = token
        form.instance.salt = salt
        form.instance.api_key_hash = api_key_hash

        ret = super().form_valid(form)

        messages.success(self.request, mark_safe('Device {} added.<br/>API key: <b>{}</b><br/>Please save it as it is shown only once'.format(name, api_key)))

        return ret

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['device_add_form'] = context.pop('form')

        return context

    def form_invalid(self, form):
        messages.error(self.request, 'Adding device failed')
        return super().form_invalid(form)


class DeviceMeasurementsMixin:

    def get_measurements_context(self, device, page):
        measurements = device.measurement_set.order_by('-date_added').all()

        measurements_paginator = Paginator(measurements, settings.MEASUREMENTS_PAGINATE_BY)
        measurements_page = measurements_paginator.get_page(page)

        return {
            'device_columns': [] if device.columns is None else device.columns.split(','),
            'measurements_page': measurements_page,
            'measurements_extra': {
                'd_sid': device.sequence_id
            },
        }


class DeviceView(DeviceMeasurementsMixin, DetailView):
    template_name = 'devices/device.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        m_context = self.get_measurements_context(self.object, 1)
        context.update(m_context)

        return context


class PaginationMeasurementsView(DeviceMeasurementsMixin, TemplateView):
    template_name = 'devices/device_measurements.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise RuntimeError('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, d_sid, page, **kwargs):
        context = super().get_context_data(**kwargs)

        device = Device.objects.get(user=self.request.user, sequence_id=d_sid)
        context['object'] = device

        m_context = self.get_measurements_context(device, page)
        context.update(m_context)

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        data = {
            'html': response.rendered_content,
        }
        return JsonResponse(data)

