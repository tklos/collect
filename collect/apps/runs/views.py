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

    def form_valid(self, form):
        device = get_object_or_404(Device.objects, user=self.request.user, sequence_id=self.kwargs['d_sid'])
        name = form.cleaned_data['name']
        # date_from, date_to = form.cleaned_data['date_from'], form.cleaned_data['date_to']

        form.instance.device = device

        ret = super().form_valid(form)

        msg = f'Run "{name}" added.<br/>'
        messages.success(self.request, mark_safe(msg))

        return ret

    @abstractmethod
    def get_context_data(self, **kwargs):
        return super().get_context_data()

    def form_invalid(self, form):
        messages.error(self.request, 'Adding run failed')
        return super().form_invalid(form)
