# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-09 17:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0004_auto_20170224_1831'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='public',
            field=models.BooleanField(default=False),
        ),
    ]
