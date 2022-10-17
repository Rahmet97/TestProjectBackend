# Generated by Django 3.2.16 on 2022-10-15 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20221016_0202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdata',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.group'),
        ),
        migrations.AlterField(
            model_name='userdata',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.role'),
        ),
        migrations.AlterField(
            model_name='userdata',
            name='type',
            field=models.IntegerField(choices=[(1, 'Fizik'), (2, 'Yuridik')], null=True),
        ),
    ]