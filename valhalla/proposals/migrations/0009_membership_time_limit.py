# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-27 22:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0008_timeallocation_instrument_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='time_limit',
            field=models.IntegerField(default=-1),
        ),
    ]
