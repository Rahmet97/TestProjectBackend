from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import serializers, status

from main.utils import responseErrorMessage

from one_c.models import PayedInformation, Invoice

from accounts.models import YurUser, FizUser, UserData, Role
from accounts.serializers import (
    GroupSerializer, FizUserSerializer, YurUserSerializer,
    YurUserSerializerForContractDetail, FizUserSerializerForContractDetail
)

from .models import (
    Service, Tarif, Device, Contract, UserContractTarifDevice, UserDeviceCount, Offer, Document,
    Element, SavedService, Pkcs, ExpertSummary, Contracts_Participants, ContractStatus, ConnetMethod,
    ExpertSummaryDocument, OldContractFile
)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    need_documents = DocumentSerializer(many=True)
    group = GroupSerializer()
    user_type = serializers.SerializerMethodField()

    def get_user_type(self, obj):
        if obj.user_type == 1:
            return "Jismoniy"
        elif obj.user_type == 2:
            return "Yuridik"
        else:
            return "Jismoniy va Yuridik"

    def get_is_saved(self, obj):
        user = self.context.get('user')
        if user and user.is_authenticated:
            saved_services = SavedService.objects.filter(user=user).first()
            if saved_services and saved_services.services.filter(pk=obj.pk).exists():
                return True
        return False

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'image', 'user_type', 'period', 'need_documents', 'group')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["is_saved"] = False
        user = self.context.get('user')
        if user and user.is_authenticated:
            saved_services = SavedService.objects.filter(user=user).first()

            if saved_services and saved_services.services.filter(pk=instance.pk).exists():
                representation["is_saved"] = True

        return representation


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        exclude = ["need_documents"]


