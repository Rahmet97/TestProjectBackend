from rest_framework import serializers

from accounts.models import UserData

from expertiseService.models import (
    ExpertiseServiceContractTarif, ExpertiseServiceContract, ExpertiseTarifContract
)


class ExpertiseServiceContractProjects(serializers.ModelSerializer):
    class Meta:
        model = ExpertiseServiceContractTarif
        fields = "__all__"


class ExpertiseServiceContractSerializers(serializers.ModelSerializer):
    projects = ExpertiseServiceContractProjects(many=True)
    stir = serializers.CharField(max_length=9)

    class Meta:
        model = ExpertiseServiceContract
        fields = ["service" , "contract_number", "contract_date", "projects", "stir", "total_price", "price_select_percentage"]
