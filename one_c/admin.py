from django.contrib import admin
from .models import Status, Invoice, Nomenclature, PayedInformation

admin.site.register(Status)


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ["service", "nomenclature", "name"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["customer", "number", "contract_code", "status"]


@admin.register(PayedInformation)
class PayedInformationAdmin(admin.ModelAdmin):
    list_display = ["invoice", "payed_cash", "payed_time", "contract_code", "customer_tin"]
