from django.contrib import admin

from expertiseService.models import (
    ExpertiseServiceContract, ExpertiseTarifContract, ExpertiseServiceContractTarif,
    ExpertiseExpertSummary, ExpertiseContracts_Participants, ExpertiseExpertSummaryDocument,
    ExpertiseTarif

)

admin.site.register((
    ExpertiseExpertSummary,
    ExpertiseExpertSummaryDocument
))


@admin.register(ExpertiseServiceContractTarif)
class ExpertiseServiceContractTarifAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpertiseServiceContract)
class ExpertiseServiceContractAdmin(admin.ModelAdmin):
    list_display = ["contract_number", "id_code"]


@admin.register(ExpertiseContracts_Participants)
class ExpertiseContracts_ParticipantstAdmin(admin.ModelAdmin):
    list_display = ["contract", "role", "participant_user", "agreement_status"]
    search_fields = ["contract"]


@admin.register(ExpertiseTarifContract)
class ExpertiseTarifContractAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpertiseTarif)
class ExpertiseTarifAdmin(admin.ModelAdmin):
    pass
