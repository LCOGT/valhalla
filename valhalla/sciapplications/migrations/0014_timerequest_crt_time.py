# Generated by Django 2.0.2 on 2018-02-21 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sciapplications', '0013_scienceapplication_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='timerequest',
            name='crt_time',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
