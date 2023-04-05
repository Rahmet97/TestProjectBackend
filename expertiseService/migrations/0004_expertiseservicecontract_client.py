# Generated by Django 3.2.18 on 2023-04-03 13:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('expertiseService', '0003_expertiseservicecontract_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='expertiseservicecontract',
            name='client',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='accounts.userdata'),
            preserve_default=False,
        ),
    ]