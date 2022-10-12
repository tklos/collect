from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.views.generic import TemplateView

from devices.forms import DeviceAddForm


class ProfileView(TemplateView):
    template_name = 'profiles/home.html'

    def get_context_data(self, **kwargs):
        devices = (
            self.request.user
            .device_set
            .annotate(
                num_runs=Count('run_set'),
                num_measurements=Count('measurement_set'),
                num_unassigned_measurements=Count('measurement_set', filter=Q(measurement_set__run__isnull=True)),
            )
            .order_by('sequence_id')
        )

        context = super().get_context_data(**kwargs)
        context.update({
            'device_add_form': DeviceAddForm(),
            'devices': devices,
        })

        return context

