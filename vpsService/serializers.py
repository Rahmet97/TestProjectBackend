from rest_framework import serializers

from accounts.models import YurUser, FizUser
from accounts.serializers import YurUserSerializerForContractDetail, FizUserSerializerForContractDetail
from billing.serializers import VpsTariffSummSerializer
from contracts.models import Service
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
    VpsExpertSummaryDocument, VpsPkcs,
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


class VpsContractSerializerForDetail(serializers.ModelSerializer):

    class Meta:
        model = VpsServiceContract
        fields = (
            'id', 'contract_number', 'contract_date', 'expiration_date',
            'contract_cash', 'payed_cash', 'base64file', 'hashcode',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["is_confirmed_contract"] = instance.is_confirmed_contract
        representation["arrearage"] = instance.contract_cash - instance.payed_cash
        representation["status"] = instance.get_status_display()
        representation["contract_status"] = instance.get_contract_status_display()
        return representation


class VpsExpertSummarySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        if obj.user.type == 2:
            u = YurUser.objects.get(userdata=obj.user)
            user = YurUserSerializerForContractDetail(u)
        else:
            u = FizUser.objects.get(userdata=obj.user)
            user = FizUserSerializerForContractDetail(u)
        return user.data

    class Meta:
        model = VpsExpertSummary
        fields = "__all__"


class VpsExpertSummarySerializerForSave(serializers.ModelSerializer):

    def create(self, validated_data):
        documents = self.context['documents']
        expertsummary = VpsExpertSummary.objects.create(**validated_data)

        for document in documents:
            VpsExpertSummaryDocument.objects.create(
                expertsummary=expertsummary,
                document=document
            )
        return expertsummary

    class Meta:
        model = VpsExpertSummary
        fields = "__all__"


class VpsContractParticipantsSerializers(serializers.ModelSerializer):
    userdata = serializers.SerializerMethodField()
    expert_summary = serializers.SerializerMethodField()
    agreement_status = serializers.CharField(source='agreement_status.name')

    def get_userdata(self, obj):
        userdata = obj.participant_user
        if userdata.type == 2:
            user = YurUser.objects.select_related('userdata').get(userdata=userdata)
            return YurUserSerializerForContractDetail(user).data
        else:
            user = FizUser.objects.select_related('userdata').get(userdata=userdata)
            return FizUserSerializerForContractDetail(user).data

    def get_expert_summary(self, obj):
        try:
            userdata = obj.participant_user
            summary = VpsExpertSummary.objects.get(contract=obj.contract, user=userdata)
            serializer = VpsExpertSummarySerializer(summary)
            return serializer.data
        except VpsExpertSummary.DoesNotExist:
            return {}

    class Meta:
        model = VpsContracts_Participants
        fields = '__all__'



# Serializer for VpsService Contract Via Client Create
# class VpsServiceContractConfigurationCreateSerializers(serializers.ModelSerializer):
#     tariff_id = serializers.IntegerField(required=False)
#     operation_system_version_id = serializers.PrimaryKeyRelatedField(
#         many=True, queryset=OperationSystemVersion.objects.all()
#     )
#
#     class Meta:
#         model = VpsDevice
#         fields = [
#             "storage_type", "storage_disk", "cpu", "ram", "internet", "tasix", "tariff_id",
#             "operation_system_version_id"
#         ]


class VpsServiceContractCreateViaClientSerializers(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    configuration = VpsTariffSummSerializer(many=True)
    save = serializers.BooleanField(default=False)

    class Meta:
        model = VpsServiceContract
        fields = ["service", "contract_date", "configuration", "save"]  # "contract_cash",


class VpsServiceContractResponseViaClientSerializers(serializers.ModelSerializer):
    class Meta:
        model = VpsServiceContract
        fields = ["id", "base64file"]
        read_only_fields = ["id", "base64file"]


# Serializers for GetGroupContract API
class GroupVpsContractSerializerForBackoffice(serializers.ModelSerializer):

    class Meta:
        model = VpsServiceContract
        fields = ["id", "contract_number", "contract_date", "expiration_date", "contract_cash", "payed_cash"]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["contract_status"] = instance.get_contract_status_display()
        rep["arrearage"] = instance.contract_cash - instance.payed_cash

        rep["client"] = {}
        client = instance.client
        if client.type == 2:
            client = YurUser.objects.get(userdata=client)
            rep["client"]["name"] = client.name
            rep["client"]["full_name"] = client.full_name
            rep["client"]["tin"] = client.tin
        else:
            client = FizUser.objects.get(userdata=client)
            rep["client"]["full_name"] = client.full_name
            rep["client"]["pin"] = client.pin

        return rep


class VpsPkcsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VpsPkcs
        fields = '__all__'


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class ConvertDocx2PDFSerializer(serializers.Serializer):
    key = serializers.CharField()
    url = serializers.URLField()


class ForceSaveFileSerializer(serializers.Serializer):
    key = serializers.CharField()
