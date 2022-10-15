from django.db import models
from os.path import splitext

from django.template.defaultfilters import slugify

from accounts.models import Group, UserData


def slugify_upload(instance, filename):
    folder = instance._meta.model.__name__
    name, ext = splitext(filename)
    try:

        name_t = slugify(name)
        if name_t is None:
            name_t = name
        path = folder + "/" + name_t + ext
    except:
        path = folder + "/default" + ext

    return path


class ContractType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Element(models.Model):
    name = models.CharField(max_length=50)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Status(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Tarif(models.Model):
    name = models.CharField(max_length=30)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class TarifElement(models.Model):
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE)
    element = models.ForeignKey(Element, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tarif.name} {self.element.name}'


class TarifLog(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE)
    comment = models.TextField()
    updated_date = models.DateTimeField()

    def __str__(self):
        return self.comment


class Document(models.Model):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to=slugify_upload, blank=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    FizLitso = 1
    YurLitso = 2
    All = 3
    users_type = (
        (FizLitso, 'Jismoniy'),
        (YurLitso, 'Yuridik'),
        (All, 'Yuridik va jismoniy')
    )
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to=slugify_upload)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user_type = models.IntegerField(choices=users_type)
    period = models.IntegerField()
    need_documents = models.ManyToManyField(Document)

    def __str__(self):
        return self.name


class Offer(models.Model):
    service = models.OneToOneField(Service, on_delete=models.CASCADE)
    file = models.FileField(upload_to=slugify_upload)

    def __str__(self):
        return self.service.name


class Device(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class UserContractTarifDevice(models.Model):
    client = models.ForeignKey(UserData, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE)
    devices = models.ManyToManyField(Device, through='UserDeviceCount')

    def __str__(self):
        return self.service.name


class UserDeviceCount(models.Model):
    user = models.ForeignKey(UserContractTarifDevice, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    device_count = models.IntegerField()
    units_count = models.IntegerField()
    electricity = models.IntegerField()


class Contract(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    contract_number = models.CharField(max_length=10)
    client_signed_date = models.DateTimeField(auto_now_add=True, blank=True)
    contract_date = models.DateTimeField(blank=True)
    service_type = models.CharField(max_length=50)
    participants = models.ManyToManyField(UserData)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    contract_cash = models.DecimalField(max_digits=10, decimal_places=2)
    payed_cash = models.DecimalField(max_digits=10, decimal_places=2)
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE)
    expiration_date = models.DateTimeField()
    file = models.FileField(upload_to=slugify_upload)

    def __str__(self):
        return self.service.name


class Pkcs(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    pkcs7 = models.TextField()

    def __str__(self):
        return self.contract.contract_number
