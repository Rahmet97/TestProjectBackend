# Generated by Django 3.2.18 on 2023-07-03 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0025_auto_20230703_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='slug',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
