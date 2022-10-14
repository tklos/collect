from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import View

from .models import Measurement


class MeasurementDeleteView(View):
    def get_measurement(self, user, m_id):
        return get_object_or_404(Measurement.objects, device__user=user, id=m_id)

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            measurement = self.get_measurement(self.request.user, self.kwargs['m_id'])
            measurement.delete()

        return JsonResponse({'status': 'ok'})
