# from django.db import models
# from contracts.models import Service, UserData, ContractStatus, Status


# PRICE_SELECT_PERCENTAGE = (
#     (50, 50),
#     (100, 100)
# )


# class ExpertiseServiceContract(models.Model):
#     service = models.ForeignKey(Service, on_delete=models.CASCADE)
#     client = models.ForeignKey(UserData, on_delete=models.CASCADE)

#     contract_number = models.CharField(max_length=10, unique=True)
#     id_code = models.CharField(max_length=11, blank=True, null=True)
#     contract_date = models.DateTimeField(blank=True)
    
#     status = models.ForeignKey(Status, on_delete=models.CASCADE)  # ijro statuslari
#     contract_status = models.ForeignKey(ContractStatus, on_delete=models.CASCADE)  # hujjat statuslari
#     condition = models.IntegerField(default=0)

#     total_price = models.DecimalField(max_digits=10, decimal_places=2)
#     price_select_percentage = models.IntegerField(choices=PRICE_SELECT_PERCENTAGE)

#     # payed_cash = models.DecimalField(max_digits=10, decimal_places=2)
#     # expiration_date = models.DateTimeField(blank=True, null=True)

#     base64file = models.TextField(blank=True, null=True)
#     hashcode = models.CharField(max_length=255, blank=True, null=True)

#     like_preview_pdf = models.FileField(blank=True, null=True, upload_to="media/Contract/pdf/")  # test mode

#     def __str__(self):
#         return self.contract_number
    
#     def get_new_id_code(self):
#         # count = ExpertiseServiceContract.objects.all().count()
#         count = self.objects.all().count()
#         return f"E{count+1}"
    
#     def save(self, *args, **kwargs):
#         self.id_code=self.get_new_id_code()
#         super(ExpertiseServiceContract, self).save(*args, **kwargs)


# class ExpertiseServiceContractTarif(models.Model):
#     title_of_tarif = models.CharField(max_length=255)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     name_of_tarif = models.CharField()
#     is_discount = models.BooleanField(default=False)

#     def __str__(self) -> str:
#         return self.name_of_tarif


# class ExpertiseTarifContract(models.Model):
#     contract = models.ForeignKey(to=ExpertiseServiceContract)
#     tarif = models.ForeignKey(to=ExpertiseServiceContractTarif)

#     def __str__(self) -> str:
#         return f"{self.contract} | {self.tarif}"
    