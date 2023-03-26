from django.db import models
from django.contrib.auth import get_user_model

from contracts.models import Service

UserData = get_user_model()


class TelegramBotChatIDs(models.Model):
    chat_name = models.CharField(max_length=255)
    chat_id = models.IntegerField()

    def __str__(self):
        return self.chat_name




    

