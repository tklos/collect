import csv
import math
import string
import random
from abc import ABC, abstractmethod
from datetime import timedelta, timezone, datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, DetailView, FormView

import runs.views

from .models import Device
from .forms import RunAddForm
# from .forms import DeviceAddForm, DeviceDownloadForm, DevicePlotDateForm, DeviceDeleteDataForm
from .functions import calculate_hash
from . import const


def get_runs_context_data(device):
    runs = device.run_set.order_by('-date_from').all()

    return {
        'runs': runs,
        'run_add_form': RunAddForm(),
    }


def get_unassigned_measurements_context_data(device, page):
    measurements = device.unassgned_measurements.order_by('-date_added').all()

    measurements_paginator = Paginator(measurements, settings.MEASUREMENTS_PAGINATE_BY)
    measurements_page = measurements_paginator.get_page(page)

    return {
        'measurements_page': measurements_page,
        'measurements_extra': {
            'd_sid': device.sequence_id
        },
    }


class DeviceView(DetailView):
    template_name = 'devices/device.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        r_context = get_runs_context_data(self.object)
        m_context = get_unassigned_measurements_context_data(self.object, 1)

        context.update(**r_context, **m_context)

        return context


class PaginationUnassignedMeasurementsView(TemplateView):
    template_name = 'devices/device_unassigned_measurements.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise RuntimeError('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, d_sid, page, **kwargs):
        device = get_object_or_404(Device.objects, user=self.request.user, sequence_id=d_sid)

        context = super().get_context_data(**kwargs)
        context['device'] = device

        m_context = get_unassigned_measurements_context_data(device, page)
        context.update(m_context)

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        data = {
            'html': response.rendered_content,
        }
        return JsonResponse(data)


class DeviceAddView(ABC, CreateView):
    # form_class =
    # template_name =
    # success_url =

    API_KEY_CHARS = string.ascii_letters + string.digits

    def form_valid(self, form):
        user = self.request.user
        name = form.cleaned_data['name']
        columns = form.cleaned_data['columns']

        # Create API key
        api_key = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_API_KEY_LEN))
        token = api_key[:const.DEVICE_TOKEN_LEN]
        salt = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_SALT_LEN))
        api_key_hash = calculate_hash(api_key, salt)

        form.instance.user = user
        form.instance.columns = columns
        form.instance.token = token
        form.instance.salt = salt
        form.instance.api_key_hash = api_key_hash

        ret = super().form_valid(form)

        msg = f'Device {name} added.<br/>API key: <b><span class="monospace">{api_key}</span></b><br/>Please save it as it is shown only once'
        messages.success(self.request, mark_safe(msg))

        return ret

    @abstractmethod
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def form_invalid(self, form):
        messages.error(self.request, 'Adding device failed')
        return super().form_invalid(form)


class RunAddView(runs.views.RunAddView):
    form_class = RunAddForm
    template_name = 'devices/device.html'

    def get_success_url(self):
        return reverse_lazy('devices:device', kwargs={'d_sid': self.kwargs['d_sid']})

    def get_context_data(self, **kwargs):
        device = get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])

        context = super().get_context_data(**kwargs)
        context['object'] = device
        context['run_add_form'] = context.pop('form')

        r_context = get_runs_context_data(device)
        r_context.pop('run_add_form')
        m_context = get_unassigned_measurements_context_data(device, 1)

        context.update(**r_context, **m_context)

        return context
