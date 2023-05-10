from django.db import models
from contracts.models import Contract, Device


class RackManager(models.Manager):
    def create_rack(self, number, unit_count):
        rack = self.create(number=number, unit_count=unit_count)
        for i in range(1, unit_count+1):
            unit = Unit.objects.create(number=i, rack=rack)
            unit.save()
        return rack


class DevicePublisher(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class DeviceStatus(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class ProviderContract(models.Model):
    contract_number = models.CharField(max_length=30)
    contract_date = models.DateField()

    def __str__(self):
        return self.contract_number


class InternetProvider(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Rack(models.Model):
    number = models.IntegerField()
    unit_count = models.IntegerField(default=42)
    is_sold = models.BooleanField(default=False)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, blank=True, null=True)
    provider = models.ForeignKey(InternetProvider, on_delete=models.CASCADE, blank=True, null=True)
    provider_contract = models.ForeignKey(ProviderContract, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.number)

    objects = RackManager()


class DeviceUnit(models.Model):
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, blank=True, null=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, blank=True, null=True)
    device_publisher = models.ForeignKey(DevicePublisher, on_delete=models.CASCADE, blank=True, null=True)
    device_model = models.CharField(max_length=50, blank=True, null=True)
    device_number = models.CharField(max_length=100, blank=True, null=True)
    electricity = models.IntegerField(blank=True, null=True, default=0)
    start = models.IntegerField(default=1)
    end = models.IntegerField(default=1)
    provider = models.ForeignKey(InternetProvider, on_delete=models.CASCADE, blank=True, null=True)
    provider_contract = models.ForeignKey(ProviderContract, on_delete=models.CASCADE, blank=True, null=True)
    status = models.ForeignKey(DeviceStatus, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.device.name


class Unit(models.Model):
    number = models.IntegerField()
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, blank=True, null=True)
    is_busy = models.BooleanField(default=False)
    device = models.ForeignKey(DeviceUnit, on_delete=models.CASCADE, blank=True, null=True, related_name='device_units')
    
    def __str__(self):
        return f'{self.rack.number}-rack {self.number}-unit'
