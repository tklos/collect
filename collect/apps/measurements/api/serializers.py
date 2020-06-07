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
        obj = Measurement.objects.create(
            device=self.context['device'],
            data=validated_data['data'],
        )
        return obj

