from rest_framework import serializers

from .models import (
    VpsServiceContract,
    OperationSystem,
    OperationSystemVersion,
    VpsDevice,
    VpsTariff,
    VpsContractDevice,
    VpsContracts_Participants,
    VpsExpertSummary,
    VpsExpertSummaryDocument,
)


class OperationSystemVersionSerializers(serializers.ModelSerializer):

    class Meta:
        model = OperationSystemVersion
        read_only_fields = ["id"]
        fields = ["id", "version_name", "price"]


class OperationSystemSerializers(serializers.ModelSerializer):

    class Meta:
        model = OperationSystem
        read_only_fields = ["id"]
        fields = ["id", "name"]
