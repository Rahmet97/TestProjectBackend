# Generated by Django 3.2.16 on 2023-02-22 05:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0004_contract_id_code'),
        ('one_c', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nomenclature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nomenclature', models.CharField(max_length=25)),
                ('name', models.CharField(max_length=30)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contracts.service')),
            ],
        ),
    ]