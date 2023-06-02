from decimal import Decimal
from django.db import models

from contracts.models import (
    Service, UserData, Role, AgreementStatus,
    slugify_upload
)
from main.models import BaseModel
from one_c.models import PayedInformation

HHD, SSD = ("hhd", "ssd")


class VpsServiceContract(models.Model):
    CONFIRMED_CONTRACT_CHOICES = [
        (1, "WAITING"),
        (2, "UNICON_CONFIRMED"),
        (3, "CLIENT_CONFIRMED"),
        (4, "DONE"),
    ]

    class StatusChoices(models.IntegerChoices):
        DONE = 1, "Bajarildi"
        IN_PROGRESS = 2, "Jarayonda"
        UNDER_REVIEW = 3, "Ko'rib chiqilmoqda"
        NEW = 4, "Yangi"

    class ContractStatusChoices(models.IntegerChoices):
        NEW = 1, "Yangi"
        PAYMENT_IS_PENDING = 2, "To'lov kutilmoqda"
        ACTIVE = 3, "Aktiv"

        REJECTED = 4, "Rad etilgan"
        CANCELLED = 5, "Bekor qilingan"

        FINISHED = 6, "Yakunlangan"

    status = models.IntegerField(choices=StatusChoices.choices, default=4)  # ijro statuslari
    contract_status = models.IntegerField(choices=ContractStatusChoices.choices, default=1)  # hujjat statuslari

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    client = models.ForeignKey(UserData, on_delete=models.CASCADE)
    contract_number = models.CharField(max_length=10, unique=True)
    id_code = models.CharField(max_length=20, blank=True, null=True, unique=True)

    contract_cash = models.DecimalField(max_digits=20, decimal_places=2)  # total_price
    payed_cash = models.DecimalField(max_digits=20, decimal_places=2)

    contract_date = models.DateTimeField(blank=True)
    expiration_date = models.DateTimeField(blank=True, null=True)

    base64file = models.TextField(blank=True, null=True)
    hashcode = models.CharField(max_length=255, blank=True, null=True)
    like_preview_pdf = models.FileField(blank=True, null=True, upload_to="media/Contract/pdf/")  # test mode

    is_confirmed_contract = models.IntegerField(choices=CONFIRMED_CONTRACT_CHOICES, default=1)

    def __str__(self):
        return self.contract_number

    @staticmethod
    def get_new_id_code():
        count = 1
        if VpsServiceContract.objects.all().exists():
            count = VpsServiceContract.objects.last().id  # to'girlab ketish kk
            count += 1
        return f"E{count}"

    # @property
    # def total_payed_percentage(self):
    #     payed_cash = float(0)
    #     for obj in PayedInformation.objects.filter(contract_code=self.id_code):
    #         payed_cash += float(obj.payed_cash)
    #     return (payed_cash * float(100)) / float(self.contract_cash)
    #
    # @property
    # def get_arrearage(self):
    #     if self.payed_cash:
    #         return self.contract_cash - self.payed_cash
    #     return self.contract_cash

    def save(self, *args, **kwargs):
        if not self.pk:
            # Actions to perform only when creating the instance
            self.id_code = self.get_new_id_code()

        super().save(*args, **kwargs)


class OperationSystem(BaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class OperationSystemVersion(BaseModel):
    operation_system = models.ForeignKey(
        to=OperationSystem, on_delete=models.CASCADE, related_name="operation_system", unique=True
    )
    version_name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.operation_system.name}-{self.version_name}"


class VpsDevice(models.Model):
    STORAGE_TYPE_CHOICES = (
        (HHD, HHD),
        (SSD, SSD),
    )
    storage_type = models.CharField(max_length=3, choices=STORAGE_TYPE_CHOICES)
    storage_disk = models.IntegerField()  # default -> GB

    cpu = models.IntegerField()
    ram = models.IntegerField()
    internet = models.IntegerField(blank=True, null=True)
    tasix = models.IntegerField(blank=True, null=True)

    operation_system = models.ForeignKey(
        to=OperationSystem, on_delete=models.CASCADE, related_name="vps_device_operation_system"
    )
    operation_system_version = models.ForeignKey(
        to=OperationSystemVersion, on_delete=models.CASCADE, related_name="vps_device_operation_system_version"
    )

    # Device price
    # device_price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.storage_type}-{self.storage_disk}|{self.cpu}|{self.ram}|{self.internet}"


class VpsTariff(models.Model):
    tariff_name = models.CharField(max_length=255)
    vps_device = models.ForeignKey(to=VpsDevice, on_delete=models.CASCADE, related_name='vps_service_tariff')

    price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    is_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.tariff_name}"


class VpsContractDevice(models.Model):
    contract = models.ForeignKey(
        to=VpsServiceContract, on_delete=models.CASCADE, related_name="vps_contract_device"
    )
    device = models.ForeignKey(
        to=VpsDevice, on_delete=models.CASCADE, related_name="vps_device_contract"
    )

    def __str__(self) -> str:
        return f"{self.contract} | {self.device}"


# class VpsServiceContractTariff(models.Model):
#     Vps_service_tariff = models.ForeignKey(VpsTariff, on_delete=models.CASCADE, related_name='vps_service_tariff')
#
#     price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
#
#     discount_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
#     is_discount = models.BooleanField(default=False)
#
#     def __str__(self) -> str:
#         return f"{self.name_of_tariff}|is_discount:{self.is_discount}"
#
#     def save(self, *args, **kwargs):
#         self.price = self.Vps_service_tariff.price
#         if self.is_discount is False:
#             self.discount_price = None
#         super(VpsServiceContractTarif, self).save(*args, **kwargs)


# class VpsTariffContract(models.Model):
#     contract = models.ForeignKey(to=VpsServiceContract, on_delete=models.CASCADE)
#     tariff = models.ForeignKey(to=VpsServiceContractTarif, on_delete=models.CASCADE)
#
#     def __str__(self) -> str:
#         return f"{self.contract} | {self.tariff}"


class VpsContracts_Participants(models.Model):
    contract = models.ForeignKey(VpsServiceContract, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    participant_user = models.ForeignKey(
        to=UserData, on_delete=models.CASCADE, related_name="vps_contracts_participants"
    )
    # kelishuv statuslari
    agreement_status = models.ForeignKey(AgreementStatus, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.contract.contract_number}|{self.role.name}|{self.agreement_status.name}"


class VpsExpertSummary(models.Model):
    GRANTED = 1
    CANCEL = 0
    summary_choice = (
        (GRANTED, "Shartnoma imzolash maqsadga muvofiq"),
        (CANCEL, "Shartnoma imzolash maqsadga muvofiq emas")
    )
    contract = models.ForeignKey(VpsServiceContract, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    summary = models.IntegerField(choices=summary_choice)
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    user_role = models.ForeignKey(to=Role, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.contract.contract_number}|{self.user.username}|{self.user.role.name}"


class VpsExpertSummaryDocument(models.Model):
    expertsummary = models.ForeignKey(VpsExpertSummary, on_delete=models.CASCADE)
    document = models.FileField(upload_to=slugify_upload, blank=True, null=True)
    client_visible = models.BooleanField(default=False)

    def __str__(self):
        return self.expertsummary.user.role.name


class VpsPkcs(models.Model):
    contract = models.ForeignKey(VpsServiceContract, on_delete=models.CASCADE)
    pkcs7 = models.TextField()

    def __str__(self):
        return self.contract.contract_number
