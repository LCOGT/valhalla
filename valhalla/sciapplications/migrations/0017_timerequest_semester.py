# Generated by Django 2.0.2 on 2018-03-13 23:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0012_proposal_non_science'),
        ('sciapplications', '0016_remove_scienceapplication_moon'),
    ]

    operations = [
        migrations.AddField(
            model_name='timerequest',
            name='semester',
            field=models.ForeignKey(default='2018A', on_delete=django.db.models.deletion.CASCADE, to='proposals.Semester'),
            preserve_default=False,
        ),
    ]
