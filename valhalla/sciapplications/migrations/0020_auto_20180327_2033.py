# Generated by Django 2.0.3 on 2018-03-27 20:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sciapplications', '0019_auto_20180326_1743'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timerequest',
            options={'ordering': ('semester', 'instrument__display')},
        ),
    ]