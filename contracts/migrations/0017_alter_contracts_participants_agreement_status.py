# Generated by Django 3.2.16 on 2022-11-15 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0016_auto_20221115_1758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contracts_participants',
            name='agreement_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contracts.agreementstatus'),
        ),
    ]