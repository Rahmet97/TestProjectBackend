import os
import json
import base64
import logging
import hashlib
import requests
import xmltodict
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
# from django.views.decorators.cache import cache_page

from drf_yasg.utils import swagger_auto_schema

from rest_framework import response, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import WorkerPermission
from contracts.models import Participant, Service
from contracts.tasks import file_downloader
from contracts.permission import IsAuthenticatedAndOwner
from contracts.utils import (
    NumbersToWord, render_to_pdf, error_response_500,
    delete_file, create_qr
)

from accounts.models import YurUser, UserData, Role
from accounts.serializers import YurUserSerializerForContractDetail

from main.models import Application
from main.permission import MonitoringPermission
from main.utils import responseErrorMessage

from expertiseService.permission import IsRelatedToExpertiseBackOffice, ExpertiseConfirmContractPermission
from expertiseService.models import (
    AgreementStatus, ExpertiseContracts_Participants,
    ExpertiseServiceContract, ExpertiseTarifContract,
    ExpertiseServiceContractTarif, ExpertiseExpertSummary,
    ExpertisePkcs, ExpertiseTarif
)
from expertiseService.serializers import (
    ExpertiseServiceContractSerializers,
    ExpertiseContractSerializerForDetail,
    ExpertiseContractParticipantsSerializers,
    ExpertiseContractSerializerForContractList,
    ExpertiseExpertSummarySerializerForSave,
    ExpertiseSummarySerializerForRejected,
    ExpertisePkcsSerializer, ExpertiseTarifSerializer, ExpertiseServiceContractProjects,
    ExpertiseMonitoringContractSerializer, GroupContractSerializerForBackoffice
)

logger = logging.getLogger(__name__)
num2word = NumbersToWord()


