import json
import logging

from rest_framework import serializers

from accounts.models import YurUser, FizUser, UserData
from accounts.serializers import YurUserSerializerForContractDetail, FizUserSerializerForContractDetail
from billing.serializers import VpsTariffSummSerializer
from contracts.models import Service
from contracts.serializers import ServiceSerializerForContract, InvoiceInformationSerializer
from one_c.models import Invoice
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

logger = logging.getLogger(__name__)


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


class VpsUserForContractCreateSerializers(serializers.Serializer):
    USER_TYPES = (
        (1, 'fiz'),
        (2, 'yur'),
        # Add more options if needed
    )

    user_type = serializers.ChoiceField(choices=USER_TYPES)
    pin_or_tin = serializers.CharField(max_length=255)


class VpsServiceContractCreateViaClientSerializers(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), pk_field=serializers.IntegerField())
    configuration = VpsTariffSummSerializer(many=True)
    save = serializers.BooleanField(default=False)
    is_back_office = serializers.BooleanField(default=False)

    class Meta:
        model = VpsServiceContract
        fields = ["service", "contract_date", "configuration", "save", "is_back_office"]  # "contract_cash",


class VpsCreateContractWithFileSerializers(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    with_word = serializers.BooleanField(default=False)
    hash_code = serializers.CharField(max_length=255, required=False, allow_null=True)

    class Meta:
        model = VpsServiceContract
        fields = ["service", "contract_date", "with_word", "contract_number", "hash_code"]

    # def to_internal_value(self, data):
    #     # Convert "configuration" field from JSON string to a dictionary
    #     configuration_data = data.get("configuration")
    #     if configuration_data:
    #         try:
    #             modified_configuration_data = json.loads(configuration_data)
    #             data["configuration"] = modified_configuration_data
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError("Invalid configuration data. Unable to decode JSON.")
    #
    #     # Convert "client_user" field from JSON string to a dictionary
    #     client_user_data = data.get("client_user")
    #     if client_user_data:
    #         try:
    #             modified_client_user_data = json.loads(client_user_data)
    #             data["client_user"] = modified_client_user_data
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError("Invalid client user data. Unable to decode JSON.")
    #
    #     return super().to_internal_value(data)

    # def to_internal_value(self, data):
    #     # Convert "configuration" field from JSON string to a list of object instances
    #     configuration_data = data.get("configuration")
    #     if configuration_data:
    #         try:
    #
    #             modified_configuration_data = json.loads(configuration_data)
    #             deserialized_configurations = []
    #             for config_data in modified_configuration_data:
    #                 deserialized_config = self.fields["configuration"].to_internal_value(config_data)
    #                 deserialized_configurations.append(deserialized_config)
    #             data["configuration"] = deserialized_configurations
    #
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError("Invalid configuration data. Unable to decode JSON.")
    #
    #         except serializers.ValidationError as validation_error:
    #             raise serializers.ValidationError("Invalid configuration data. " + str(validation_error))
    #
    #     # Convert "client_user" field from JSON string to an object instance
    #     client_user_data = data.get("client_user")
    #     if client_user_data:
    #         try:
    #
    #             deserialized_user = self.fields["client_user"].to_internal_value(json.loads(client_user_data))
    #             data["client_user"] = deserialized_user
    #
    #         except json.JSONDecodeError:
    #             raise serializers.ValidationError("Invalid client user data. Unable to decode JSON.")
    #
    #         except serializers.ValidationError as validation_error:
    #             raise serializers.ValidationError("Invalid client user data. " + str(validation_error))
    #
    #     return super().to_internal_value(data)


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


class VpsMonitoringContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = VpsServiceContract
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Customize the representation of your data here
        representation['payed_information'] = None
        payed_information_objects = Invoice.objects.filter(contract_code=instance.id_code)
        if payed_information_objects:
            representation['payed_information'] = InvoiceInformationSerializer(
                payed_information_objects, many=True, context={'contract_cash': instance.contract_cash}
            ).data[0],

        client = UserData.objects.get(id=instance.client.id)
        try:
            if client.type == 1:  # FIZ = 1 YUR = 2
                representation["user_type"] = "fiz"
                client = FizUser.objects.get(userdata=client)
                representation["client"]["full_name"] = client.full_name
                representation["client"]["pin"] = client.pin
            else:
                representation["user_type"] = "yur"
                client = YurUser.objects.get(userdata=client)
                representation["client"]["name"] = client.name
                representation["client"]["full_name"] = client.full_name
                representation["client"]["tin"] = client.tin
        except:
            logger.error(f"344: vps contract_number is: {instance.contract_number}, the bug is here ;]")

        # representation["total_payed_percentage"] = (float(instance.payed_cash) * float(100))/float(
        # instance.contract_cash)
        return representation
