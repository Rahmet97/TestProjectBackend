# Generated by Django 3.2.16 on 2023-02-24 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0006_usercontracttarifdevice_total_electricity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='contract_number',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]