# Back office APIs
class CreateExpertiseServiceContractView(APIView):
    queryset = ExpertiseServiceContract.objects.all()
    permission_classes = [IsAuthenticated]

    @staticmethod
    def generate_hash_code(text: str):
        hashcode = hashlib.md5(text.encode())
        hash_code = hashcode.hexdigest()
        return hash_code

    @staticmethod
    def create_contract_participants(service_id: int, exclude_role=None):
        participants = Participant.objects.get(service_id=service_id).participants.all().exclude(name=exclude_role)
        users = []
        service_group = Service.objects.get(id=service_id).group
        for role in participants:

            query = Q(role=role) & (Q(group__in=[service_group]) | Q(group=None))
            matching_user = UserData.objects.filter(query).last()

            if matching_user is not None:
                users.append(matching_user)
            else:
                logger.error("84 -> No matching user found")

        return users

    def post(self, request):
        context = dict()
        request_objects_serializers = ExpertiseServiceContractSerializers(data=request.data)
        request_objects_serializers.is_valid(raise_exception=True)

        context['u_type'] = 'yuridik'
        context["user_obj"] = YurUser.objects.get(tin=request_objects_serializers.validated_data.get("stir"))
        context['contract_number'] = request_objects_serializers.validated_data.get("contract_number")

        date = request_objects_serializers.validated_data.get("contract_date")
        context['datetime'] = datetime.fromisoformat(str(date)).strftime('%d.%m.%Y')

        context['price'] = request_objects_serializers.validated_data.get("contract_cash")
        context['price_text'] = num2word.change_num_to_word(int(context['price']))

        context['withoutnds_price'] = float(context['price']) * 0.88
        context['withoutnds_price_text'] = num2word.change_num_to_word(int(context['withoutnds_price']))

        context['onlynds_price'] = float(context['price']) * 0.12
        context['onlynds_price_text'] = num2word.change_num_to_word(int(context['onlynds_price']))

        context['price_select_percentage'] = request_objects_serializers.validated_data.get('price_select_percentage')
        context['price_select_percentage_text'] = num2word.change_num_to_word(int(context['price_select_percentage']))

        context['tarif'] = request_objects_serializers.validated_data.get("projects")

        context['host'] = 'http://' + request.META['HTTP_HOST']
        context['qr_code'] = ''
        context['save'] = False
        context['page_break'] = False
        # context['save'] = True
        # context['page_break'] = True

        if int(request.data['save']):
            context['save'] = True
            context['page_break'] = True

            hash_code = self.generate_hash_code(
                text=f"{context.get('user_obj').get_director_short_full_name}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
            )

            link = 'http://' + request.META['HTTP_HOST'] + f'/expertise/contract/{hash_code}'
            qr_code_path = create_qr(link)
            context['hash_code'] = hash_code
            context['qr_code'] = f"http://api2.unicon.uz/media/qr/{hash_code}.png"

            # Contract yaratib olamiz bazada id_code olish uchun
            user_stir = request_objects_serializers.validated_data.pop('stir')
            projects_data = request_objects_serializers.validated_data.pop('projects')

            client = UserData.objects.get(username=user_stir)
            expertise_service_contract = ExpertiseServiceContract.objects.create(
                **request_objects_serializers.validated_data,
                service_id=int(request.data['service_id']),
                client=client,
                status=4,
                contract_status=1,  # new
                payed_cash=0,
                # base64file=base64code,
                hashcode=hash_code,
                # like_preview_pdf=like_preview_pdf_path
            )
            expertise_service_contract.save()

            context['id_code'] = expertise_service_contract.id_code

            # rendered html file
            contract_file_for_base64_pdf = None
            template_name = "shablonEkspertiza.html"
            pdf = render_to_pdf(template_src=template_name, context_dict=context)
            if pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                contract_file_for_base64_pdf = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
                with open(contract_file_for_base64_pdf, 'wb') as f:
                    f.write(pdf.content)
            else:
                error_response_500()

            if contract_file_for_base64_pdf is None:
                error_response_500()

            contract_file = open(contract_file_for_base64_pdf, 'rb').read()
            base64code = base64.b64encode(contract_file)

            # pdf fileni ochirish
            delete_file(contract_file_for_base64_pdf)
            # qr_code fileni ochirish
            delete_file(qr_code_path)

            # preview ni bazaga ham saqlab ketishim kk chunki contractni statusiga qarab foydalanish uchun
            context['save'] = False
            # context['save'] = True
            like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)

            like_preview_pdf_path = None
            if like_preview_pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
                with open(like_preview_pdf_path, 'wb') as f:
                    f.write(like_preview_pdf.content)
            if like_preview_pdf_path is None:
                error_response_500()

            expertise_service_contract.base64file = base64code
            expertise_service_contract.like_preview_pdf = like_preview_pdf_path
            expertise_service_contract.save()

            for project_data in projects_data:
                project = ExpertiseServiceContractTarif.objects.create(**project_data)
                ExpertiseTarifContract.objects.create(
                    contract=expertise_service_contract,
                    tarif=project
                )

            # ExpertiseContracts_Participants
            # if the amount of the contract is less than 10 million,
            # the director will not participate as a participant
            exclude_role = None
            if expertise_service_contract.contract_cash < 10_000_000:
                exclude_role = Role.RoleNames.DIRECTOR

            service_id = int(request.data['service'])
            participants = self.create_contract_participants(service_id=service_id, exclude_role=exclude_role)
            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()

            for participant in participants:
                ExpertiseContracts_Participants.objects.create(
                    contract=expertise_service_contract,
                    role=participant.role,
                    participant_user=participant,
                    agreement_status=agreement_status
                ).save()

            # After the contract is created, the application is_contracted=True
            application_pk = request.data.get("application_pk")
            Application.objects.filter(pk=application_pk).update(is_contracted=True)

            return response.Response(data={"message": "Created Expertise Service Contract"}, status=201)
            # return render(request=request, template_name=template_name, context=context)

        template_name = "shablonEkspertiza.html"
        return render(request=request, template_name=template_name, context=context)


