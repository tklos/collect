# Generated by Django 3.2.16 on 2022-10-11 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_auto_20200729_1644'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='columns',
            field=models.JSONField(),
        ),
    ]
