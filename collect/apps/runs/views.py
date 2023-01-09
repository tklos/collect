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

from devices.models import Device
from .models import Run
# from .forms import DeviceAddForm, DeviceDownloadForm, DevicePlotDateForm, DeviceDeleteDataForm
# from .functions import calculate_hash
# from . import const


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
