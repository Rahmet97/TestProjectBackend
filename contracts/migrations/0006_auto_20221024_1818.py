# Generated by Django 3.2.16 on 2022-10-24 13:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0005_auto_20221016_0625'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgreementStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RenameModel(
            old_name='ContractType',
            new_name='ContractStatus',
        ),
        migrations.RenameField(
            model_name='contract',
            old_name='contract_type',
            new_name='contract_status',
        ),
        migrations.AddField(
            model_name='contract',
            name='agreement_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='contracts.agreementstatus'),
            preserve_default=False,
        ),
    ]
