import math
import string
import random
from datetime import timedelta, timezone, datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, DetailView, FormView

from .models import Device
from .forms import DeviceAddForm, DevicePlotDateForm
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

        msg = f'Device {name} added.<br/>API key: <b><span class="monospace">{api_key}</span></b><br/>Please save it as it is shown only once'
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

        context['plot_date_form'] = DevicePlotDateForm()

        return context


class XticksAndLabelsMixin:
    XTICK_INTERVALS = [
        timedelta(minutes=1), timedelta(minutes=2), timedelta(minutes=5), timedelta(minutes=10), timedelta(minutes=20), timedelta(minutes=30),
        timedelta(hours=1), timedelta(hours=2), timedelta(hours=4), timedelta(hours=6), timedelta(hours=12),
        timedelta(days=1),
    ]
    MAX_NUM_XTICKS = 7

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


class BasicPlotDataMixin:

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise PermissionDenied('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_device(self):
        return get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])


class DevicePlotInitialDataView(BasicPlotDataMixin, XticksAndLabelsMixin, View):
    DEFAULT_NUM_DATA_PTS = 360
    MAX_TIME_RANGE = timedelta(hours=6)
    MAX_UNTIL_NOW_DIFF = timedelta(minutes=2)

    http_method_names = ['get']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        current_time = datetime.now(settings.LOCAL_TIMEZONE)
        self.current_time = current_time
        self.this_minute, self.following_minute = self._get_this_minute(current_time), self._get_following_minute(current_time)

    def get(self, request, *args, **kwargs):
        # Get measurements
        device = self.get_device()
        measurements, is_until_now = self._get_measurements(device)

        # Process measurements
        time_dt, data = [], [[] for _ in range(len(device.columns))]
        for measurement in measurements:
            time_dt.append(measurement.date_added.astimezone(settings.LOCAL_TIMEZONE))
            for idx, value in enumerate(measurement.data):
                data[idx].append(value)

        # Convert to unix timestamp
        time_e = [t.timestamp() for t in time_dt]

        # Calculate xlimits, ticks and labels
        if not time_dt:
            xlim_dt = (self._get_this_minute(self.current_time), self.following_minute)
        else:
            xlim_end_dt = self.following_minute if is_until_now else self._get_following_minute(time_dt[-1])
            xlim_dt = (self._get_this_minute(time_dt[0]), xlim_end_dt)

        xlim_e = tuple(dt.timestamp() for dt in xlim_dt)
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        # Return data
        data = {
            'date_from_s': xlim_dt[0].strftime('%Y-%m-%d %H:%M'),
            'date_to_s': 'now' if is_until_now else xlim_dt[1].strftime('%Y-%m-%d %H:%M'),

            'labels': device.columns,
            'time': time_e,
            'time_fmt': [t.strftime('%Y-%m-%d %H:%M:%S') for t in time_dt],
            'data': data,
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,

            'date_from_interval': None,
            'is_until_now': is_until_now,
            'last_record_time': time_e[-1] if time_e else None,
        }
        return JsonResponse(data)

    def _get_measurements(self, device):
        """
        Returns:
            measurements: list ordered by ascending `date_added`
            is_until_now: True if the most recent record is close to now or if no measurements
        """
        measurements = list(reversed(device.measurement_set.order_by('-date_added')[:self.DEFAULT_NUM_DATA_PTS]))
        if not measurements:
            return measurements, True

        # Check if until now
        diff = self.this_minute - measurements[-1].date_added
        is_until_now = diff <= self.MAX_UNTIL_NOW_DIFF

        min_time = measurements[-1].date_added - self.MAX_TIME_RANGE
        # FIXME use binary search
        first_idx = next(idx for idx, el in enumerate(measurements) if min_time <= el.date_added)
        return measurements[first_idx:], is_until_now

    @staticmethod
    def _get_this_minute(d):
        return d.replace(second=0, microsecond=0)

    @staticmethod
    def _get_following_minute(d):
        following_minute = d.replace(second=0, microsecond=0)
        following_minute += timedelta(minutes=1)
        return following_minute


