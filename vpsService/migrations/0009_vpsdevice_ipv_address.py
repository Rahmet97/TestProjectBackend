# Generated by Django 3.2.18 on 2023-06-23 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vpsService', '0008_alter_vpsdevice_storage_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpsdevice',
            name='ipv_address',
            field=models.BooleanField(default=True),
        ),
    ]
