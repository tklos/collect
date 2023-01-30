from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Measurement


class MeasurementDeleteView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise PermissionDenied('Ajax request expected')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Measurement.objects, device__user=self.request.user, pk=self.kwargs['m_id'])

    def post(self, *args, **kwargs):
        with transaction.atomic():
            measurement = self.get_object()
            measurement.delete()

        return JsonResponse({'status': 'ok'})
