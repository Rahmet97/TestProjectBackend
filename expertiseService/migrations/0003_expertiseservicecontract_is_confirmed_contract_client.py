# Generated by Django 3.2.18 on 2023-05-16 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expertiseService', '0002_alter_expertiseservicecontract_id_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertiseservicecontract',
            name='is_confirmed_contract_client',
            field=models.BooleanField(default=False),
        ),
    ]