# Generated by Django 2.0.3 on 2018-03-21 16:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sciapplications', '0018_auto_20180319_2126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='proposal_type',
            field=models.CharField(choices=[('SCI', 'Science'), ('DDT', "Director's Discretionary Time"), ('KEY', 'Key Project'), ('NAOC', 'NAOC proposal'), ('COLAB', 'Science Collaboration Proposal')], max_length=5),
        ),
    ]
