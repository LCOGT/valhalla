# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-19 21:07
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('proposals', '0002_auto_20161010_2125'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together=set([('user', 'proposal')]),
        ),
    ]
