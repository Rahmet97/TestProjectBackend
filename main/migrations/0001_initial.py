# Generated by Django 3.2.18 on 2023-04-12 10:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contracts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramBotChatIDs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_name', models.CharField(max_length=255)),
                ('chat_id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='F.I.SH/Tashkilot nomi')),
                ('phone', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_contracted', models.BooleanField(default=False)),
                ('file', models.FileField(upload_to='application/files')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_application', to='contracts.service')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_application', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
