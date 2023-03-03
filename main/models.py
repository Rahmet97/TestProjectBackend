from django.db import models
from django.contrib.auth import get_user_model

from contracts.models import Service

UserData = get_user_model()


class TelegramBotChatIDs(models.Model):
    chat_name = models.CharField(max_length=255)
    chat_id = models.IntegerField()

    def __str__(self):
        return self.chat_name



class Application(models.Model):
    user = models.ForeignKey(to=UserData, related_name="user_application", on_delete=models.CASCADE)
    service = models.ForeignKey(to=Service, related_name="service_application", on_delete=models.CASCADE)
    name = models.CharField(verbose_name="F.I.SH/Tashkilot nomi", max_length=255)
    phone = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    file = models.FileField(upload_to="application/files", blank=True, null=True)

    def __str__(self):
        return self.name
    

