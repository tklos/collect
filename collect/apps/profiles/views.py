from django.db.models import Count, Q
from django.views.generic import TemplateView

from devices.forms import DeviceAddForm


def get_profile_context_data(user):
    devices = (
        user
        .device_set
        .annotate(
            num_runs=Count('run_set'),
            num_measurements=Count('measurement_set'),
            num_unassigned_measurements=Count('measurement_set', filter=Q(measurement_set__run__isnull=True)),
        )
        .order_by('sequence_id')
    )

    return {
        'device_add_form': DeviceAddForm(),
        'devices': devices,
    }


class ProfileView(TemplateView):
    template_name = 'profiles/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        p_context = get_profile_context_data(self.request.user)

        context.update(**p_context)

        return context
