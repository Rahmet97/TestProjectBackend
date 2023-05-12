# Generated by Django 3.2.18 on 2023-05-11 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_historicalunicondatas'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unicondatas',
            name='document_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='first_name_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='mid_name_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='name_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='per_adr_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='position_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='short_name_uz',
        ),
        migrations.RemoveField(
            model_name='unicondatas',
            name='sur_name_uz',
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='document_en',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='document_ru',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='first_name_en',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='first_name_ru',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='mid_name_en',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='mid_name_ru',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='name_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='name_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='per_adr_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='per_adr_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='position_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='position_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='short_name_en',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='short_name_ru',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='sur_name_en',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='historicalunicondatas',
            name='sur_name_ru',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='document',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='first_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='mid_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='position',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='short_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='historicalunicondatas',
            name='sur_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='document',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='first_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='mid_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='per_adr_en',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='per_adr_ru',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='position',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='short_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='unicondatas',
            name='sur_name',
            field=models.CharField(max_length=50),
        ),
    ]
