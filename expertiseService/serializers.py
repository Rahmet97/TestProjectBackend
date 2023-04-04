from django.db.models import Q
from rest_framework import serializers

from accounts.models import UserData, FizUser, YurUser

from accounts.serializers import FizUserSerializerForContractDetail, YurUserSerializerForContractDetail

from contracts.serializers import ServiceSerializerForContract

from expertiseService.models import (
    ExpertiseExpertSummary, ExpertiseContracts_Participants,
    ExpertiseServiceContract, ExpertiseServiceContractTarif
)


class ExpertiseContractSerializerForDetail(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    contract_status = serializers.SerializerMethodField()

    def get_arrearage(self, obj):
        return obj.contract_cash - obj.payed_cash
    

    def get_status(self, obj):
        return obj.get_status_display()

    def get_contract_status(self, obj):
        return obj.get_contract_status_display()

    class Meta:
        model = ExpertiseServiceContract
        fields = (
            'id', 'contract_number', 'contract_date', 'expiration_date', 
            'contract_cash', 'payed_cash', 'arrearage', 'contract_status',
            'base64file', 'hashcode', 'status'
        )


class ExpertiseExpertSummarySerializer(serializers.ModelSerializer):
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
        model = ExpertiseExpertSummary
        fields = "__all__"


class ExpertiseContractParticipantsSerializers(serializers.ModelSerializer):
    agreement_status = serializers.SerializerMethodField()
    userdata = serializers.SerializerMethodField()
    expert_summary = serializers.SerializerMethodField()

    def get_userdata(self, obj):
        userdata = UserData.objects.get(
            Q(role=obj.role),
            # (Q(group=obj.contract.service.group) | Q(group=None))
        )
        if userdata.type == 2:
            user = YurUser.objects.get(userdata=userdata)
            return YurUserSerializerForContractDetail(user).data
        else:
            user = FizUser.objects.get(userdata=userdata)
            return FizUserSerializerForContractDetail(user).data

    def get_expert_summary(self, obj):
        try:
            userdata = UserData.objects.get(Q(role=obj.role), Q(group=obj.contract.service.group))
            summary = ExpertiseExpertSummary.objects.get(contract=obj.contract, user=userdata)
            serializer = ExpertiseExpertSummarySerializer(summary)
            return serializer.data
        except ExpertiseExpertSummary.DoesNotExist:
            return {}

    def get_agreement_status(self, obj):
        return obj.agreement_status.name

    class Meta:
        model = ExpertiseContracts_Participants
        fields = '__all__'


# class ExpertiseContractParticipantsSerializers(serializers.ModelSerializer):
#     agreement_status = serializers.SerializerMethodField()
#     userdata = serializers.SerializerMethodField()
#     expert_summary = serializers.SerializerMethodField()

#     def get_userdata(self, obj):
#         if obj.role.name != "dasturchi" and obj.role.name != 'mijoz':
#             userdata = UserData.objects.get(
#                 Q(role=obj.role), 
#                 (Q(group=obj.contract.service.group) | Q(group=None))
#             )
            
#             if userdata.type == 2:
#                 u = YurUser.objects.get(userdata=userdata)
#                 user = YurUserSerializerForContractDetail(u)
#             else:
#                 u = FizUser.objects.get(userdata=userdata)
#                 user = FizUserSerializerForContractDetail(u)
#             return user.data
        
#         return None

#     def get_expert_summary(self, obj):
#         try:
#             userdata = UserData.objects.get(Q(role=obj.role), Q(group=obj.contract.service.group))
#             summary = ExpertiseExpertSummary.objects.filter(contract=obj.contract).get(user=userdata)
#             serializer = ExpertiseExpertSummarySerializer(summary)
#             return serializer.data
#         except:
#             return dict()

#     def get_agreement_status(self, obj):
#         return obj.agreement_status.name

#     class Meta:
#         model = ExpertiseContracts_Participants
#         fields = '__all__'


class ExpertiseContractSerializerForContractList(serializers.ModelSerializer):
    service = ServiceSerializerForContract()
    status = serializers.SerializerMethodField()
    contract_status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_contract_status(self, obj):
        return obj.get_contract_status_display()

    class Meta:
        model = ExpertiseServiceContract
        fields = ('id', 'service', 'contract_number', 'contract_date', 'contract_status', 'status', 'contract_cash', 'hashcode')


class ExpertiseContractSerializerForBackoffice(serializers.ModelSerializer):
    arrearage = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    contract_status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_contract_status(self, obj):
        return obj.get_contract_status_display()

    def get_client(self, obj):
        try:
            client_id = ExpertiseServiceContract.objects.select_related('client').get(id=obj.id).client
            if client_id.type == 2:
                clientt = YurUser.objects.get(userdata=client_id)
                serializer = YurUserSerializerForContractDetail(clientt)
            else:
                clientt = FizUser.objects.get(userdata=client_id)
                serializer = FizUserSerializerForContractDetail(clientt)
        except ExpertiseServiceContract.DoesNotExist:
            return dict()

        return serializer.data

    def get_arrearage(self, obj):
        return obj.contract_cash - obj.payed_cash

    class Meta:
        model = ExpertiseServiceContract
        fields = (
            'id', 'client', 'contract_number', 'contract_date', 'expiration_date', 'contract_cash',
            'payed_cash', 'arrearage', 'contract_status', 'status'
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
        fields = ["service", "contract_number", "contract_date", "projects", "stir", "contract_cash", "price_select_percentage"]
