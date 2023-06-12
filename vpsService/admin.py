# from django.contrib import admin
#
# from .models import (
#     VpsServiceContract,
#     OperationSystem,
#     OperationSystemVersion,
#     VpsDevice,
#     VpsTariff,
#     VpsContractDevice,
#     VpsContracts_Participants,
#     VpsExpertSummary,
#     VpsExpertSummaryDocument,
#     VpsPkcs
# )
#
#
# @admin.register(VpsServiceContract)
# class VpsServiceContractAdmin(admin.ModelAdmin):
#     list_display = ["contract_status", "contract_number", "contract_cash", "payed_cash"]
#
#
# @admin.register(OperationSystem)
# class OperationSystemAdmin(admin.ModelAdmin):
#     list_display = ["name"]
#
#
# @admin.register(OperationSystemVersion)
# class OperationSystemVersionAdmin(admin.ModelAdmin):
#     list_display = ["operation_system", "version_name", "price"]
#
#
# @admin.register(VpsDevice)
# class VpsDeviceAdmin(admin.ModelAdmin):
#     list_display = ["storage_type", "storage_disk", "cpu", "ram", "internet", "tasix", "operation_system_version"]
#
#
# @admin.register(VpsTariff)
# class VpsTariffAdmin(admin.ModelAdmin):
#     list_display = ["tariff_name", "vps_device", "price"]
#
#
# @admin.register(VpsContractDevice)
# class VpsContractDeviceAdmin(admin.ModelAdmin):
#     list_display = ["contract", "device"]
#
#
# @admin.register(VpsContracts_Participants)
# class VpsContracts_ParticipantsAdmin(admin.ModelAdmin):
#     list_display = ["contract", "role", "participant_user", "agreement_status"]
#
#
# @admin.register(VpsExpertSummary)
# class VpsExpertSummaryAdmin(admin.ModelAdmin):
#     list_display = ["contract", "comment", "summary", "user_role", "date"]
#
#
# @admin.register(VpsExpertSummaryDocument)
# class VpsExpertSummaryDocumentAdmin(admin.ModelAdmin):
#     list_display = ["expertsummary", "client_visible"]
#
#
# @admin.register(VpsPkcs)
# class VpsPkcsAdmin(admin.ModelAdmin):
#     list_display = ["contract"]
