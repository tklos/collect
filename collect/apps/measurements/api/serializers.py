from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from measurements.models import Measurement


class MeasurementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Measurement
        fields = (
            'data',
        )

    def validate_data(self, value):
        device = self.context['device']
        if len(value) != len(device.columns):
            raise serializers.ValidationError('Expected {} columns; got {}'.format(len(device.columns), len(value)))
        return value

    def create(self, validated_data):
        device = self.context['device']

        # Save measurement
        with transaction.atomic():
            obj = Measurement.objects.create(
                device=device,
                run=None,
                data=validated_data['data'],
            )

            # Set run that this measurement belongs to (might not exist)
            run = device.run_set.filter(
                Q(date_from__lte=obj.date_added) & (
                    Q(date_to=None) | Q(date_to__gt=obj.date_added)
                )
            ).first()
            if run:
                obj.run = run
                obj.save()

        return obj

