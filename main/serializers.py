from datetime import datetime, timedelta

from django.db.models import Q
from rest_framework import serializers

from main.models import Application, TestFileUploader

from contracts.models import Contract, Contracts_Participants
from expertiseService.models import ExpertiseServiceContract, ExpertiseContracts_Participants
from vpsService.models import VpsServiceContract, VpsContracts_Participants

from accounts.models import FizUser, YurUser, Role
from accounts.serializers import FizUserForOldContractSerializers, YurUserSerializerForContractDetail


class GetFilterNotificationCountSerializer(serializers.Serializer):

    def get_colocation(self):
        user = self.context['request'].user
        # new
        if user.role.name == Role.RoleNames.DIRECTOR:
            contract_participants_query_filter = (
                    Q(role__name=Role.RoleNames.DEPARTMENT_BOSS) & Q(agreement_status__name='Kelishildi')
            )
            contract_participants = Contracts_Participants.objects.filter(
                contract_participants_query_filter
            ).values('contract')

            director_accepted_contracts_query_filter = (
                    Q(role__name=Role.RoleNames.DIRECTOR) & Q(agreement_status__name='Kelishildi')
            )
            director_accepted_contracts = Contracts_Participants.objects.filter(
                director_accepted_contracts_query_filter
            ).values('contract')

            new_data_query_filter = (
                    Q(id__in=contract_participants) &
                    Q(contract_status__name="Yangi")
            )
            new_data_exclude_query_filter = (
                    Q(id__in=director_accepted_contracts) |
                    Q(id__in=contract_participants) & Q(contract_date__lt=datetime.now() - timedelta(days=1))
                # mudati o'tgan
            )
            new_data = Contract.objects.filter(
                new_data_query_filter
            ).exclude(
                new_data_exclude_query_filter
            ).select_related()
        else:
            contract_participants_query_filter = (
                    Q(role=user.role) &
                    (Q(agreement_status__name='Yuborilgan') | Q(agreement_status__name="Ko'rib chiqilmoqda"))
            )
            contract_participants = Contracts_Participants.objects.filter(
                contract_participants_query_filter
            ).values('contract')

            new_data_query_filter = Q(id__in=contract_participants) & Q(contract_status__name="Yangi")
            new_data_exclude_query_filter = (
                    Q(contract_status__name="Bekor qilingan") |
                    Q(contract_status__name="Rad etilgan") |
                    Q(id__in=contract_participants) & Q(contract_date__lt=datetime.now() - timedelta(days=1))
                # mudati o'tgan
            )
            new_data = Contract.objects.filter(
                new_data_query_filter
            ).exclude(
                new_data_exclude_query_filter
            ).select_related()

        # expired
        contract_participants_query_filter = (
                Q(role=user.role) &
                (
                        Q(agreement_status__name='Yuborilgan') |
                        Q(agreement_status__name="Ko'rib chiqilmoqda")
                )
        )
        contract_participants = Contracts_Participants.objects.filter(
            contract_participants_query_filter
        ).values('contract')
        expired_data_query_filter = (
                Q(id__in=contract_participants) &
                Q(contract_date__lt=datetime.now() - timedelta(days=1)) &
                Q(contract_status__name='Yangi')
        )
        expired_data_exclude_query_filter = (
                Q(contract_status__name='Bekor qilingan') |
                Q(contract_status__name="Rad etilgan")
        )
        expired_data = Contract.objects.filter(expired_data_query_filter).select_related().exclude(
            expired_data_exclude_query_filter
        )

        return new_data.count(), expired_data.count()

    def get_expertise(self):
        user = self.context['request'].user

        all_data = ExpertiseServiceContract.objects.all()

        # new contrasts
        if user.role.name == Role.RoleNames.DIRECTOR:
            contract_participants = ExpertiseContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DEPUTY_DIRECTOR),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')

            director_accepted_contracts = ExpertiseContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DIRECTOR), Q(agreement_status__name='Kelishildi')
            ).values('contract')

            new_data = all_data.filter(
                Q(id__in=contract_participants) | Q(is_confirmed_contract=1),
                Q(contract_status=1)
            ).exclude(
                Q(id__in=director_accepted_contracts),
                Q(contract_status=5),  # REJECTED
                Q(contract_status=6),  # CANCELLED
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related().order_by('-contract_date')
        else:
            contract_participants = ExpertiseContracts_Participants.objects.filter(
                Q(role=user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            new_data = all_data.filter(
                id__in=contract_participants,
                contract_status=1
            ).exclude(
                Q(contract_status=5) | Q(contract_status=6),  # REJECTED, CANCELLED
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related().order_by('-contract_date')

        # expired contracts
        # Retrieve contract IDs where the user's role matches and agreement_status is 'Kelishildi'
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            role=user.role,
            agreement_status__name__in=['Yuborilgan', "Ko'rib chiqilmoqda"]
        ).values_list('contract', flat=True)

        expired_data = all_data.filter(
            id__in=contract_participants,
            contract_date__lt=datetime.now() - timedelta(days=1),
            contract_status=1
        ).select_related().exclude(
            contract_status__in=[5, 6]  # REJECTED, CANCELLED
        )

        return new_data.count(), expired_data.count()

    def get_vps(self):
        user = self.context['request'].user
        # all contracts
        all_data = VpsServiceContract.objects.order_by('-contract_date')

        # new contracts
        if user.role.name == Role.RoleNames.DIRECTOR:
            contract_participants = VpsContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DEPUTY_DIRECTOR),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')

            director_accepted_contracts = VpsContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DIRECTOR), Q(agreement_status__name='Kelishildi')
            ).values('contract')

            new_data = all_data.filter(
                Q(id__in=contract_participants) | Q(is_confirmed_contract=1),
                Q(contract_status=1)
            ).exclude(
                Q(id__in=director_accepted_contracts),
                Q(contract_status=5),  # REJECTED
                Q(contract_status=6),  # CANCELLED
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related()
        else:
            contract_participants = VpsContracts_Participants.objects.filter(
                Q(role=user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            new_data = all_data.filter(
                id__in=contract_participants,
                contract_status=1
            ).exclude(
                Q(contract_status=5) | Q(contract_status=6),  # REJECTED, CANCELLED
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related()

        # expired contracts
        # Retrieve contract IDs where the user's role matches and agreement_status is 'Kelishildi'
        contract_participants = VpsContracts_Participants.objects.filter(
            role=user.role,
            agreement_status__name__in=['Yuborilgan', "Ko'rib chiqilmoqda"]
        ).values_list('contract', flat=True)

        expired_data = all_data.filter(
            id__in=contract_participants,
            contract_date__lt=datetime.now() - timedelta(days=1),
            contract_status=1
        ).select_related().exclude(
            contract_status__in=[5, 6]  # REJECTED, CANCELLED
        ).order_by('-contract_date')

        return new_data.count(), expired_data.count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["colocation"] = {}
        rep["colocation"]["new"], rep["colocation"]["expired"] = self.get_colocation()

        rep["expertise"]={}
        rep["expertise"]["new"], rep["expertise"]["expired"] = self.get_expertise()

        rep["vps"]={}
        rep["vps"]["new"], rep["vps"]["expired"] = self.get_vps()
        return rep


class TestFileUploaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestFileUploader
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    service = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = ["pk", "user", "service", "name", "phone", "email", "message", "created_at", "file", "is_contracted"]

    @staticmethod
    def get_user(obj):
        user_obj = obj.user
        if user_obj.type == 1:  # fiz
            serializer = FizUserForOldContractSerializers(FizUser.objects.get(userdata=user_obj))
            data = serializer.data
            data['u_type'] = 'Fizik'
        else:
            serializer = YurUserSerializerForContractDetail(YurUser.objects.get(userdata=user_obj))
            data = serializer.data
            data['u_type'] = 'Yuridik'
        return data

    @staticmethod
    def get_service(obj):
        return {
            "pk": obj.service.pk,
            "name": obj.service.name
        }
