# Generated by Django 3.2.18 on 2023-03-03 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_alter_application_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='message',
            field=models.TextField(),
        ),
    ]
