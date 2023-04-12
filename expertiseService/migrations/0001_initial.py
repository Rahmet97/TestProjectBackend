# Generated by Django 3.2.18 on 2023-04-12 10:36

import contracts.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contracts', '0001_initial'),
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpertiseExpertSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('summary', models.IntegerField(choices=[(1, 'Shartnoma imzolash maqsadga muvofiq'), (0, 'Shartnoma imzolash maqsadga muvofiq emas')])),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExpertiseServiceContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(choices=[(1, 'Bajarildi'), (2, 'Jarayonda'), (3, "Ko'rib chiqilmoqda"), (4, 'Yangi')], default=4)),
                ('contract_status', models.IntegerField(choices=[(0, 'Yaratilgan'), (1, 'Rad etilgan'), (2, 'Yakunlangan'), (3, 'Aktiv'), (4, "To'lov kutilmoqda"), (5, 'Bekor qilingan'), (6, 'Yangi')], default=0)),
                ('price_select_percentage', models.IntegerField(blank=True, choices=[(50, 50), (100, 100)], null=True)),
                ('contract_number', models.CharField(max_length=10, unique=True)),
                ('id_code', models.CharField(blank=True, max_length=20, null=True)),
                ('contract_cash', models.DecimalField(decimal_places=2, max_digits=20)),
                ('payed_cash', models.DecimalField(decimal_places=2, max_digits=20)),
                ('contract_date', models.DateTimeField(blank=True)),
                ('expiration_date', models.DateTimeField(blank=True, null=True)),
                ('base64file', models.TextField(blank=True, null=True)),
                ('hashcode', models.CharField(blank=True, max_length=255, null=True)),
                ('like_preview_pdf', models.FileField(blank=True, null=True, upload_to='media/Contract/pdf/')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contracts.service')),
            ],
        ),
        migrations.CreateModel(
            name='ExpertiseServiceContractTarif',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_of_tarif', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('name_of_tarif', models.CharField(max_length=255)),
                ('is_discount', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ExpertiseTarifContract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseservicecontract')),
                ('tarif', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseservicecontracttarif')),
            ],
        ),
        migrations.CreateModel(
            name='ExpertisePkcs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pkcs7', models.TextField()),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseservicecontract')),
            ],
        ),
        migrations.CreateModel(
            name='ExpertiseExpertSummaryDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(blank=True, null=True, upload_to=contracts.models.slugify_upload)),
                ('client_visible', models.BooleanField(default=False)),
                ('expertsummary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseexpertsummary')),
            ],
        ),
        migrations.AddField(
            model_name='expertiseexpertsummary',
            name='contract',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseservicecontract'),
        ),
        migrations.AddField(
            model_name='expertiseexpertsummary',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='expertiseexpertsummary',
            name='user_role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.role'),
        ),
        migrations.CreateModel(
            name='ExpertiseContracts_Participants',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_status', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contracts.agreementstatus')),
                ('contract', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expertiseService.expertiseservicecontract')),
                ('participant_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participant_user', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.role')),
            ],
        ),
    ]
