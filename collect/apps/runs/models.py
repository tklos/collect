from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from devices.models import Device


class Run(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='run_set')
    name = models.CharField(max_length=100)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField(null=True, blank=True)

    def get_date_from_display(self):
        return f'{self.date_from.astimezone(settings.LOCAL_TIMEZONE):%Y-%m-%d %H:%M}'

    def get_date_to_display(self):
        return f'{self.date_to.astimezone(settings.LOCAL_TIMEZONE):%Y-%m-%d %H:%M}' if self.date_to else 'current'

    def get_time_range_display(self):
        if not self.date_from and not self.date_to:
            return ''

        return f'{self.get_date_from_display()} &mdash; {self.get_date_to_display()}'

    @cached_property
    def num_measurements(self):
        return self.measurement_set.count()

    def __str__(self):
        return 'Run for device {}: "{}": {} \u2014 {}'.format(
            self.device,
            self.name,
            self.get_date_from_display(),
            self.get_date_to_display(),
        )

