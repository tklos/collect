# Generated by Django 2.2.9 on 2020-01-19 12:00

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='measurement_set', to='devices.Device')),
            ],
        ),
        migrations.AddIndex(
            model_name='measurement',
            index=models.Index(fields=['device', 'date_added'], name='measurement_device__76a5d7_idx'),
        ),
    ]
