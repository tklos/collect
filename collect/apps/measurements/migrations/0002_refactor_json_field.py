# Generated by Django 2.2.9 on 2020-06-07 11:02

from django.db import migrations


def remove_data_key(apps, schema_editor):
    Measurement = apps.get_model('measurements', 'Measurement')

    for measurement in Measurement.objects.all():
        measurement.data = measurement.data['data']
        measurement.save()


def reverse_remove_data_key(apps, schema_editor):
    Measurement = apps.get_model('measurements', 'Measurement')

    for measurement in Measurement.objects.all():
        measurement.data = {'data': measurement.data}
        measurement.save()


class Migration(migrations.Migration):

    dependencies = [
        ('measurements', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_data_key, reverse_remove_data_key),
    ]

