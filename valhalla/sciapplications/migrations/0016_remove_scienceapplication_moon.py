# Generated by Django 2.0.2 on 2018-02-27 21:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sciapplications', '0015_auto_20180221_1953'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scienceapplication',
            name='moon',
        ),
    ]
