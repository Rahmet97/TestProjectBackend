import uuid

from django.db import models

from accounts.models import UserData
from contracts.models import Contract, Service


class Status(models.Model):
    name = models.CharField(max_length=10)
    status_code = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Statuses'


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='ID')
    customer = models.ForeignKey(UserData, on_delete=models.CASCADE)
    number = models.CharField(max_length=20)
    date = models.DateTimeField(auto_now=True)
    # contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    contract_code = models.CharField(max_length=20, blank=True, null=True)  # id_code which is of the contract
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.number

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'


class Nomenclature(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    nomenclature = models.CharField(max_length=25)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.service.name


class PayedInformation(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=True, null=True)
    # contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    payed_cash = models.FloatField()
    payed_time = models.DateTimeField()
    contract_code = models.CharField(max_length=20, blank=True, null=True)  # id_code which is of the contract
    customer_tin = models.IntegerField(blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    customer_payment_account = models.CharField(max_length=30, blank=True, null=True)
    customer_mfo = models.IntegerField(blank=True, null=True)
    company_payment_account = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.contract.contract_number
