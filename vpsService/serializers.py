from rest_framework import serializers

from contracts.serializers import ServiceSerializerForContract
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


# Serializer for VpsService Contract Create
class VpsServiceContractConfigurationCreateSerializers(serializers.ModelSerializer):
    tariff_id = serializers.IntegerField(required=False)
    operation_system_version_id = serializers.PrimaryKeyRelatedField(
        many=True, queryset=OperationSystemVersion.objects.all()
    )

    class Meta:
        model = VpsDevice
        fields = [
            "storage_type", "storage_disk", "cpu", "ram", "internet", "tasix", "tariff_id",
            "operation_system_version_id"
        ]


class VpsServiceContractCreateSerializers(serializers.ModelSerializer):
    configuration = VpsServiceContractConfigurationCreateSerializers(many=True)
    user_tin_or_pin = serializers.CharField(max_length=50)

    class Meta:
        model = VpsServiceContract
        fields = ["service", "contract_date", "configuration", "user_tin_or_pin", "contract_cash"]


# Serializer for VpsService app showed
class VpsDeviceSerializers(serializers.ModelSerializer):
    class Meta:
        model = VpsDevice
        exclude = ["operation_system", "operation_system_version"]


class VpsTariffSerializers(serializers.ModelSerializer):
    class Meta:
        model = VpsTariff
        fields = ["id", "tariff_name"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["vps_device"] = VpsDeviceSerializers(instance.vps_device).data
        return representation


class VpsGetUserContractsListSerializer(serializers.ModelSerializer):
    service = ServiceSerializerForContract()

    class Meta:
        model = VpsServiceContract
        fields = ['id', 'service', 'contract_number', 'contract_date', 'contract_cash', 'hashcode']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["is_confirmed_contract"] = instance.is_confirmed_contract
        representation["status"] = instance.get_status_display()
        representation["contract_status"] = instance.get_contract_status_display()
        return representation


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
