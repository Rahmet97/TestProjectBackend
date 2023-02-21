import uuid

from django.db import models

from accounts.models import UserData
from contracts.models import Contract


class Status(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Statuses'


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='ID')
    customer = models.ForeignKey(UserData, on_delete=models.CASCADE)
    number = models.CharField(max_length=4)
    date = models.DateTimeField(auto_now=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
