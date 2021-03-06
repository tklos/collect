from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Max
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from .functions import calculate_hash
from . import const


class Device(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='device_set')
    sequence_id = models.IntegerField()
    name = models.CharField(max_length=30)
    columns = JSONField()
    token = models.CharField(max_length=const.DEVICE_TOKEN_LEN)
    salt = models.CharField(max_length=const.DEVICE_SALT_LEN)
    api_key_hash = models.CharField(max_length=64)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]
        unique_together = (
            ('user', 'sequence_id'),
        )
        ordering = [
            'sequence_id',
        ]

    def get_api_key_display(self):
        return '{}{}'.format(self.token, '*' * (const.DEVICE_API_KEY_LEN - const.DEVICE_TOKEN_LEN))

    @cached_property
    def num_measurements(self):
        try:
            return self.measurement_set__count
        except AttributeError:
            return self.measurement_set.count()

    def get_num_measurements_display(self):
        return self.num_measurements or ''

    def get_time_range_display(self):
        if not self.num_measurements:
            return ''

        qs = self.measurement_set.order_by('date_added')
        first, last = qs[0], qs.reverse()[0]
        return f'{first.date_added:%Y-%m-%d %H:%M:%S} &mdash; {last.date_added:%Y-%m-%d %H:%M:%S}'

    def is_matching_api_key(self, api_key):
        return calculate_hash(api_key, self.salt) == self.api_key_hash

    def save(self, *args, **kwargs):
        if self.pk is None:
            last_seq_id = (
                Device
                .objects
                .filter(user=self.user)
                .aggregate(ret=Coalesce(Max('sequence_id'), 0))
                ['ret']
            )

            self.sequence_id = last_seq_id + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return 'Device {} {}: {}'.format(
            self.user,
            self.sequence_id,
            self.name,
        )

