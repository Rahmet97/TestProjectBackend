from django.db import models

from accounts.models import UserData

from TestProjectBackend.contracts.models import Service


class BillingLog(models.Model):
    FRONTOFFICE = 1
    BACKOFFICE = 2
    office = (
        (FRONTOFFICE, 'Frontoffice'),
        (BACKOFFICE, 'Backoffice'),
    )
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    fr = models.IntegerField(choices=office)
    request = models.JSONField()
    response = models.JSONField()
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.date)


class InvoiceElements(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    is_automate = models.BooleanField(defaul=False)
    date = models.DateField()

    def __str__(self):
        return f'{self.service.name}|{self.is_automate}|{self.date}'