class DevicePlotDataView(BasicPlotDataMixin, XticksAndLabelsMixin, FormView):
    form_class = DevicePlotDateForm
    template_name = 'devices/device_plot_form_date.html'
    success_url = 'invalid_ajax_doesnt_exist.html'

    http_method_names = ['post']

    def form_valid(self, form):
        super().form_valid(form)

        xlim_dt = (form.cleaned_data['date_from'], form.cleaned_data['date_to'])

        # Get measurements
        device = self.get_device()
        measurements = self._get_measurements(device, xlim_dt)

        # Process measurements
        time_dt, data = [], [[] for _ in range(len(device.columns))]
        for measurement in measurements:
            time_dt.append(measurement.date_added.astimezone(settings.LOCAL_TIMEZONE))
            for idx, value in enumerate(measurement.data):
                data[idx].append(value)

        # Convert to unix timestamp
        time_e = [t.timestamp() for t in time_dt]

        # Calculate xlimits, ticks and labels
        xlim_e = tuple(dt.timestamp() for dt in xlim_dt)
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        if not xticks_e:
            form.add_error(None, f'Time interval too long; max allowed ~{self.MAX_NUM_XTICKS} days')
            return self.form_invalid(form)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        # Return data
        data = {
            'time': time_e,
            'time_fmt': [t.strftime('%Y-%m-%d %H:%M:%S') for t in time_dt],
            'data': data,
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,

            'date_from_interval': form.date_from_interval,
            'is_until_now': form.date_to_is_now,
            'last_record_time': time_e[-1] if time_e else None,
        }
        return JsonResponse(data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['device'] = self.get_device()
        return context

    def form_invalid(self, form):
        response = super().form_invalid(form)
        data = {
            'form_html': response.rendered_content,
        }
        return JsonResponse(data, status=400)

    @classmethod
    def _get_measurements(cls, device, xlim_dt):
        measurements = (
            device
            .measurement_set
            .filter(date_added__gte=xlim_dt[0])
            .filter(date_added__lt=xlim_dt[1])
            .order_by('-date_added')
        )
        measurements = list(reversed(measurements))

        return measurements


class DeviceNewestPlotDataView(BasicPlotDataMixin, XticksAndLabelsMixin, View):
    http_method_names = ['get']

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        ## Process request parameters
        current_time = datetime.now(settings.LOCAL_TIMEZONE)
        xlim_dt = [datetime.fromtimestamp(float(t), settings.LOCAL_TIMEZONE) for t in request.GET.getlist('xlimits[]')]
        xlim_dt[1] = current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

        date_from_interval = request.GET['date_from_interval']
        if date_from_interval:
            xlim_dt[0] = xlim_dt[1] - timedelta(hours=float(date_from_interval)) - timedelta(minutes=1)

        last_record_time = request.GET['last_record_time']
        if last_record_time:
            date_after_dt = max(xlim_dt[0], datetime.fromtimestamp(float(last_record_time), settings.LOCAL_TIMEZONE))
        else:
            date_after_dt = xlim_dt[0]

        # Get data
        device = self.get_device()
        measurements = self._get_measurements(device, date_after_dt)

        # Process measurements
        time_dt, data = [], [[] for _ in range(len(device.columns))]
        for measurement in measurements:
            time_dt.append(measurement.date_added.astimezone(settings.LOCAL_TIMEZONE))
            for idx, value in enumerate(measurement.data):
                data[idx].append(value)

        # Convert to unix timestamp
        time_e = [t.timestamp() for t in time_dt]

        # Calculate xlimits, ticks and labels
        xlim_e = tuple(dt.timestamp() for dt in xlim_dt)
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        # Return data
        data = {
            'time': time_e,
            'time_fmt': [t.strftime('%Y-%m-%d %H:%M:%S') for t in time_dt],
            'data': data,
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,

            'last_record_time': time_e[-1] if time_e else None,
        }
        return JsonResponse(data)

    @classmethod
    def _get_measurements(cls, device, date_after):
        measurements = device.measurement_set
        if date_after:
            measurements = measurements.filter(date_added__gt=date_after)
        measurements = measurements.order_by('-date_added')
        measurements = list(reversed(measurements))

        return measurements


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

