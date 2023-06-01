import uuid

from django.db import models
from django.contrib.auth import get_user_model

from contracts.models import Service

UserData = get_user_model()


# Base model class that provides common fields and functionalities for other models to inherit from
class BaseModel(models.Model):
    # Unique identifier for each instance of the model
    id = models.UUIDField(unique=True, editable=False, default=uuid.uuid4, primary_key=True)

    # DateTimeField that automatically stores the creation time of an instance when
    # it is first saved to the database
    created_time = models.DateTimeField(auto_now_add=True)

    # DateTimeField that automatically updates with the current time whenever
    # the instance is saved or updated in the database
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        # Specifies that this model is abstract, meaning it won't be created as a separate table in the database
        abstract = True


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

    is_contracted = models.BooleanField(default=False)

    file = models.FileField(upload_to="application/files")

    def __str__(self):
        return self.name


class TestFileUploader(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="testFileUploader")

    def __str__(self):
        return self.name
