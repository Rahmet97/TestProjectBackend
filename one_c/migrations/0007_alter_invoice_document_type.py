# Generated by Django 3.2.18 on 2023-02-24 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('one_c', '0006_invoice_document_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='document_type',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]