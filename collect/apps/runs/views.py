import csv
import math
import re
from abc import ABC, abstractmethod
from datetime import timedelta, timezone, datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.functions import Now
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import TemplateView, CreateView, DetailView

from devices.models import Device
from .models import Run


EARLIEST_DATE = datetime(2000, 1, 1, tzinfo=settings.LOCAL_TIMEZONE)


def get_measurements_context_data(run, page, measurements=None):
    if measurements is None:
        measurements = (
            run
            .measurement_set
            .order_by('-date_added')
        )

    measurements_paginator = Paginator(measurements, settings.MEASUREMENTS_PAGINATE_BY)
    measurements_page = measurements_paginator.get_page(page)

    start_idx = measurements_paginator.count - measurements_page.start_index() + 1

    return {
        'measurements_page': measurements_page,
        'measurements_l': zip(range(start_idx, start_idx-settings.MEASUREMENTS_PAGINATE_BY, -1), measurements_page),
        'measurements_extra': {
            'r_id': run.pk,
        },
    }


def get_map_context_data(run, queryset=None, start_idx=None):
    lat_idx, lon_idx = run.device.columns.index('lat'), run.device.columns.index('lon')

    if queryset is None:
        queryset = (
            run
            .measurement_set
            .order_by('date_added')
        )
        start_idx = 1

    locations = [
        (idx, m.data[lat_idx], m.data[lon_idx], m.date_added.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'))
        for idx, m in enumerate(queryset, start_idx)
    ]

    return {
        'locations_l': locations,

        'MAPS_API_KEY': settings.MAPS_API_KEY,
    }


class PlotContextData:
    XTICK_INTERVALS = [
        timedelta(minutes=1), timedelta(minutes=2), timedelta(minutes=5), timedelta(minutes=10), timedelta(minutes=20), timedelta(minutes=30),
        timedelta(hours=1), timedelta(hours=2), timedelta(hours=4), timedelta(hours=6), timedelta(hours=12),
        timedelta(days=1),
    ]
    MAX_NUM_XTICKS = 7

    def __init__(self, run, *args, **kwargs):
        self.run = run
        super().__init__(*args, **kwargs)

    def get_plot_context_data(self, measurements=None, start_idx=None):
        run = self.run
        device = run.device
        columns = device.columns
        if measurements is None:
            measurements = (
                run
                .measurement_set
                .order_by('date_added')
            )
            start_idx = 1

        # Process measurements
        time_dt, data = [], [[] for _ in range(len(columns))]
        for measurement in measurements:
            time_dt.append(measurement.date_added.astimezone(settings.LOCAL_TIMEZONE))
            for idx, value in enumerate(measurement.data):
                data[idx].append(value)

        # Convert to unix timestamp
        time_e = [t.timestamp() for t in time_dt]

        # Calculate x-axis limits
        xlim_dt = self._calculate_xaxis_limits()

        xlim_e = tuple(dt.timestamp() for dt in xlim_dt)
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        titles = [
            f'''#{start_idx+idx}: {t.strftime('%Y-%m-%d %H:%M:%S')}'''
            for idx, t in enumerate(time_dt)
        ]

        # Return data
        return {
            'labels': columns,
            'time': time_e,
            'titles': titles,
            'data': data,
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,
        }

    def get_plot_xaxis_context_data(self):
        run = self.run

        xlim_dt = self._calculate_xaxis_limits()

        xlim_e = tuple(dt.timestamp() for dt in xlim_dt)
        xticks_e, xticks_dt = self._calculate_xticks(*xlim_dt)
        xticklabels = self._calculate_xticklabels(xticks_dt)

        return {
            'xlimits': xlim_e,
            'xticks': xticks_e,
            'xticklabels': xticklabels,
        }

    def _calculate_xticks(self, begin_dt, end_dt):
        """Calculate x-axis ticks for the limits of [begin_dt, end_dt].

        Parameters:
            begin_dt: aware datetime
            end_dt: aware datetime

        Returns: tuple of list
            xticks_e: list of float
            xticks_dt: list of aware datetime
                in local timezone
        """
        # Local timestamps, but with timezones set to UTC
        begin_dt_utc, end_dt_utc = begin_dt.astimezone(settings.LOCAL_TIMEZONE).replace(tzinfo=timezone.utc), end_dt.astimezone(settings.LOCAL_TIMEZONE).replace(tzinfo=timezone.utc)
        begin_e, end_e = begin_dt_utc.timestamp(), end_dt_utc.timestamp()

        for interval in self.XTICK_INTERVALS:
            interval_s = int(interval.total_seconds())

            min_e, max_e = math.ceil(begin_e / interval_s) * interval_s, math.floor(end_e / interval_s) * interval_s

            num_ticks = (max_e - min_e) // interval_s + 1
            if num_ticks > self.MAX_NUM_XTICKS and interval != self.XTICK_INTERVALS[-1]:
                continue

            xticks_e = [min_e + i * interval_s for i in range(num_ticks)]
            xticks_dt = [settings.LOCAL_TIMEZONE.localize(datetime.utcfromtimestamp(xtick)) for xtick in xticks_e]
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

    def _calculate_xaxis_limits(self):
        run = self.run
        if run.date_to:
            xlim_to = run.date_to
        else:
            current_time = datetime.now(settings.LOCAL_TIMEZONE)
            if current_time < run.date_from:
                xlim_to = run.date_from + timedelta(days=1)
            else:
                xlim_to = self._get_following_minute(current_time)

        return run.date_from, xlim_to

    @staticmethod
    def _get_following_minute(d):
        following_minute = d.replace(second=0, microsecond=0)
        following_minute += timedelta(minutes=1)
        return following_minute


def get_newest_data_context_data(run, last_record_dt):
    last_record_e = last_record_dt.timestamp() if last_record_dt else None

    return {
        'needs_updating': run.needs_updating,
        'url': reverse('runs:get-newest-data', kwargs={'r_id': run.pk}),
        'has_plot': run.device.has_plot,
        'has_map': run.device.has_map,
        'last_record_time': last_record_e,
    }


class RunView(DetailView):
    template_name = 'runs/run.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        measurements = list(
            self.object
            .measurement_set
            .order_by('date_added')
        )
        measurements_rev = list(reversed(measurements))

        context['can_be_trimmed'] = self.object.can_be_trimmed(measurements)
        context['num_measurements'] = len(measurements)

        m_context = get_measurements_context_data(self.object, 1, measurements_rev)

        context.update(**m_context)

        if self.object.device.has_plot:
            plot_data = PlotContextData(self.object).get_plot_context_data(measurements, 1)
            context['plot_data'] = plot_data

        if self.object.device.has_map:
            map_context = get_map_context_data(self.object, measurements, 1)
            context.update(**map_context)

        last_record_dt = m_context['measurements_page'][0].date_added if m_context['measurements_page'] else EARLIEST_DATE
        context['get_newest_data'] = get_newest_data_context_data(self.object, last_record_dt)

        return context


