# Generated by Django 3.2.16 on 2022-10-20 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='date_from',
            field=models.DateTimeField(),
        ),
    ]
