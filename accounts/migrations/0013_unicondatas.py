# Generated by Django 3.2.18 on 2023-05-11 11:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_historicalrole'),
    ]

    operations = [
        migrations.CreateModel(
            name='UniconDatas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('name_uz', models.CharField(blank=True, max_length=255, null=True)),
                ('name_en', models.CharField(blank=True, max_length=255, null=True)),
                ('name_ru', models.CharField(blank=True, max_length=255, null=True)),
                ('short_name', models.CharField(blank=True, max_length=100, null=True)),
                ('short_name_uz', models.CharField(blank=True, max_length=100, null=True)),
                ('short_name_en', models.CharField(blank=True, max_length=100, null=True)),
                ('short_name_ru', models.CharField(blank=True, max_length=100, null=True)),
                ('position', models.CharField(blank=True, max_length=255, null=True)),
                ('position_uz', models.CharField(blank=True, max_length=255, null=True)),
                ('position_en', models.CharField(blank=True, max_length=255, null=True)),
                ('position_ru', models.CharField(blank=True, max_length=255, null=True)),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('first_name_uz', models.CharField(blank=True, max_length=50, null=True)),
                ('first_name_en', models.CharField(blank=True, max_length=50, null=True)),
                ('first_name_ru', models.CharField(blank=True, max_length=50, null=True)),
                ('mid_name', models.CharField(blank=True, max_length=50, null=True)),
                ('mid_name_uz', models.CharField(blank=True, max_length=50, null=True)),
                ('mid_name_en', models.CharField(blank=True, max_length=50, null=True)),
                ('mid_name_ru', models.CharField(blank=True, max_length=50, null=True)),
                ('sur_name', models.CharField(blank=True, max_length=50, null=True)),
                ('sur_name_uz', models.CharField(blank=True, max_length=50, null=True)),
                ('sur_name_en', models.CharField(blank=True, max_length=50, null=True)),
                ('sur_name_ru', models.CharField(blank=True, max_length=50, null=True)),
                ('document', models.CharField(blank=True, max_length=50, null=True)),
                ('document_uz', models.CharField(blank=True, max_length=50, null=True)),
                ('document_en', models.CharField(blank=True, max_length=50, null=True)),
                ('document_ru', models.CharField(blank=True, max_length=50, null=True)),
                ('per_adr', models.CharField(max_length=255)),
                ('per_adr_uz', models.CharField(max_length=255, null=True)),
                ('per_adr_en', models.CharField(max_length=255, null=True)),
                ('per_adr_ru', models.CharField(max_length=255, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=50, null=True)),
                ('fax', models.CharField(blank=True, max_length=50, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('e_xat', models.EmailField(blank=True, max_length=254, null=True)),
                ('postCode', models.CharField(blank=True, max_length=20, null=True)),
                ('tin', models.CharField(blank=True, max_length=9, null=True)),
                ('paymentAccount', models.CharField(blank=True, max_length=24, null=True)),
                ('xxtut', models.CharField(blank=True, max_length=20, null=True)),
                ('ktut', models.CharField(blank=True, max_length=20, null=True)),
                ('oked', models.CharField(blank=True, max_length=5, null=True)),
                ('web_site', models.URLField(blank=True, null=True)),
                ('dm_web_site', models.URLField(blank=True, null=True)),
                ('dm_phone_number', models.CharField(blank=True, max_length=50, null=True)),
                ('bank_mfo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.bankmfoname')),
            ],
        ),
    ]