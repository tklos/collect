from django.db import models
from django.db.models import JSONField

from devices.models import Device
from runs.models import Run


class Measurement(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='measurement_set')
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='measurement_set', null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    data = JSONField()

    class Meta:
        indexes = [
            models.Index(fields=['device', 'date_added']),
        ]

    def __str__(self):
        return 'Measurement for device {}, run "{}": {} {}'.format(
            self.device,
            self.run,
            self.date_added,
            self.data,
        )

