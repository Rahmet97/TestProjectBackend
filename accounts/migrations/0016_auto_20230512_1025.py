# Generated by Django 3.2.18 on 2023-05-12 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_auto_20230511_1706'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='document',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='document',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
