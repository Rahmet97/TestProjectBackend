# Generated by Django 3.2.18 on 2023-02-23 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('one_c', '0003_status_status_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='number',
            field=models.CharField(max_length=20),
        ),
    ]
