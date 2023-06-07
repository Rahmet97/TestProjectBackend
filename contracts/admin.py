from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources

admin.site.register((
    SavedService,
    UserContractTarifDevice,
    UserDeviceCount,
    Contract,
    ExpertSummary,
    ExpertSummaryDocument,

    OldContractFile  # test
))


class ServiceResource(resources.ModelResource):
    class Meta:
        model = Service


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    resource_class = ServiceResource


class ElementResource(resources.ModelResource):
    class Meta:
        model = Element


@admin.register(Element)
class ElementAdmin(ImportExportModelAdmin):
    resource_class = ElementResource


class DeviceResource(resources.ModelResource):
    class Meta:
        model = Device


@admin.register(Device)
class DeviceAdmin(ImportExportModelAdmin):
    resource_class = DeviceResource


class OfferResource(resources.ModelResource):
    class Meta:
        model = Offer


@admin.register(Offer)
class OfferAdmin(ImportExportModelAdmin):
    resource_class = OfferResource


class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document


@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    resource_class = DocumentResource


class TarifResource(resources.ModelResource):
    class Meta:
        model = Tarif


@admin.register(Tarif)
class TarifAdmin(ImportExportModelAdmin):
    resource_class = TarifResource


class ContractStatusResource(resources.ModelResource):
    class Meta:
        model = ContractStatus


@admin.register(ContractStatus)
class ContractStatusAdmin(ImportExportModelAdmin):
    resource_class = ContractStatusResource


class AgreementStatusResource(resources.ModelResource):
    class Meta:
        model = AgreementStatus


@admin.register(AgreementStatus)
class AgreementStatusAdmin(ImportExportModelAdmin):
    resource_class = AgreementStatusResource


class StatusResource(resources.ModelResource):
    class Meta:
        model = Status


@admin.register(Status)
class StatusAdmin(ImportExportModelAdmin):
    resource_class = StatusResource


class ConnetMethodResource(resources.ModelResource):
    class Meta:
        model = ConnetMethod


@admin.register(ConnetMethod)
class ConnetMethodAdmin(ImportExportModelAdmin):
    resource_class = ConnetMethodResource


class ParticipantResource(resources.ModelResource):
    class Meta:
        model = Participant


@admin.register(Participant)
class ParticipantAdmin(ImportExportModelAdmin):
    resource_class = ParticipantResource


class ServiceParticipantsResource(resources.ModelResource):
    class Meta:
        model = ServiceParticipants


@admin.register(ServiceParticipants)
class ServiceParticipantsAdmin(ImportExportModelAdmin):
    resource_class = ServiceParticipantsResource
    list_display = ["participant", "role", "with_eds"]


@admin.register(Contracts_Participants)
class Contracts_ParticipantsAdmin(admin.ModelAdmin):
    list_display = ["contract", "role", "agreement_status"]
    search_fields = ["contract"]
