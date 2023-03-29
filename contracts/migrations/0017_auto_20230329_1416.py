# Generated by Django 3.2.18 on 2023-03-29 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0016_auto_20230328_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='contract_cash',
            field=models.DecimalField(decimal_places=2, max_digits=20),
        ),
        migrations.AlterField(
            model_name='contract',
            name='payed_cash',
            field=models.DecimalField(decimal_places=2, max_digits=20),
        ),
    ]
