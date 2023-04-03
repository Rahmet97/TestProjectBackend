# Generated by Django 3.2.18 on 2023-04-03 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0019_auto_20230401_1701'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='connetmethod',
            index=models.Index(fields=['name'], name='contracts_c_name_c0bdf5_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['service', 'contract_number', 'id_code', 'client', 'contract_status', 'tarif'], name='contracts_c_service_1e7bf5_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['contract_date', 'condition', 'hashcode'], name='contracts_c_contrac_d7cc3a_idx'),
        ),
        migrations.AddIndex(
            model_name='contracts_participants',
            index=models.Index(fields=['contract', 'role', 'agreement_status'], name='contracts_c_contrac_bc3329_idx'),
        ),
        migrations.AddIndex(
            model_name='expertsummary',
            index=models.Index(fields=['contract', 'user', 'date'], name='contracts_e_contrac_d88a6a_idx'),
        ),
        migrations.AddIndex(
            model_name='pkcs',
            index=models.Index(fields=['contract', 'pkcs7'], name='contracts_p_contrac_e5d88f_idx'),
        ),
        migrations.AddIndex(
            model_name='service',
            index=models.Index(fields=['name'], name='contracts_s_name_407a7f_idx'),
        ),
    ]
