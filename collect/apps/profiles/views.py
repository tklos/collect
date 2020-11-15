from django.contrib.auth import get_user_model
from django.db.models import Count
from django.views.generic import TemplateView

from devices.forms import DeviceAddForm


class ProfileView(TemplateView):
    template_name = 'profiles/home.html'

    def get_context_data(self, **kwargs):
        devices = (
            self.request.user
            .device_set
            .annotate(
                Count('measurement_set'),
            )
        )

        context = super().get_context_data(**kwargs)
        context.update({
            'device_add_form': DeviceAddForm(),
            'devices': devices,
        })

        return context

