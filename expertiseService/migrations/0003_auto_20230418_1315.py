# Generated by Django 3.2.18 on 2023-04-18 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expertiseService', '0002_auto_20230417_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertiseservicecontracttarif',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='expertiseservicecontracttarif',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=20),
        ),
    ]
