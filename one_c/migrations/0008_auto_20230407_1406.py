# Generated by Django 3.2.18 on 2023-04-07 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('one_c', '0007_alter_invoice_document_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='payedinformation',
            name='comment',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='company_payment_account',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='contract_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='currency',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='customer_mfo',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='customer_payment_account',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='payedinformation',
            name='customer_tin',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='payedinformation',
            name='invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='one_c.invoice'),
        ),
    ]