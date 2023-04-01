from django.contrib import admin

from expertiseService.models import (
    ExpertiseServiceContract, ExpertiseTarifContract, ExpertiseServiceContractTarif,
    ExpertiseExpertSummary, ExpertiseContracts_Participants, ExpertiseExpertSummaryDocument,

)


admin.site.register((
    ExpertiseExpertSummary,
    ExpertiseContracts_Participants,
    ExpertiseExpertSummaryDocument
))


@admin.register(ExpertiseServiceContractTarif)
class ExpertiseServiceContractTarifAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpertiseServiceContract)
class ExpertiseServiceContractAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpertiseTarifContract)
class ExpertiseTarifContractAdmin(admin.ModelAdmin):
    pass
