# Generated by Django 3.2.16 on 2022-12-01 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_auto_20221021_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='yuruser',
            name='ifut',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='yuruser',
            name='ktut',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='yuruser',
            name='xxtut',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
