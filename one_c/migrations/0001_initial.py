# Generated by Django 3.2.18 on 2023-04-11 14:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contracts', '0021_alter_contract_id_code'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=20)),
                ('date', models.DateTimeField(auto_now=True)),
                ('contract_code', models.CharField(blank=True, max_length=20, null=True)),
                ('document_type', models.CharField(blank=True, max_length=10, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Invoice',
                'verbose_name_plural': 'Invoices',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10)),
                ('status_code', models.IntegerField(default=1)),
            ],
            options={
                'verbose_name': 'Status',
                'verbose_name_plural': 'Statuses',
            },
        ),
        migrations.CreateModel(
            name='PayedInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payed_cash', models.FloatField()),
                ('payed_time', models.DateTimeField()),
                ('contract_code', models.CharField(blank=True, max_length=20, null=True)),
                ('customer_tin', models.IntegerField(blank=True, null=True)),
                ('currency', models.CharField(blank=True, max_length=10, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('customer_payment_account', models.CharField(blank=True, max_length=30, null=True)),
                ('customer_mfo', models.IntegerField(blank=True, null=True)),
                ('company_payment_account', models.CharField(blank=True, max_length=30, null=True)),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='one_c.invoice')),
            ],
        ),
        migrations.CreateModel(
            name='Nomenclature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nomenclature', models.CharField(max_length=25)),
                ('name', models.CharField(max_length=30)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contracts.service')),
            ],
        ),
        migrations.AddField(
            model_name='invoice',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='one_c.status'),
        ),
    ]
