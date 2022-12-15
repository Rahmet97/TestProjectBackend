from django.db.models import Q
from rest_framework import serializers

from accounts.models import YurUser, FizUser, UserData
from accounts.serializers import GroupSerializer, FizUserSerializer, YurUserSerializer, \
    YurUserSerializerForContractDetail, FizUserSerializerForContractDetail
from .models import Service, Tarif, Device, Contract, UserContractTarifDevice, UserDeviceCount, Offer, Document, \
    Element, TarifElement, SavedService, Pkcs, ExpertSummary, Contracts_Participants, ContractStatus, ConnetMethod, \
    ExpertSummaryDocument


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    need_documents = DocumentSerializer(many=True)
    group = GroupSerializer()
    user_type = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    def get_user_type(self, obj):
        if obj.user_type == 1:
            return "Jismoniy"
        elif obj.user_type == 2:
            return "Yuridik"
        else:
            return "Jismoniy va Yuridik"

    def get_is_saved(self, obj):
        try:
            request = self.context.get('request', None)
            print(request)
            saved_service = SavedService.objects.get(user=request.user)
            if obj in saved_service.services.all():
                return True
            else:
                return False
        except:
            return False

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'image', 'user_type', 'period', 'need_documents', 'group', 'is_saved')


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


class ContractSerializerForBackoffice(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    contract_status = ContractStatusSerializerForContractsList()

    def get_client(self, obj):
        try:
            client_id = Contract.objects.select_related('client').get(id=obj.id).client
            if client_id.type == 2:
                clientt = YurUser.objects.get(userdata=client_id)
                serializer = YurUserSerializer(clientt)
            else:
                clientt = FizUser.objects.get(userdata=client_id)
                serializer = FizUserSerializer(clientt)
        except Contract.DoesNotExist:
            return dict()

        return serializer.data

    def get_arrearage(self, obj):
        return obj.contract_cash - obj.payed_cash

    class Meta:
        model = Contract
        fields = (
            'id', 'client', 'contract_number', 'contract_date', 'expiration_date', 'contract_cash', 'payed_cash',
            'arrearage', 'contract_status')


class ContractSerializerForDetail(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    contract_status = ContractStatusSerializerForContractsList()

    def get_arrearage(self, obj):
        return obj.contract_cash - obj.payed_cash

    class Meta:
        model = Contract
        fields = (
            'id', 'contract_number', 'contract_date', 'expiration_date', 'contract_cash', 'payed_cash',
            'arrearage', 'contract_status', 'base64file', 'hashcode')


class UserContractTarifDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContractTarifDevice
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class UserDeviceCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceCount
        fields = '__all__'


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = '__all__'


class TarifElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarifElement
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
        expertsummary = ExpertSummary.objects.create(**validated_data)
        for document in documents:
            ExpertSummaryDocument.objects.create(
                expertsummary=expertsummary,
                document=document['document'],
                client_visible=document['client_visible']
            )
        return expertsummary

    class Meta:
        model = ExpertSummary
        fields = "__all__"


class ContractParticipantsSerializers(serializers.ModelSerializer):
    agreement_status = serializers.SerializerMethodField()
    userdata = serializers.SerializerMethodField()
    expert_summary = serializers.SerializerMethodField()

    def get_userdata(self, obj):
        userdata = UserData.objects.get(Q(role=obj.role), Q(group=obj.contract.service.group))
        if userdata.type == 2:
            u = YurUser.objects.get(userdata=userdata)
            user = YurUserSerializerForContractDetail(u)
        else:
            u = FizUser.objects.get(userdata=userdata)
            user = FizUserSerializerForContractDetail(u)
        return user.data

    def get_expert_summary(self, obj):
        try:
            userdata = UserData.objects.get(Q(role=obj.role), Q(group=obj.contract.service.group))
            summary = ExpertSummary.objects.filter(contract=obj.contract).get(user=userdata)
            serializer = ExpertSummarySerializer(summary)
            return serializer.data
        except ExpertSummary.DoesNotExist:
            return dict()

    def get_agreement_status(self, obj):
        return obj.agreement_status.name

    class Meta:
        model = Contracts_Participants
        fields = '__all__'
