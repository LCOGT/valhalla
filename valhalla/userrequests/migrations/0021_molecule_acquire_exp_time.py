# Generated by Django 2.1.3 on 2019-03-14 20:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userrequests', '0020_auto_20180827_2256'),
    ]

    operations = [
        migrations.AddField(
            model_name='molecule',
            name='acquire_exp_time',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(60.0)]),
        ),
    ]