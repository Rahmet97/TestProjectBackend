# Generated by Django 3.2.18 on 2023-05-25 10:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_alter_permission_icon'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HistoricalRole',
        ),
    ]