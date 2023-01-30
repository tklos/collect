from datetime import datetime, timedelta

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

    def can_be_trimmed(self, measurements=None):
        """Is there any data gap at the beginning or end of the run timerange?

        Parameters:
            measurements: list of Measurement or None

        Returns: bool
        """
        if not self.date_to:
            return False

        if measurements is None:
            qs = self.measurement_set.order_by('date_added')
            if not qs:
                return False
            first, last = qs[0], qs.reverse()[0]
        else:
            if not measurements:
                return False
            first, last = measurements[0], measurements[-1]

        first_dt, last_dt = first.date_added, last.date_added
        first_minute_dt = first_dt.replace(second=0, microsecond=0)
        last_minute_dt = last_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)

        return first_minute_dt != self.date_from or last_minute_dt != self.date_to

    @property
    def needs_updating(self):
        return not self.date_to or datetime.now(settings.LOCAL_TIMEZONE) <= self.date_to

    def __str__(self):
        return 'Run for device {}: "{}": {} \u2014 {}'.format(
            self.device,
            self.name,
            self.get_date_from_display(),
            self.get_date_to_display(),
        )

