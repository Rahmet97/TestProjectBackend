# Generated by Django 3.2.18 on 2023-05-26 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_alter_role_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(choices=[('admin', 'admin'), ("departament boshlig'i", "departament boshlig'i"), ("bo'lim boshlig'i", "bo'lim boshlig'i"), ("direktor o'rinbosari", "direktor o'rinbosari"), ('direktor', 'direktor'), ('buxgalteriya', 'buxgalteriya'), ('dispetcher', 'dispetcher'), ('mijoz', 'mijoz')], max_length=50),
        ),
    ]
