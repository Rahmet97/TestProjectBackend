import uuid

from django.db import models

from accounts.models import UserData
from contracts.models import Contract


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='ID')
    customer = models.ForeignKey(UserData, on_delete=models.CASCADE)
    number = models.CharField(max_length=4)
    date = models.DateTimeField(auto_now=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    
