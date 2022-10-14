from django.db import models

from devices.models import Device


class Run(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='run_set')
    name = models.CharField(max_length=100)
    date_from = models.DateTimeField(null=True, blank=True)
    date_to = models.DateTimeField(null=True, blank=True)

    def get_time_range_display(self):
        if not self.date_from and not self.date_to:
            return ''
        return f'{self.date_from:%Y-%m-%d %H:%M:%S} &mdash; {self.date_to:%Y-%m-%d %H:%M:%S}'

    def __str__(self):
        return 'Run for device {}: "{}": {} \u2014 {}'.format(
            self.device,
            self.name,
            self.date_from,
            self.date_to,
        )

