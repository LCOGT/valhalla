# Generated by Django 2.0.3 on 2018-03-21 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0014_auto_20180321_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeallocationgroup',
            name='four_meter_alloc',
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='timeallocationgroup',
            name='one_meter_alloc',
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='timeallocationgroup',
            name='two_meter_alloc',
            field=models.PositiveIntegerField(blank=True, default=0),
        ),
    ]
