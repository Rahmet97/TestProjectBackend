# Generated by Django 3.2.16 on 2023-01-03 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_auto_20230102_2345'),
    ]

    operations = [
        migrations.AddField(
            model_name='deviceunit',
            name='end',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='deviceunit',
            name='start',
            field=models.IntegerField(default=1),
        ),
    ]
