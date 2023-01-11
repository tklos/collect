import csv
import math
import re
import string
import random
from abc import ABC, abstractmethod
from datetime import timedelta, timezone, datetime

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.functions import Now
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, DetailView, FormView

from devices.models import Device
from .models import Run
# from .forms import DeviceDownloadForm
# from .forms import DeviceAddForm, DeviceDownloadForm, DevicePlotDateForm, DeviceDeleteDataForm
# from .functions import calculate_hash
# from . import const


def get_measurements_context_data(run, page):
    measurements = run.measurement_set.order_by('-date_added').all()

    measurements_paginator = Paginator(measurements, settings.MEASUREMENTS_PAGINATE_BY)
    measurements_page = measurements_paginator.get_page(page)

    return {
        'measurements_page': measurements_page,
        'measurements_extra': {
            'r_id': run.pk,
        },
    }


def get_map_context_data(run):
    lat_idx, lon_idx = run.device.columns.index('lat'), run.device.columns.index('lon')

    locations = [
        (idx, m.data[lat_idx], m.data[lon_idx], m.date_added.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'))
        for idx, m in enumerate(run.measurement_set.order_by('date_added').all(), 1)
    ]

    return {
        'locations_l': locations,

        'MAPS_API_KEY': settings.MAPS_API_KEY,
    }


class RunView(DetailView):
    template_name = 'runs/run.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        m_context = get_measurements_context_data(self.object, 1)

        context.update(**m_context)

        if self.object.device.has_map:
            map_context = get_map_context_data(self.object)
            context.update(**map_context)

        return context


class RunFinaliseView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('runs:run', kwargs=self.kwargs)

    def post(self, request, *args, **kwargs):
        run = self.object = self.get_object()
        if run.date_to:
            raise RuntimeError('Run already finalised')

        # Detach measurements
        run.date_to = Now()
        run.save()

        # Remove microseconds
        run.refresh_from_db()
        run.date_to = run.date_to.replace(microsecond=0)
        run.save()

        messages.success(self.request, f'Run {run.name} finalised')

        return redirect(self.get_success_url())


class RunDownloadDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def post(self, request, *args, **kwargs):
        run = self.get_object()
        device = run.device
        clean_device_name = re.sub('[^\w]', '_', run.device.name)
        clean_run_name = re.sub('[^\w]', '_', run.name)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="data-{clean_device_name}-{clean_run_name}.csv"'

        writer = csv.writer(response)

        # Write header
        writer.writerow(['Date added'] + device.columns)

        # Write data
        for m in run.measurement_set.order_by('date_added'):
            writer.writerow([m.date_added.astimezone(settings.LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')] + m.data)

        return response


class RunDeleteRunDetachDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('devices:device', kwargs={'d_sid': self.object.device.sequence_id})

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            run = self.object = self.get_object()

            # Detach measurements
            num_detached = run.measurement_set.all().update(run=None)

            # Delete run
            run.delete()

        messages.success(self.request, f'Run {run.name} daleted; its {num_detached} records are now unassigned')

        return redirect(self.get_success_url())


class RunDeleteRunAndDataView(View):

    def get_object(self):
        return get_object_or_404(Run.objects, device__user=self.request.user, pk=self.kwargs['r_id'])

    def get_success_url(self):
        return reverse_lazy('devices:device', kwargs={'d_sid': self.object.device.sequence_id})

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            run = self.object = self.get_object()

            # Delete measurements
            num_deleted, _ = run.measurement_set.all().delete()

            # Delete run
            run.delete()

        messages.success(self.request, f'Run {run.name} and its {num_deleted} records deleted')

        return redirect(self.get_success_url())


class PaginationMeasurementsView(TemplateView):
    template_name = 'runs/run_measurements.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise RuntimeError('Ajax request expected')
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
        all_runs = device.run_set.all()
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
            qs = qs.filter(date_added__lt=date_to+timedelta(seconds=1))
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