class ExpertiseGetGroupContract(APIView):
    permission_classes = [IsRelatedToExpertiseBackOffice]

    def get(self, request):

        # barcha contractlar
        barcha_data = ExpertiseServiceContract.objects.order_by('-contract_date')
        self.check_object_permissions(request=request, obj=barcha_data)
        barcha = GroupContractSerializerForBackoffice(barcha_data, many=True)

        # yangi contractlar
        if request.user.role.name == Role.RoleNames.DIRECTOR:
            contract_participants = ExpertiseContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DEPUTY_DIRECTOR),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')

            director_accepted_contracts = ExpertiseContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DIRECTOR), Q(agreement_status__name='Kelishildi')
            ).values('contract')

            yangi_data = barcha_data.filter(
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
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            yangi_data = barcha_data.filter(
                id__in=contract_participants,
                contract_status=1
            ).exclude(
                Q(contract_status=5) | Q(contract_status=6),  # REJECTED, CANCELLED
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=yangi_data)
        yangi = GroupContractSerializerForBackoffice(yangi_data, many=True)

        # kelishilgan contractlar
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            role=request.user.role,
            agreement_status__name='Kelishildi'
        ).values_list('contract', flat=True)

        # Retrieve contracts with the matching IDs, order by contract_date and prefetch related data
        kelishilgan_data = barcha_data.filter(
            id__in=contract_participants
        ).exclude(
            contract_status__in=[1, 5, 6, 7]  # List of contract_status values to exclude
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=kelishilgan_data)
        kelishilgan = GroupContractSerializerForBackoffice(kelishilgan_data, many=True)

        # rad etilgan contractlar
        rejected_cancelled_data = barcha_data.filter(
            contract_status__in=[5, 6]  # REJECTED, CANCELLED
        ).order_by('-contract_date')
        self.check_object_permissions(request=request, obj=rejected_cancelled_data)
        rad_etildi = GroupContractSerializerForBackoffice(rejected_cancelled_data, many=True)

        # expired contracts
        # Retrieve contract IDs where the user's role matches and agreement_status is 'Kelishildi'
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            role=request.user.role,
            agreement_status__name__in=['Yuborilgan', "Ko'rib chiqilmoqda"]
        ).values_list('contract', flat=True)

        expired_data = barcha_data.filter(
            id__in=contract_participants,
            contract_date__lt=datetime.now() - timedelta(days=1),
            contract_status=1
        ).select_related().exclude(
            contract_status__in=[5, 6]  # REJECTED, CANCELLED
        ).order_by('-contract_date')

        self.check_object_permissions(request=request, obj=expired_data)
        expired = GroupContractSerializerForBackoffice(expired_data, many=True)

        # last day contracts
        today = datetime.now()
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            role=request.user.role,
            agreement_status__name__in=['Yuborilgan', "Ko'rib chiqilmoqda"]
        ).values_list('contract', flat=True)

        lastday_data = barcha_data.filter(
            id__in=contract_participants,
            contract_date__date=today.date()
        ).exclude(
            contract_status__in=[5, 6]
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=lastday_data)
        lastday = GroupContractSerializerForBackoffice(lastday_data, many=True)

        # expired accepted contracts
        contract_participants = ExpertiseContracts_Participants.objects.filter(
            role=request.user.role,
            agreement_status__name='Kelishildi'
        ).values_list('contract', flat=True)

        expired_accepted_data = barcha_data.filter(
            id__in=contract_participants,
            contract_date__lt=datetime.now() - timedelta(days=1)
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=expired_accepted_data)
        expired_accepted = GroupContractSerializerForBackoffice(expired_accepted_data, many=True)

        # in_time contracts
        # Retrieve contracts based on the specified conditions and ordering
        contracts_selected = ExpertiseExpertSummary.objects.select_related('contract').filter(
            user=request.user
        ).order_by('-contract', '-contract__contract_date')
        # Filter the contracts that are in time based on the date comparison
        in_time_data = [
            element.contract for element in contracts_selected
            if element.contract.contract_date < element.date <= element.contract.contract_date + timedelta(days=1)
        ]
        self.check_object_permissions(request=request, obj=in_time_data)
        in_time = GroupContractSerializerForBackoffice(in_time_data, many=True)

        return response.Response(
            data={
                'barcha': barcha.data,
                'yangi': yangi.data,
                'kelishildi': kelishilgan.data,
                'rad_etildi': rad_etildi.data,
                'expired': expired.data,
                'lastday': lastday.data,
                'expired_accepted': expired_accepted.data,
                'in_time': in_time.data
            },
            status=200
        )


