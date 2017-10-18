# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-10 00:40
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userrequests', '0016_auto_20171009_1746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='meananom',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(360.0)], verbose_name='Mean anomaly (deg)'),
        ),
    ]