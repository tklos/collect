import math
import string
import random
from datetime import timedelta, timezone, datetime

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views import View
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
        user = self.request.user
        name = form.cleaned_data['name']
        columns = form.cleaned_data['columns']

        # Check if name is correct
        if Device.objects.filter(user=user, name=name).first() is not None:
            form.add_error('name', 'Device with this name already exists')
            return self.form_invalid(form)

        form.instance.user = user
        form.instance.columns = columns

        # Create API key
        api_key = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_API_KEY_LEN))
        token = api_key[:const.DEVICE_TOKEN_LEN]
        salt = ''.join(random.sample(self.API_KEY_CHARS, k=const.DEVICE_SALT_LEN))
        api_key_hash = calculate_hash(api_key, salt)

        form.instance.token = token
        form.instance.salt = salt
        form.instance.api_key_hash = api_key_hash

        ret = super().form_valid(form)

        msg = f'Device {name} added.<br/>API key: <b>{api_key}</b><br/>Please save it as it is shown only once'
        messages.success(self.request, mark_safe(msg))

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


class DevicePlotDataView(View):
    DEFAULT_NUM_DATA_PTS = 360
    MAX_TIME_RANGE = timedelta(hours=6)

    XTICK_INTERVALS = [
        timedelta(minutes=1), timedelta(minutes=2), timedelta(minutes=5), timedelta(minutes=10), timedelta(minutes=20), timedelta(minutes=30),
        timedelta(hours=1), timedelta(hours=2), timedelta(hours=4), timedelta(hours=6), timedelta(hours=12),
        timedelta(days=1),
    ]
    MAX_NUM_XTICKS = 7

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise RuntimeError('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_device(self):
        return get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])

    def get(self, request, *args, **kwargs):
        device = self.get_device()
        measurements = self._get_measurements(device)

        # Process measurements
        time_dt, data = [], [[] for _ in range(len(device.columns))]
        for measurement in measurements:
            time_dt.append(measurement.date_added.astimezone(settings.LOCAL_TIMEZONE))
            for idx, value in enumerate(measurement.data):
                data[idx].append(value)

        # Convert to unix timestamp
        time_e = [t.timestamp() for t in time_dt]

        # Calculate xlimits, ticks and labels
        xlim_dt = (time_dt[0], time_dt[-1])
        xlim_e = (time_e[0], time_e[-1])
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        # Return data
        data = {
            'labels': device.columns,
            'time': time_e,
            'time_fmt': [t.strftime('%Y-%m-%d %H:%M:%S') for t in time_dt],
            'data': data,
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,
        }
        return JsonResponse(data)

    @classmethod
    def _get_measurements(cls, device):
        measurements = list(reversed(device.measurement_set.order_by('-date_added')[:cls.DEFAULT_NUM_DATA_PTS]))
        if not measurements:
            return measurements

        min_time = measurements[-1].date_added - cls.MAX_TIME_RANGE
        # FIXME use binary search
        first_idx = next(idx for idx, el in enumerate(measurements) if min_time < el.date_added)
        return measurements[first_idx:]

    def _calculate_xticks(self, begin_dt, end_dt):
        begin_dt_utc, end_dt_utc = begin_dt.replace(tzinfo=timezone.utc), end_dt.replace(tzinfo=timezone.utc)
        begin_e, end_e = begin_dt_utc.timestamp(), end_dt_utc.timestamp()

        for interval in self.XTICK_INTERVALS:
            interval_s = int(interval.total_seconds())

            min_e, max_e = math.ceil(begin_e / interval_s) * interval_s, math.floor(end_e / interval_s) * interval_s

            num_ticks = (max_e - min_e) // interval_s + 1
            if num_ticks > self.MAX_NUM_XTICKS:
                continue

            xticks_e = [min_e + i * interval_s for i in range(num_ticks)]
            xticks_dt = [settings.LOCAL_TIMEZONE.localize(datetime.fromtimestamp(xtick)) for xtick in xticks_e]
            xticks_e = [xtick.timestamp() for xtick in xticks_dt]

            return xticks_e, xticks_dt

        return [], []

    @staticmethod
    def _calculate_xticklabels(xticks_dt):
        labels = [xtick.strftime('%H:%M') for xtick in xticks_dt]
        for idx, xtick in enumerate(xticks_dt):
            if idx == 0 or xticks_dt[idx-1].date() != xtick.date():
                labels[idx] = [xtick.strftime('%Y-%m-%d'), xtick.strftime('%H:%M')]

        return labels


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

