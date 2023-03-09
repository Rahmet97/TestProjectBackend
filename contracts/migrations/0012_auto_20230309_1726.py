# Generated by Django 3.2.18 on 2023-03-09 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0011_element_keyword'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tarif',
            name='elements',
        ),
        migrations.AddField(
            model_name='element',
            name='tariff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contracts.tarif'),
        ),
    ]
