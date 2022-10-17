# Generated by Django 3.2.16 on 2022-10-15 20:19

import contracts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0002_pkcs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(blank=True, upload_to=contracts.models.slugify_upload),
        ),
    ]