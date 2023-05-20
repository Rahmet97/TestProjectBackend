from decimal import Decimal
from django.db import models

from contracts.models import (
    Service, UserData, Role, AgreementStatus,
    slugify_upload
)
from one_c.models import PayedInformation

PRICE_SELECT_PERCENTAGE = (
    (50, 50),
    (100, 100)
)


class ExpertiseServiceContract(models.Model):
    class ConfirmedContractStatusChoices(models.IntegerChoices):
        WAITING = 1, "WAITING"
        UNICON_CONFIRMED = 2, "UNICON_CONFIRMED"
        CLIENT_CONFIRMED = 3, "CLIENT_CONFIRMED"

    class StatusChoices(models.IntegerChoices):
        DONE = 1, "Bajarildi"
        IN_PROGRESS = 2, "Jarayonda"
        UNDER_REVIEW = 3, "Ko'rib chiqilmoqda"
        NEW = 4, "Yangi"

    class ContractStatusChoices(models.IntegerChoices):
        CREATED = 0, "Yaratilgan"
        REJECTED = 1, "Rad etilgan"
        FINISHED = 2, "Yakunlangan"
        ACTIVE = 3, "Aktiv"
        PAYMENT_IS_PENDING = 4, "To'lov kutilmoqda"
        CANCELLED = 5, "Bekor qilingan"
        NEW = 6, "Yangi"
        APPROVED = 7, "Tasdiqlangan"

    status = models.IntegerField(choices=StatusChoices.choices, default=4)  # ijro statuslari
    contract_status = models.IntegerField(choices=ContractStatusChoices.choices, default=0)  # hujjat statuslari

    price_select_percentage = models.IntegerField(choices=PRICE_SELECT_PERCENTAGE, blank=True, null=True)

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    client = models.ForeignKey(UserData, on_delete=models.CASCADE)
    contract_number = models.CharField(max_length=10, unique=True)
    id_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    # condition = models.IntegerField(default=0)

    contract_cash = models.DecimalField(max_digits=20, decimal_places=2)  # total_price
    payed_cash = models.DecimalField(max_digits=20, decimal_places=2)

    contract_date = models.DateTimeField(blank=True)
    expiration_date = models.DateTimeField(blank=True, null=True)

    base64file = models.TextField(blank=True, null=True)
    hashcode = models.CharField(max_length=255, blank=True, null=True)
    like_preview_pdf = models.FileField(blank=True, null=True, upload_to="media/Contract/pdf/")  # test mode

    is_confirmed_contract = models.IntegerField(
        choices=ConfirmedContractStatusChoices, default=ConfirmedContractStatusChoices.WAITING
    )

    def __str__(self):
        return self.contract_number

    @staticmethod
    def get_new_id_code():
        count = 1
        if ExpertiseServiceContract.objects.all().exists():
            print("last_id", ExpertiseServiceContract.objects.last().id)
            count = ExpertiseServiceContract.objects.last().id  # to'girlab ketish kk
            count += 1
        return f"E{count}"

    @property
    def total_payed_percentage(self):
        payed_cash = float(0)
        for obj in PayedInformation.objects.filter(contract_code=self.id_code):
            payed_cash += float(obj.payed_cash)
        return (payed_cash * float(100)) / float(self.contract_cash)

    @property
    def get_arrearage(self):
        if self.payed_cash:
            return self.contract_cash - self.payed_cash
        return self.contract_cash

    def save(self, *args, **kwargs):
        if not self.pk:
            # Actions to perform only when creating the instance
            self.id_code = self.get_new_id_code()

        super().save(*args, **kwargs)


class ExpertiseTarif(models.Model):
    title_of_tarif = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.title_of_tarif}|{self.price}"


class ExpertiseServiceContractTarif(models.Model):
    expertise_service_tarif = models.ForeignKey(
        ExpertiseTarif, on_delete=models.CASCADE, related_name='expertise_service_tarif')

    price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    discount_price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    name_of_tarif = models.CharField(max_length=255)
    is_discount = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name_of_tarif}|is_discount:{self.is_discount}"

    def save(self, *args, **kwargs):
        self.price = self.expertise_service_tarif.price
        if self.is_discount is False:
            self.discount_price = None
        super(ExpertiseServiceContractTarif, self).save(*args, **kwargs)


class ExpertiseTarifContract(models.Model):
    contract = models.ForeignKey(to=ExpertiseServiceContract, on_delete=models.CASCADE)
    tarif = models.ForeignKey(to=ExpertiseServiceContractTarif, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.contract} | {self.tarif}"


class ExpertiseContracts_Participants(models.Model):
    contract = models.ForeignKey(ExpertiseServiceContract, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    participant_user = models.ForeignKey(to=UserData, on_delete=models.CASCADE, related_name="participant_user")
    # kelishuv statuslari
    agreement_status = models.ForeignKey(AgreementStatus, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.contract.contract_number}|{self.role.name}|{self.agreement_status.name}"


class ExpertiseExpertSummary(models.Model):
    GRANTED = 1
    CANCEL = 0
    summary_choice = (
        (GRANTED, "Shartnoma imzolash maqsadga muvofiq"),
        (CANCEL, "Shartnoma imzolash maqsadga muvofiq emas")
    )
    contract = models.ForeignKey(ExpertiseServiceContract, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    summary = models.IntegerField(choices=summary_choice)
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    user_role = models.ForeignKey(to=Role, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.contract.contract_number}|{self.user.username}|{self.user.role.name}"


class ExpertiseExpertSummaryDocument(models.Model):
    expertsummary = models.ForeignKey(ExpertiseExpertSummary, on_delete=models.CASCADE)
    document = models.FileField(upload_to=slugify_upload, blank=True, null=True)
    client_visible = models.BooleanField(default=False)

    def __str__(self):
        return self.expertsummary.user.role.name


class ExpertisePkcs(models.Model):
    contract = models.ForeignKey(ExpertiseServiceContract, on_delete=models.CASCADE)
    pkcs7 = models.TextField()

    def __str__(self):
        return self.contract.contract_number
