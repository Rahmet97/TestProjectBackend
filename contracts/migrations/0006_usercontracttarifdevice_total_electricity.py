# Generated by Django 3.2.18 on 2023-02-21 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0005_oldcontractfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercontracttarifdevice',
            name='total_electricity',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
