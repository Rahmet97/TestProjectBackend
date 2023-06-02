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


# Serializer for OperationSystemVersion model
class OperationSystemVersionSerializers(serializers.ModelSerializer):

    class Meta:
        model = OperationSystemVersion
        # Specify the read-only fields
        read_only_fields = ["id"]
        # Specify the fields to include in the serialized representation
        fields = ["id", "version_name", "price"]


# Serializer for OperationSystem model
class OperationSystemSerializers(serializers.ModelSerializer):

    class Meta:
        model = OperationSystem
        # Specify the read-only fields
        read_only_fields = ["id"]
        # Specify the fields to include in the serialized representation
        fields = ["id", "name"]
