# Generated by Django 2.1.3 on 2018-11-09 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sciapplications', '0022_remove_scienceapplication_submitter_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instrument',
            name='telescope_class',
            field=models.CharField(choices=[('0m4', '0m4'), ('0m8', '0m8'), ('1m0', '1m0'), ('2m0', '2m0')], max_length=20),
        ),
    ]