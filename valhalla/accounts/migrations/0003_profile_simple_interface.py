# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 05:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_notifications_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='simple_interface',
            field=models.BooleanField(default=False),
        ),
    ]
