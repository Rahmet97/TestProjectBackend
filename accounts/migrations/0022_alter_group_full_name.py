# Generated by Django 3.2.18 on 2023-05-31 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_alter_role_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='full_name',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]