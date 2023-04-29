from datetime import datetime

from rest_framework import serializers, status

from accounts.models import FizUser, YurUser

from accounts.serializers import FizUserSerializerForContractDetail, YurUserSerializerForContractDetail

from contracts.serializers import ServiceSerializerForContract

from expertiseService.models import (
    ExpertiseExpertSummary, ExpertiseContracts_Participants,
    ExpertiseServiceContract, ExpertiseServiceContractTarif,
    ExpertiseExpertSummaryDocument, ExpertisePkcs, ExpertiseTarif
)
from main.utils import responseErrorMessage
from one_c.models import PayedInformation


class ExpertiseTarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertiseTarif
        fields = '__all__'


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
        # userdata = UserData.objects.get(
        #     Q(role=obj.role),
        #     (Q(group=obj.contract.service.group) | Q(group=None))
        # )
        userdata = obj.participant_user
        if userdata.type == 2:
            user = YurUser.objects.get(userdata=userdata)
            return YurUserSerializerForContractDetail(user).data
        else:
            user = FizUser.objects.get(userdata=userdata)
            return FizUserSerializerForContractDetail(user).data

    def get_expert_summary(self, obj):
        try:
            # userdata = UserData.objects.get(
            #     Q(role=obj.role),
            #     (Q(group=obj.contract.service.group) | Q(group=None))
            # )

            userdata = obj.participant_user
            summary = ExpertiseExpertSummary.objects.get(
                contract=obj.contract, user=userdata)
            serializer = ExpertiseExpertSummarySerializer(summary)
            return serializer.data
        except ExpertiseExpertSummary.DoesNotExist:
            return {}

    def get_agreement_status(self, obj):
        return obj.agreement_status.name

    class Meta:
        model = ExpertiseContracts_Participants
        fields = '__all__'


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
        fields = ('id', 'service', 'contract_number', 'contract_date',
                  'contract_status', 'status', 'contract_cash', 'hashcode')


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
            client_id = ExpertiseServiceContract.objects.select_related(
                'client').get(id=obj.id).client
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
        fields = ["service", "contract_number", "contract_date",
                  "projects", "stir", "contract_cash", "price_select_percentage"]


class ExpertiseExpertSummarySerializerForSave(serializers.ModelSerializer):

    def create(self, validated_data):
        documents = self.context['documents']
        expertsummary = ExpertiseExpertSummary.objects.create(**validated_data)

        for document in documents:
            ExpertiseExpertSummaryDocument.objects.create(
                expertsummary=expertsummary,
                document=document
            )
        return expertsummary

    class Meta:
        model = ExpertiseExpertSummary
        fields = "__all__"


# Agar client sharnomani rejected qilsa
class ExpertiseSummarySerializerForRejected(serializers.ModelSerializer):

    class Meta:
        model = ExpertiseExpertSummary
        # "contract", "summary", "user", "user_role"]
        fields = ["comment", "date"]


class ExpertisePkcsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertisePkcs
        fields = '__all__'


# Serializer for monitoring contract
# class PayedInformationSerializer(serializers.ModelSerializer):
#     payed_percentage = serializers.SerializerMethodField()
#     month_name = serializers.SerializerMethodField()
#
#     class Meta:
#         model = PayedInformation
#         # fields = "__all__"
#         exclude = ["invoice"]
#
#     def get_payed_percentage(self, obj):
#         contract_cash = self.context.get("contract_cash")
#         if contract_cash is None:
#             responseErrorMessage(message=None, status_code=status.HTTP_400_BAD_REQUEST)
#         return (float(obj.payed_cash) * float(100)) / float(contract_cash)
#
#     @staticmethod
#     def get_month_name(obj):
#         date_object = datetime.fromisoformat(str(obj.payed_time))
#         return date_object.strftime("%B")


class ExpertiseMonitoringContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertiseServiceContract
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Customize the representation of your data here
        # payed_information_objects = PayedInformation.objects.filter(contract_code=instance.id_code)
        # representation['payed_information'] = PayedInformationSerializer(
        #     payed_information_objects, many=True, context={'contract_cash': instance.contract_cash}
        # ).data,

        representation["total_payed_percentage"] = instance.total_payed_percentage
        return representation