class ExpertiseConfirmContract(APIView):
    permission_classes = (ExpertiseConfirmContractPermission,)

    def post(self, request):
        contract = get_object_or_404(ExpertiseServiceContract, pk=int(request.data['contract']))

        if int(request.data['summary']) == 1:  # 1 -> muofiq, 0 -> muofiq emas
            agreement_status = AgreementStatus.objects.get(name='Kelishildi')
        else:
            agreement_status = AgreementStatus.objects.get(name='Rad etildi')
            contract.contract_status = 5  # REJECTED
            if contract.contract_cash >= 10_000_000:
                director_participants = ExpertiseContracts_Participants.objects.get(
                    Q(role__name=Role.RoleNames.DIRECTOR),
                    Q(contract=contract),
                )
                director_participants.agreement_status = agreement_status
                director_participants.save()

        contracts_participants = ExpertiseContracts_Participants.objects.get(
            Q(role=request.user.role),
            Q(contract=contract),
            Q(participant_user=request.user)
        )

        if contracts_participants is None or contracts_participants.participant_user != request.user:
            responseErrorMessage(
                message="you are not contract's participant",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        contracts_participants.agreement_status = agreement_status
        contracts_participants.save()

        # If the amount of the contract is more than 10 million,
        # it expects the director to give a conclusion
        director_role_name = \
            Role.RoleNames.DIRECTOR if contract.contract_cash >= 10_000_000 else Role.RoleNames.DEPUTY_DIRECTOR
        try:
            cntrct = ExpertiseContracts_Participants.objects.get(
                contract=contract,
                role__name=director_role_name,
                agreement_status__name='Kelishildi'
            )
        except ExpertiseContracts_Participants.DoesNotExist:
            cntrct = None

        if cntrct:
            contract.is_confirmed_contract = 2  # UNICON_CONFIRMED
            contract.contract_status = 2  # CUSTOMER_SIGNATURE_IS_EXPECTED

        contract.save()

        request.data._mutable = True
        request.data['user'] = request.user.id
        documents = request.FILES.getlist('documents', None)

        summary = ExpertiseExpertSummarySerializerForSave(
            data=request.data, context={'documents': documents}
        )
        summary.is_valid(raise_exception=True)
        summary.save()

        return response.Response(status=200)


# Front office APIs -> client request user
class ExpertiseGetUserContracts(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contracts = ExpertiseServiceContract.objects.filter(client=request.user).order_by('-id')
        serializer = ExpertiseContractSerializerForContractList(contracts, many=True)
        return response.Response(serializer.data)


# General APIs
class ExpertiseContractDetail(APIView):
    permission_classes = (IsAuthenticated,)
    permitted_roles = [
        Role.RoleNames.ADMIN,
        Role.RoleNames.ACCOUNTANT,
        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,
    ]

    def get(self, request, pk):
        client = None
        contract = ExpertiseServiceContract.objects.select_related('client').get(pk=pk)
        contract_serializer = ExpertiseContractSerializerForDetail(contract)

        # agar request user mijoz bo'lsa
        if request.user.role.name == Role.RoleNames.CLIENT and contract.client == request.user:
            client = request.user

        # agar reuqest user role permitted_roles tarkibida bo'lsa
        elif request.user.role.name in self.permitted_roles:
            client = contract.client
            participant = ExpertiseContracts_Participants.objects.filter(
                contract=contract,
                role=request.user.role,
                participant_user=request.user,
                agreement_status__name="Yuborilgan"
            ).last()
            if participant:
                participant.agreement_status = AgreementStatus.objects.get(name="Ko'rib chiqilmoqda")
                participant.save()
        else:
            responseErrorMessage(message="You are not permitted to view this contact detail", status_code=200)

        user = YurUser.objects.get(userdata=client)
        client_serializer = YurUserSerializerForContractDetail(user)
        participants = ExpertiseContracts_Participants.objects.filter(contract=contract).order_by('role_id')

        participant_serializer = ExpertiseContractParticipantsSerializers(participants, many=True)

        try:
            expert_summary = ExpertiseExpertSummary.objects.filter(
                Q(contract=contract),
                Q(user=request.user),
                (Q(user__group__in=request.user.group.all()) | Q(user__group=None))
            ).distinct()
            expert_summary_value = expert_summary[0].summary if expert_summary.exists() else 0

        except (ExpertiseExpertSummary.DoesNotExist, IndexError):
            expert_summary_value = 0

        projects_obj = ExpertiseServiceContractTarif.objects.filter(expertisetarifcontract__contract=contract)
        projects_obj_serializer = ExpertiseServiceContractProjects(projects_obj, many=True)
        return response.Response(data={
            'contract': contract_serializer.data,
            'client': client_serializer.data,
            'participants': participant_serializer.data,
            'projects': projects_obj_serializer.data,
            'is_confirmed': True if int(expert_summary_value) == 1 else False
        }, status=200)


class ExpertiseGetContractFile(APIView):
    permission_classes = ()

    def get(self, request, hash_code):
        if hash_code is None:
            return response.Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)

        contract = get_object_or_404(ExpertiseServiceContract, hashcode=hash_code)
        if contract.contract_status == 4 or contract.contract_status == 3:  # PAYMENT_IS_PENDING ACTIVE
            # delete like pdf file test mode
            if contract.like_preview_pdf:
                delete_file(contract.like_preview_pdf.path)
                contract.like_preview_pdf = None
                contract.save()

            file_pdf_path, pdf_file_name = file_downloader(
                base64file=bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'),
                pk=contract.id,
            )
            if os.path.exists(file_pdf_path):
                with open(file_pdf_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/pdf")
                    response['Content-Disposition'] = f'attachment; filename={contract.contract_number}.pdf'
                    delete_file(file_pdf_path)
                    return response
        else:
            if contract.like_preview_pdf:
                # Open the file and create a response with the PDF data
                with open(contract.like_preview_pdf.path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={contract.contract_number}.pdf'
                    return response

        return response.Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)


class ExpertiseTarifListAPIView(generics.ListCreateAPIView):
    queryset = ExpertiseTarif.objects.all()
    serializer_class = ExpertiseTarifSerializer
    permission_classes = (IsAuthenticated,)


class ExpertiseTarifUpdateAPIView(APIView):
    serializer_class = ExpertiseTarifSerializer
    permission_classes = (IsAuthenticated,)

    def patch(self, request, tarif_id):
        queryset = ExpertiseTarif.objects.get(pk=tarif_id)
        serializer = self.serializer_class(queryset, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(data={"message": "Object successfully update"}, status=status.HTTP_200_OK)


# Agar client sharnomani rejected qilsa
class ExpertiseContractRejectedViews(APIView):
    serializer_class = ExpertiseSummarySerializerForRejected
    permission_classes = [IsAuthenticatedAndOwner]

    @swagger_auto_schema(
        operation_summary="Front Officeda Expertisada. clientga yaratilgan shartnomani bekor qilish uchun")
    def post(self, request, contract_id):
        contract = get_object_or_404(ExpertiseServiceContract, pk=contract_id)
        self.check_object_permissions(self.request, contract)
        if contract.contract_status != 6:  # CANCELLED
            serializer = self.serializer_class(data=request.data)

            serializer.is_valid(raise_exception=True)
            contract.contract_status = 6  # CANCELLED
            contract.save()

            serializer.save(
                summary=0,
                user=request.user,
                contract=contract,
                user_role=request.user.role
            )
            return response.Response({"message": f"Rejected Contract id: {contract_id}"}, status=201)
        responseErrorMessage(message="you are already rejected contract", status_code=200)


class ExpertiseSavePkcs(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ExpertisePkcsSerializer

    def join2pkcs(self, pkcs7_1, pkcs7_2):
        xml = f"""
            <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                <Body>
                    <join2Pkcs7Attached xmlns="http://v1.pkcs7.plugin.server.dsv.eimzo.yt.uz/">
                        <pkcs7AttachedB64A xmlns="">{pkcs7_1}</pkcs7AttachedB64A>
                        <pkcs7AttachedB64B xmlns="">{pkcs7_2}</pkcs7AttachedB64B>
                    </join2Pkcs7Attached>
                </Body>
            </Envelope>
            """
        headers = {'Content-Type': 'text/xml'}  # set what your server accepts
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1',
                            data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        pkcs7_12 = dict_data['S:Envelope']['S:Body']['ns2:join2Pkcs7AttachedResponse']['return']
        d = json.loads(pkcs7_12)
        return d

    def verifyPkcs(self, pkcs):
        xml = f"""
            <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                <Body>
                    <verifyPkcs7 xmlns="http://v1.pkcs7.plugin.server.dsv.eimzo.yt.uz/">
                        <pkcs7B64 xmlns="">{pkcs}</pkcs7B64>
                    </verifyPkcs7>
                </Body>
            </Envelope>
        """
        headers = {'Content-Type': 'text/xml'}  # set what your server accepts
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1', data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        res = dict_data['S:Envelope']['S:Body']['ns2:verifyPkcs7Response']['return']
        return json.loads(res)

    def post(self, request):
        contract_id = int(request.data['contract_id'])
        pkcs7 = request.data['pkcs7']
        try:
            contract = ExpertiseServiceContract.objects.get(pk=contract_id)
            # if request.user.role in ExpertiseContracts_Participants.objects.filter(contract=contract).values('role'):
            role_names = ExpertiseContracts_Participants.objects.filter(
                contract=contract
            ).values_list('role__name', flat=True)
            # if request.user.role.name in Contracts_Participants.objects.filter(contract=contract).values('role'):
            if request.user.role.name in role_names or request.user.role.name == Role.RoleNames.CLIENT:
                if not ExpertisePkcs.objects.filter(contract=contract).exists():
                    pkcs = ExpertisePkcs.objects.create(contract=contract, pkcs7=pkcs7)
                    pkcs.save()
                else:
                    pkcs_exist_object = ExpertisePkcs.objects.get(contract=contract)
                    client_pkcs = pkcs_exist_object.pkcs7
                    new_pkcs7 = self.join2pkcs(pkcs7, client_pkcs)
                    pkcs_exist_object.pkcs7 = new_pkcs7
                    pkcs_exist_object.save()
            if request.user == contract.client:
                contract.contract_status = 3  # PAYMENT_IS_PENDING
                contract.is_confirmed_contract = 3  # CLIENT_CONFIRMED
                contract.save()
        except ExpertiseServiceContract.DoesNotExist:
            return response.Response({'message': 'Bunday shartnoma mavjud emas'})
        return response.Response({'message': 'Success'})


class ExpertiseMonitoringContractViews(APIView):
    permission_classes = [MonitoringPermission]

    @staticmethod
    def get_objects(
            query_year=None, contract_number=None,
            id_code=None, contract_date=None,
            client_type=None, pin=None, tin=None,
            contract_cash=None
    ):
        # create an empty query object
        query = Q()
        # add more filter criteria to the query object using the | (OR) operator
        if contract_number:
            query |= Q(contract_number=contract_number)

        if id_code:
            query |= Q(id_code=id_code)

        if contract_date:
            query |= Q(contract_date=contract_date)

        if client_type:  # FIZ = 1 YUR = 2
            query |= Q(client__type=client_type)

        if pin:
            query |= Q(client__username=pin)

        if tin:
            query |= Q(client__username=tin)

        if contract_cash:
            query |= Q(contract_cash=contract_cash)

        if query_year:
            query |= Q(contract_date__year=query_year)

        # execute the query and retrieve the matching books
        contracts = ExpertiseServiceContract.objects.filter(query).order_by("-id")
        return contracts

    def get(self, request):
        contracts = self.get_objects(
            query_year=request.GET.get("year"),
            contract_number=request.GET.get("contract_number"),
            id_code=request.GET.get("id_code"),
            contract_date=request.GET.get("contract_date"),
            client_type=request.GET.get("client_type"),
            pin=request.GET.get("pin"),
            tin=request.GET.get("tin"),
            contract_cash=request.GET.get("contract_cash"),
        )
        serializer = ExpertiseMonitoringContractSerializer(contracts, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


class ExpertiseMonitoringContractDetailViews(generics.RetrieveAPIView):
    queryset = ExpertiseServiceContract.objects.all()
    serializer_class = ExpertiseMonitoringContractSerializer
    permission_classes = [MonitoringPermission]
