# Generated by Django 3.2.16 on 2022-11-16 07:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0017_alter_contracts_participants_agreement_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='agreement_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='contracts.agreementstatus'),
            preserve_default=False,
        ),
    ]