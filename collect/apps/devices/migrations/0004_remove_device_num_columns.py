# Generated by Django 2.2.9 on 2020-06-07 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0003_make_columns_json'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='num_columns',
        ),
    ]