class ServiceSerializerForContract(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name')


class TarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarif
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class UserDeviceCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceCount
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['device'] = DeviceSerializer(instance.device).data
        return representation


class UserContractTarifDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContractTarifDevice
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tarif'] = TarifSerializer(instance.tarif).data

        representation['user_device'] = UserDeviceCountSerializer(
            UserDeviceCount.objects.filter(user=instance), many=True
        ).data

        return representation


# old contract file serializers
class AddOldContractFilesSerializers(serializers.ModelSerializer):
    class Meta:
        model = OldContractFile
        fields = ["id", "file"]


class ContractSerializer(serializers.ModelSerializer):
    contract_number = serializers.SerializerMethodField()

    def get_contract_number(self, obj):
        group_names = obj.service.group.name.split()
        c_number = ''
        for i in group_names:
            c_number += i[0]
        return c_number

    class Meta:
        model = Contract
        fields = '__all__'


class ContractStatusSerializerForContractsList(serializers.ModelSerializer):
    class Meta:
        model = ContractStatus
        fields = ('id', 'name')


class ContractSerializerForContractList(serializers.ModelSerializer):
    service = ServiceSerializerForContract()
    contract_status = ContractStatusSerializerForContractsList()

    class Meta:
        model = Contract
        fields = ('id', 'service', 'contract_number', 'contract_date', 'contract_status', 'contract_cash', 'hashcode')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        old_contract = instance.old_contract_file.all()
        context = {
            "has_old_contract": False,
            "old_contract": None
        }

        if old_contract:
            context['has_old_contract'] = True
            context['old_contract'] = AddOldContractFilesSerializers(old_contract, many=True).data

        representation["old_contract"] = context
        return representation


class ContractSerializerForBackoffice(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    contract_status = ContractStatusSerializerForContractsList()

    def get_client(self, obj):
        try:
            client_id = Contract.objects.select_related('client').get(id=obj.id).client
            if client_id.type == 2:
                clientt = YurUser.objects.get(userdata=client_id)
                serializer = YurUserSerializerForContractDetail(clientt)
            else:
                clientt = FizUser.objects.get(userdata=client_id)
                serializer = FizUserSerializerForContractDetail(clientt)

        except Contract.DoesNotExist:
            return dict()

        return serializer.data

    def get_arrearage(self, obj):
        return obj.contract_cash - obj.payed_cash

    class Meta:
        model = Contract
        fields = (
            'id', 'client', 'contract_number', 'contract_date', 'expiration_date', 'contract_cash',
            'payed_cash', 'arrearage', 'contract_status'
        )


class ContractSerializerForDetail(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    contract_status = ContractStatusSerializerForContractsList()

    # old_contract = serializers.SerializerMethodField()

    @staticmethod
    def get_arrearage(obj):
        return obj.contract_cash - obj.payed_cash

    class Meta:
        model = Contract
        fields = (
            'id', 'contract_number', 'contract_date', 'expiration_date', 'contract_cash', 'payed_cash',
            'arrearage', 'contract_status', 'base64file', 'hashcode'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        user_contract_tariff_device = UserContractTarifDevice.objects.filter(contract=instance)
        representation["tariff"] = {
            "tariff": TarifSerializer(instance.tarif).data,
            "user_contract_tariff_device": UserContractTarifDeviceSerializer(
                user_contract_tariff_device, many=True
            ).data
        }

        old_contract = instance.old_contract_file.all()
        representation['old_contract'] = {
            "has_old_contract": False,
            "old_contract": None
        }

        if old_contract:
            representation['old_contract']['has_old_contract'] = True
            representation['old_contract']['old_contract'] = AddOldContractFilesSerializers(
                old_contract, many=True).data

        return representation


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = '__all__'


class GetElementSerializer(serializers.ModelSerializer):
    group = GroupSerializer()
    tariff = TarifSerializer()

    class Meta:
        model = Element
        fields = '__all__'


class PkcsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pkcs
        fields = '__all__'


class ExpertSummarySerializer(serializers.ModelSerializer):
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
        model = ExpertSummary
        fields = "__all__"


class ConnectMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnetMethod
        fields = '__all__'


class ExpertSummarySerializerForSave(serializers.ModelSerializer):

    def create(self, validated_data):
        documents = self.context['documents']
        if ExpertSummary.objects.filter(
                contract=validated_data.get("contract"), user=validated_data.get("user")
        ).exists():
            responseErrorMessage(
                message="Already exists in ExpertSummary",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        expertsummary = ExpertSummary.objects.create(**validated_data)
        for document in documents:
            ExpertSummaryDocument.objects.create(
                expertsummary=expertsummary,
                document=document
            )
        return expertsummary

    class Meta:
        model = ExpertSummary
        fields = "__all__"


class ContractParticipantsSerializers(serializers.ModelSerializer):
    agreement_status = serializers.SerializerMethodField()
    userdata = serializers.SerializerMethodField()
    expert_summary = serializers.SerializerMethodField()

    @staticmethod
    def get_userdata(obj):
        try:
            if obj.role.name != Role.RoleNames.ADMIN and obj.role.name != Role.RoleNames.CLIENT:
                userdata = UserData.objects.filter(
                    Q(role=obj.role) &
                    (
                            Q(group__in=[obj.contract.service.group]) |
                            Q(group=None)
                    )
                ).first()
                if userdata is not None:
                    if userdata.type == 2:
                        u = YurUser.objects.get(userdata=userdata)
                        user = YurUserSerializerForContractDetail(u)
                    else:
                        u = FizUser.objects.get(userdata=userdata)
                        user = FizUserSerializerForContractDetail(u)
                    return user.data
        except ObjectDoesNotExist:
            pass
        return None

    @staticmethod
    def get_expert_summary(obj):
        try:
            userdata = UserData.objects.get(
                Q(role=obj.role),
                # Q(group=obj.contract.service.group)
                Q(group__in=[obj.contract.service.group])
            )
            summary = ExpertSummary.objects.filter(contract=obj.contract).get(user=userdata)
            serializer = ExpertSummarySerializer(summary)
            return serializer.data
        except ObjectDoesNotExist:
            return {}

    @staticmethod
    def get_agreement_status(obj):
        return obj.agreement_status.name

    class Meta:
        model = Contracts_Participants
        fields = '__all__'


# old contracts
class UserOldContractTarifDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContractTarifDevice
        exclude = ["client", "price"]


class AddOldContractSerializers(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = ["id", "service", "contract_number", "contract_date", "expiration_date", "tarif", "file"]

    @staticmethod
    def get_file(obj):
        return AddOldContractFilesSerializers(obj.old_contract_file.all(), many=True).data


# Serializer for monitoring contract
class PayedInformationSerializer(serializers.ModelSerializer):
    payed_percentage = serializers.SerializerMethodField()
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = PayedInformation
        # fields = "__all__"
        exclude = ["invoice"]

    def get_payed_percentage(self, obj):
        contract_cash = self.context.get("contract_cash")
        if contract_cash is None:
            responseErrorMessage(message=None, status_code=status.HTTP_400_BAD_REQUEST)
        return (float(obj.payed_cash) * float(100)) / float(contract_cash)

    @staticmethod
    def get_month_name(obj):
        date_object = datetime.fromisoformat(str(obj.payed_time))
        return date_object.strftime("%B")


class InvoiceInformationSerializer(serializers.ModelSerializer):
    payed_information = serializers.SerializerMethodField()

    def get_payed_information(self, obj):
        if PayedInformation.objects.filter(invoice=obj).exists():
            # payed_info = PayedInformation.objects.get(invoice=obj)
            payed_info = PayedInformation.objects.filter(invoice=obj)
            return PayedInformationSerializer(
                payed_info, context={
                    'contract_cash': self.context.get("contract_cash")
                }, many=True).data
        return {}

    class Meta:
        model = Invoice
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["invoice_status"] = {
            "name": instance.status.name,
            "status_code": instance.status.status_code
        }
        return representation


class MonitoringContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
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
        if client.type == 1:  # FIZ = 1 YUR = 2
            representation["client"] = FizUserSerializer(FizUser.objects.get(userdata=client)).data
            representation["user_type"] = "fiz"
        else:
            representation["client"] = YurUserSerializer(YurUser.objects.get(userdata=client)).data
            representation["user_type"] = "yur"

        # representation["total_payed_percentage"] = (float(instance.payed_cash) * float(100))/float(
        # instance.contract_cash)
        return representation


# Serializers for GetGroupContract API
class GroupContractSerializerForBackoffice(serializers.ModelSerializer):

    class Meta:
        model = Contract
        fields = ["id", "contract_number", "contract_date", "expiration_date", "contract_cash", "payed_cash"]
        read_only_fields = ["id"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["contract_status"] = instance.contract_status.name
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