class RunFinaliseView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('runs:run', kwargs=self.kwargs)

    def post(self, *args, **kwargs):
        run = self.object = self.get_object()
        if run.date_to:
            raise RuntimeError('Run already finalised')

        # Detach measurements
        run.date_to = Now()
        run.save()

        # Set end to the next minute
        run.refresh_from_db()
        run.date_to = run.date_to.replace(second=0, microsecond=0) + timedelta(minutes=1)
        run.save()

        messages.success(self.request, f'Run {run.name} finalised')

        return redirect(self.get_success_url())


class RunTrimView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('runs:run', kwargs=self.kwargs)

    def post(self, *args, **kwargs):
        run = self.object = self.get_object()

        qs = (
            run
            .measurement_set
            .order_by('date_added')
        )
        if not qs:
            raise SuspiciousOperation('No measurements anymore')

        first, last = qs[0], qs.reverse()[0]
        first_dt, last_dt = first.date_added, last.date_added
        first_minute_dt = first_dt.replace(second=0, microsecond=0)
        last_minute_dt = last_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Save
        run.date_from = first_minute_dt
        run.date_to = last_minute_dt
        run.save()

        first_minute_s = first_minute_dt.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M')
        last_minute_s = last_minute_dt.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M')

        messages.success(self.request, f'Run {run.name} trimmed to {first_minute_s} -- {last_minute_s}')

        return redirect(self.get_success_url())


class RunDownloadDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get(self, *args, **kwargs):
        run = self.get_object()
        device = run.device
        qs = (
            run
            .measurement_set
            .order_by('date_added')
        )
        clean_device_name = re.sub('[^\w]', '_', run.device.name)
        clean_run_name = re.sub('[^\w]', '_', run.name)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="data-{clean_device_name}-{clean_run_name}.csv"'

        writer = csv.writer(response)

        # Write header
        writer.writerow(['Date added'] + device.columns)

        # Write data
        for m in qs:
            writer.writerow([m.date_added.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')] + m.data)

        return response


class RunDeleteRunDetachDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('devices:device', kwargs={'d_sid': self.object.device.sequence_id})

    def post(self, *args, **kwargs):
        with transaction.atomic():
            run = self.object = self.get_object()

            # Detach measurements
            num_detached = (
                run
                .measurement_set
                .all()
                .update(run=None)
            )

            # Delete run
            run.delete()

        messages.success(self.request, f'Run {run.name} daleted; its {num_detached} records are now unassigned')

        return redirect(self.get_success_url())


class RunDeleteRunAndDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('devices:device', kwargs={'d_sid': self.object.device.sequence_id})

    def post(self, *args, **kwargs):
        with transaction.atomic():
            run = self.object = self.get_object()

            # Delete measurements
            num_deleted, _ = (
                run
                .measurement_set
                .all()
                .delete()
            )

            # Delete run
            run.delete()

        messages.success(self.request, f'Run {run.name} and its {num_deleted} records deleted')

        return redirect(self.get_success_url())


class RunNewestDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get(self, request, *args, **kwargs):
        run = self.get_object()

        try:
            last_record_e = int(float(request.GET['last_record_time'])) + 1
        except KeyError:
            return JsonResponse({'status': 'error'}, status=500)

        last_record = datetime.fromtimestamp(last_record_e, settings.LOCAL_TIMEZONE)

        # Get all new measurements
        new_measurements = list(
            run
            .measurement_set
            .filter(date_added__gte=last_record)
            .order_by('date_added')
        )

        any_new = bool(len(new_measurements))
        if not any_new:
            data = {
                'any_new': any_new,
            }
            if run.device.has_plot:
                ctx = PlotContextData(run).get_plot_xaxis_context_data()
                data['plot_ctx'] = ctx
            return JsonResponse(data)

        # Process new measurements
        last_record_e = new_measurements[-1].date_added.timestamp()

        m_context = get_measurements_context_data(run, 1)
        m_context['run'] = run
        response = render(request, 'runs/run_measurements.html', m_context)

        num_measurements = run.measurement_set.count()

        data = {
            'any_new': any_new,
            'num_measurements': num_measurements,
            'last_record_time': last_record_e,
            'measurements_table_html': response.content.decode(),
        }

        if run.device.has_map:
            ctx = get_map_context_data(run, queryset=new_measurements, start_idx=num_measurements-len(new_measurements)+1)
            data['map_ctx'] = ctx

        if run.device.has_plot:
            ctx = PlotContextData(run).get_plot_context_data(measurements=new_measurements, start_idx=num_measurements-len(new_measurements)+1)
            data['plot_ctx'] = ctx

        return JsonResponse(data)


class PaginationMeasurementsView(TemplateView):
    template_name = 'runs/run_measurements.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise PermissionDenied('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, r_id, page, **kwargs):
        run = get_object_or_404(Run.objects, device__user=self.request.user, pk=r_id)

        context = super().get_context_data(**kwargs)
        context['run'] = run

        m_context = get_measurements_context_data(run, page)
        context.update(m_context)

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        data = {
            'html': response.rendered_content,
        }
        return JsonResponse(data)


class RunAddView(ABC, CreateView):
    # form_class =
    # template_name =
    # success_url =

    MAX_DATETIME = settings.LOCAL_TIMEZONE.localize(datetime(2100, 1, 1))

    def _check_that_run_doesnt_overlap(self, device, date_from, date_to):
        all_runs = (
            device
            .run_set
            .all()
        )
        self_date_from, self_date_to = date_from, date_to or self.MAX_DATETIME
        for run in all_runs:
            date_from, date_to = run.date_from, run.date_to or self.MAX_DATETIME
            if self_date_from < date_to and date_from < self_date_to:
                return False, run

        return True, None

    @transaction.atomic
    def form_valid(self, form):
        device = get_object_or_404(Device.objects.select_for_update(), user=self.request.user, sequence_id=self.kwargs['d_sid'])
        name = form.cleaned_data['name']
        date_from, date_to = form.cleaned_data['date_from'], form.cleaned_data['date_to']

        ret, overlapping_run = self._check_that_run_doesnt_overlap(device, date_from, date_to)
        if not ret:
            form.add_error(None, f'This run would overlap with run {overlapping_run}')
            return self.form_invalid(form)

        form.instance.device = device

        ret = super().form_valid(form)

        # Move selected measurements to the newly created run
        run = self.object
        qs = device.measurement_set.filter(date_added__gte=date_from)
        if date_to:
            qs = qs.filter(date_added__lt=date_to)
        num_assigned = qs.update(run=run)

        msg = f'Run "{name}" added. {num_assigned} measurements assigned.<br/>'
        messages.success(self.request, mark_safe(msg))

        return ret

    @abstractmethod
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def form_invalid(self, form):
        messages.error(self.request, 'Adding run failed')
        return super().form_invalid(form)
