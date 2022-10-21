# Generated by Django 3.2.16 on 2022-10-21 06:51

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_auto_20221020_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='active_icon',
            field=models.ImageField(blank=True, null=True, upload_to=accounts.models.slugify_upload),
        ),
        migrations.AddField(
            model_name='group',
            name='inactive_icon',
            field=models.ImageField(blank=True, null=True, upload_to=accounts.models.slugify_upload),
        ),
    ]