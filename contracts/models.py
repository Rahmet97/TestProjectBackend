import datetime

from django.db import models
from os.path import splitext

from django.template.defaultfilters import slugify

from accounts.models import Group, UserData, Role


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


class ContractStatus(models.Model):
    name = models.CharField(max_length=50)

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


class Element(models.Model):
    name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    keyword = models.CharField(max_length=30, blank=True, null=True)
    new_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    new_cost_date = models.DateField(blank=True, null=True)
    quantity = models.IntegerField()
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    tariff = models.ForeignKey(Tarif, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


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
    pinned_user = models.ForeignKey(UserData, on_delete=models.CASCADE, blank=True, null=True)
    period = models.IntegerField()
    need_documents = models.ManyToManyField(Document)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

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


class ConnetMethod(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name


class AgreementStatus(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Contract(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    contract_number = models.CharField(max_length=10, unique=True)
    id_code = models.CharField(max_length=11, blank=True, null=True)
    contract_date = models.DateTimeField(blank=True)
    client = models.ForeignKey(UserData, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)  # ijro statuslari
    contract_status = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)  # hujjat statuslari
    condition = models.IntegerField(default=0)
    contract_cash = models.DecimalField(max_digits=20, decimal_places=2)  # total_price
    payed_cash = models.DecimalField(max_digits=20, decimal_places=2)
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE, blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    base64file = models.TextField(blank=True, null=True)
    hashcode = models.CharField(max_length=255, blank=True, null=True)
    like_preview_pdf = models.FileField(blank=True, null=True, upload_to="media/Contract/pdf/")  # test mode

    class Meta:
        indexes = [
            models.Index(fields=['service', 'contract_number', 'id_code', 'client', 'contract_status', 'tarif']),
            models.Index(fields=['contract_date', 'condition', 'hashcode'])
        ]

    def __str__(self):
        return self.contract_number


class OldContractFile(models.Model):
    contract = models.ForeignKey(
        to=Contract, related_name="old_contract_file",
        on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(upload_to=slugify_upload)

    def __str__(self):
        return f"{self.contract} - old contract file"


class UserContractTarifDevice(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, blank=True, null=True)
    client = models.ForeignKey(UserData, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE)
    rack_count = models.IntegerField(blank=True, null=True)
    connect_method = models.ForeignKey(ConnetMethod, on_delete=models.CASCADE, blank=True, null=True)
    odf_count = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_electricity = models.IntegerField(blank=True, null=True)
    devices = models.ManyToManyField(Device, through='UserDeviceCount')

    def __str__(self):
        return self.contract.contract_number


class UserDeviceCount(models.Model):
    user = models.ForeignKey(UserContractTarifDevice, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    device_count = models.IntegerField()
    units_count = models.IntegerField()
    electricity = models.IntegerField()


class Participant(models.Model):  # umumiy model
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    participants = models.ManyToManyField(Role, through='ServiceParticipants')

    def __str__(self):
        return self.service.name


class ServiceParticipants(models.Model):  # umumiy model
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    with_eds = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.role}|{self.participant.service.name}|with_eds={self.with_eds}"


class Contracts_Participants(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    agreement_status = models.ForeignKey(AgreementStatus, on_delete=models.CASCADE, blank=True, null=True)  # kelishuv statuslari

    class Meta:
        indexes = [
            models.Index(fields=['contract', 'role', 'agreement_status'])
        ]

    def __str__(self):
        return f"{self.contract.contract_number}|{self.role.name}|{self.agreement_status.name}"


class ExpertSummary(models.Model):
    GRANTED = 1
    CANCEL = 0
    summary_choice = (
        (GRANTED, "Shartnoma imzolash maqsadga muvofiq"),
        (CANCEL, "Shartnoma imzolash maqsadga muvofiq emas")
    )
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    summary = models.IntegerField(choices=summary_choice)
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    user_role = models.ForeignKey(to=Role, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['contract', 'user', 'date'])
        ]

    def __str__(self) -> str:
        return f"{self.contract.contract_number}|{self.user.username}|{self.user_role}"


class ExpertSummaryDocument(models.Model):
    expertsummary = models.ForeignKey(ExpertSummary, on_delete=models.CASCADE)
    document = models.FileField(upload_to=slugify_upload, blank=True, null=True)
    client_visible = models.BooleanField(default=False)

    def __str__(self):
        return self.expertsummary.user.role.name


class Pkcs(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    pkcs7 = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['contract', 'pkcs7'])
        ]

    def __str__(self):
        return self.contract.contract_number


class SavedService(models.Model):  # umumiy model
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    services = models.ManyToManyField(Service)

    def __str__(self):
        return self.user.username
