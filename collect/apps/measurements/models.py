from django.contrib.postgres.fields import JSONField
from django.db import models

from devices.models import Device


class Measurement(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='measurement_set')
    date_added = models.DateTimeField(auto_now_add=True)
    data = JSONField()

    class Meta:
        indexes = [
            models.Index(fields=['device', 'date_added']),
        ]

    def __str__(self):
        return 'Measurement for device {}: {} {}'.format(
            self.device,
            self.date_added,
            self.data,
        )

