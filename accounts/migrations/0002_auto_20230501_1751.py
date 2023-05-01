# Generated by Django 3.2.18 on 2023-05-01 12:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_one_time_payment',
            field=models.BooleanField(default=False, verbose_name="bir martalik to'lovmi?"),
        ),
        migrations.AddField(
            model_name='rolepermission',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.group'),
        ),
    ]