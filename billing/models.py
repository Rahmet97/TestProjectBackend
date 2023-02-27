from django.db import models

from accounts.models import UserData


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
