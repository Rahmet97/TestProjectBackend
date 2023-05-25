from django.contrib import admin
from .models import Application, TelegramBotChatIDs


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "phone", "email", "is_contracted"]


@admin.register(TelegramBotChatIDs)
class TelegramBotChatIDsAdmin(admin.ModelAdmin):
    list_display = ["chat_name", "chat_id"]
