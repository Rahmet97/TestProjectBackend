import base64, hashlib, json, logging, os, requests
from datetime import datetime, timedelta

import xmltodict
from django.http import HttpResponse
from docx import Document

from django.db.models import Q
from django.shortcuts import render
from django.conf import settings
from rest_framework import views, generics, permissions, response, status, parsers
from django.core.files.storage import default_storage
from rest_framework.generics import get_object_or_404

from accounts.models import UserData, YurUser, FizUser, Role, UniconDatas
from accounts.serializers import (
    YurUserSerializerForContractDetail, FizUserSerializerForContractDetail,
    YurUserForOldContractSerializers, FizUserForOldContractSerializers
)
from contracts.models import AgreementStatus, Service, Participant
from contracts.tasks import file_downloader
from contracts.utils import error_response_500, render_to_pdf, delete_file, create_qr, generate_uid, hash_text
from contracts.views import num2word

from main.permission import IsRelatedToBackOffice, ConfirmContractPermission
from main.utils import responseErrorMessage

from .models import (
    VpsServiceContract, OperationSystem, OperationSystemVersion, VpsDevice, VpsTariff, VpsContractDevice,
    VpsContracts_Participants, VpsExpertSummary, VpsExpertSummaryDocument, VpsPkcs, VpsPremadeContractFile
)
from .permission import VpsServiceContractDeletePermission
from .serializers import (
    OperationSystemSerializers, OperationSystemVersionSerializers, VpsTariffSerializers,
    VpsGetUserContractsListSerializer, VpsServiceContractCreateViaClientSerializers, ConvertDocx2PDFSerializer,
    ForceSaveFileSerializer, VpsPkcsSerializer, VpsServiceContractResponseViaClientSerializers,
    VpsContractSerializerForDetail, VpsContractParticipantsSerializers, GroupVpsContractSerializerForBackoffice,
    VpsExpertSummarySerializerForSave, VpsUserForContractCreateSerializers, VpsCreateContractWithFileSerializers,
    VpsTariffSummSerializer
)
from .serializers import FileUploadSerializer
from .utils import get_configurations_context

logger = logging.getLogger(__name__)


# ##############
def create_contract_participants(service_obj, exclude_role=None):
    participants = Participant.objects.get(service_id=service_obj.id).participants.all().exclude(name=exclude_role)
    users = []
    service_group = service_obj.group
    for role in participants:

        query = Q(role=role) & (Q(group__in=[service_group]) | Q(group=None))
        matching_user = UserData.objects.filter(query).last()

        if matching_user is not None:
            users.append(matching_user)
        else:
            logger.error("226 -> No matching user found")

    return users


def create_vps_configurations(configuration_data: dict, contract: object):
    if configuration_data.pop("count_vm") != len(configuration_data.get("operation_system_versions")):
        contract.delete()

        responseErrorMessage(
            "count_vm is equal to count of operation system versions !!",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    tariff_id = configuration_data.pop("tariff")
    if isinstance(tariff_id, int):
        try:
            tariff = VpsTariff.objects.get(id=tariff_id)
        except VpsTariff.DoesNotExist:
            raise serializers.ValidationError("Invalid tariff ID.")
    else:
        tariff = tariff_id

    operation_system_versions = configuration_data.pop("operation_system_versions")
    for os_version in operation_system_versions:

        operation_system_version_id = os_version.get("operation_system_version")
        if isinstance(operation_system_version_id, str):
            try:
                operation_system_version = OperationSystemVersion.objects.get(id=operation_system_version_id)
            except OperationSystemVersion.DoesNotExist:
                raise serializers.ValidationError("Invalid operation system version ID.")
        else:
            operation_system_version = operation_system_version_id

        operation_system = operation_system_version.operation_system
        ipv_address = os_version.get("ipv_address")

        if tariff:
            vps_device, _ = VpsDevice.objects.get_or_create(
                operation_system=operation_system,
                operation_system_version=operation_system_version,

                storage_type=tariff.vps_device.storage_type,
                storage_disk=tariff.vps_device.storage_disk,
                cpu=tariff.vps_device.cpu,
                ram=tariff.vps_device.ram,
                internet=tariff.vps_device.internet,
                tasix=tariff.vps_device.tasix,
                imut=tariff.vps_device.imut,
                ipv_address=ipv_address
            )
        else:
            # Retrieve an object or create it if it doesn't exist
            vps_device, _ = VpsDevice.objects.get_or_create(
                operation_system=operation_system,
                operation_system_version=operation_system_version,

                ipv_address=ipv_address,
                **configuration_data
            )

        VpsContractDevice.objects.create(
            contract=contract,
            device=vps_device
        )


def get_number_and_prefix(service_obj):
    """
    return:
        number -> int
        prefix -> str
    """
    try:
        last_contract = VpsServiceContract.objects.last()
        if last_contract and last_contract.contract_number:
            number = int(last_contract.contract_number.split("-")[-1]) + 1
        else:
            number = 1
    except ValueError:
        number = 1
    prefix = service_obj.prefix  # "VM"
    return number, prefix


def generate_hash_code(text: str):
    hashcode = hashlib.md5(text.encode())
    hash_code = hashcode.hexdigest()
    return hash_code


# #############


# View for listing OperationSystem objects
class OperationSystemListView(generics.ListAPIView):
    # Retrieve all OperationSystem objects
    queryset = OperationSystem.objects.all()
    # Use OperationSystemSerializers for serialization
    serializer_class = OperationSystemSerializers

    # Specify the permission classes for this view
    # permission_classes = [permissions.IsAuthenticated]


class VpsGetUserContracts(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contracts = VpsServiceContract.objects.filter(client=request.user).order_by('-id')
        serializer = VpsGetUserContractsListSerializer(contracts, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


# View for listing OperationSystemVersion objects based on an operation_system_id
class OperationSystemVersionListView(views.APIView):
    # Specify the permission classes for this view
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request, operation_system_id):
        # Filter OperationSystemVersion objects based on the provided operation_system_id
        operation_system_version_objects = OperationSystemVersion.objects.filter(
            operation_system__id=operation_system_id
        )

        # Check if any OperationSystemVersion objects were found
        if operation_system_version_objects.exists():
            # Serialize the queryset of OperationSystemVersion objects
            serializer = OperationSystemVersionSerializers(operation_system_version_objects, many=True)

            # Return the serialized data with a 200 OK status
            return response.Response(data=serializer.data, status=status.HTTP_200_OK)

        # If no OperationSystemVersion objects were found, raise an error
        raise responseErrorMessage(
            message="objects not found 404",
            status_code=status.HTTP_404_NOT_FOUND
        )


class VpsTariffListView(generics.ListAPIView):
    queryset = VpsTariff.objects.all()
    serializer_class = VpsTariffSerializers
    # permission_classes = [permissions.IsAuthenticated]


class DeleteVpsContractView(generics.DestroyAPIView):
    queryset = VpsServiceContract.objects.all()
    permission_classes = [VpsServiceContractDeletePermission]


class VpsConfirmContract(views.APIView):
    permission_classes = (ConfirmContractPermission,)

    def post(self, request):
        contract = get_object_or_404(VpsServiceContract, pk=int(request.data['contract']))

        if int(request.data['summary']) == 1:  # 1 -> muofiq, 0 -> muofiq emas
            agreement_status = AgreementStatus.objects.get(name='Kelishildi')
        else:
            agreement_status = AgreementStatus.objects.get(name='Rad etildi')
            contract.contract_status = 5  # REJECTED
            # if contract.contract_cash >= 10_000_000:
            #     director_participants = VpsContracts_Participants.objects.get(
            #         Q(role__name=Role.RoleNames.DIRECTOR),
            #         Q(contract=contract),
            #     )
            #     director_participants.agreement_status = agreement_status
            #     director_participants.save()

        contracts_participants = VpsContracts_Participants.objects.get(
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
        # director_role_name = \
        #     Role.RoleNames.DIRECTOR if contract.contract_cash >= 10_000_000 else Role.RoleNames.DEPUTY_DIRECTOR
        try:
            cntrct = VpsContracts_Participants.objects.get(
                contract=contract,
                role__name=Role.RoleNames.DIRECTOR,
                agreement_status__name='Kelishildi'
            )
        except VpsContracts_Participants.DoesNotExist:
            cntrct = None

        if cntrct:
            contract.is_confirmed_contract = 2  # UNICON_CONFIRMED
            contract.contract_status = 2  # CUSTOMER_SIGNATURE_IS_EXPECTED

        contract.save()

        request.data._mutable = True
        request.data['user'] = request.user.id
        documents = request.FILES.getlist('documents', None)

        summary = VpsExpertSummarySerializerForSave(
            data=request.data, context={'documents': documents}
        )
        summary.is_valid(raise_exception=True)
        summary.save()

        return response.Response(status=200)


class FileUploadAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            destination_path = f'{settings.MEDIA_ROOT}/Contract/{str(uploaded_file).replace(" ", "_")}'
            saved_path = default_storage.save(destination_path, uploaded_file)
            file_path = f"http://{request.META['HTTP_HOST']}/media/{saved_path}"
            hashed_text = hash_text(file_path)
            return response.Response({
                'message': 'File uploaded successfully',
                'path': file_path,
                'key': hashed_text
            })
        else:
            return response.Response(serializer.errors, status=400)


class NewFileCreateAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        doc = Document()
        file_name = generate_uid(8)
        file_path = f'{settings.MEDIA_ROOT}/Contract/{file_name}.docx'
        file_url = 'http://' + request.META['HTTP_HOST'] + '/media/Contract/' + file_name + '.docx'
        doc.save(file_path)
        hashed_text = hash_text(file_path)
        return response.Response({'path': file_url, 'key': hashed_text})


class ConvertDocx2PDFAPIView(views.APIView):
    serializer_class = ConvertDocx2PDFSerializer
    permission_classes = ()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = 'http://onlyoffice-documentserver/ConvertService.ashx'
        payload = {
            'async': False,
            'filetype': 'docx',
            'key': serializer.validated_data.get('key'),
            'outputtype': 'pdf',
            'title': f"{serializer.validated_data.get('key')}.pdf",
            'url': serializer.validated_data.get('url')
        }
        rsp = requests.post(url, headers={"Accept": "application/json"}, json=payload)
        if rsp.status_code == 200:
            print('153 ===> ', rsp)
            rsp = rsp.json()
            print('155 ===> ', rsp)
            file_url = rsp['fileUrl']
        else:
            return response.Response({'message': 'Does not converted!'})
        return response.Response({'file_url': file_url.replace('onlyoffice-documentserver', '185.74.4.35:81')})


class ForceSaveFileAPIView(views.APIView):
    serializer_class = ForceSaveFileSerializer
    permission_classes = ()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = 'http://onlyoffice-documentserver/coauthoring/CommandService.ashx'
        payload = {
            'c': 'forcesave',
            'key': serializer.validated_data.get('key'),
        }
        rsp = requests.post(url, json=payload)
        if rsp.status_code == 200:
            rsp = rsp.json()
            print('153 ===> ', rsp)
        else:
            return response.Response({'message': 'Does not converted!'})
        return response.Response(rsp)


class CallbackUrlAPIView(views.APIView):
    permission_classes = ()

    def post(self, request):
        body = request.body.decode('utf-8')
        json_data = json.loads(body)
        print('json_data >>>>> ', json_data)

        if json_data['status'] == 2 or json_data['status'] == 6:
            download_uri = json_data['url']
            rsp = requests.get(download_uri)
            print(request.query_params.get('filename'))
            path_for_save = f"{settings.MEDIA_ROOT}/Contract/{request.query_params.get('filename')}"
            with open(path_for_save, 'wb') as f:
                f.write(rsp.content)
        return response.Response({'error': 0})


class CreateVpsServiceContractViaClientView(views.APIView):
    queryset = VpsServiceContract.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        context = dict()
        request_objects_serializers = VpsServiceContractCreateViaClientSerializers(data=request.data)
        request_objects_serializers.is_valid(raise_exception=True)
        is_back_office = request_objects_serializers.validated_data.pop("is_back_office")

        number, prefix = get_number_and_prefix(request_objects_serializers.validated_data.get("service"))

        if is_back_office:
            user_serializers = VpsUserForContractCreateSerializers(data=request.data)
            user_serializers.is_valid(raise_exception=True)
            pin_or_tin = user_serializers.validated_data.get("pin_or_tin")
            if user_serializers.validated_data.get("user_type") == 2:
                context['u_type'] = 'yuridik'
                # context["user_obj"] = YurUser.objects.get(tin=pin_or_tin)
                context["user_obj"] = get_object_or_404(YurUser, tin=pin_or_tin)
            elif user_serializers.validated_data.get("user_type") == 1:
                context['u_type'] = 'fizik'
                # context["user_obj"] = FizUser.objects.get(pin=pin_or_tin)
                context["user_obj"] = get_object_or_404(FizUser, pin=pin_or_tin)
        else:
            if request.user.type == 2:
                context['u_type'] = 'yuridik'
                # context["user_obj"] = YurUser.objects.get(userdata=request.user)
                context["user_obj"] = get_object_or_404(YurUser, userdata=request.user)
            elif request.user.type == 1:
                context['u_type'] = 'fizik'
                # context["user_obj"] = FizUser.objects.get(userdata=request.user)
                context["user_obj"] = get_object_or_404(FizUser, userdata=request.user)

        context['contract_number'] = prefix + '-' + str(number)

        date = request_objects_serializers.validated_data.get("contract_date")
        context['datetime'] = datetime.fromisoformat(str(date)).strftime('%d.%m.%Y')

        configurations = request_objects_serializers.validated_data.pop("configuration")

        configurations_context, configurations_total_price, configurations_cost_prices = get_configurations_context(
            configurations
        )
        context['configurations'] = {
            "configurations_total_price": configurations_total_price,
            "configurations": configurations_context,
            "configurations_cost_prices": configurations_cost_prices
        }
        context["unicon_datas"] = UniconDatas.objects.last()

        context['host'] = 'http://' + request.META['HTTP_HOST']
        context['qr_code'] = ''
        context['save'] = False
        context['page_break'] = False

        service_obj = request_objects_serializers.validated_data.get("service")

        if int(request_objects_serializers.validated_data.pop("save")):
            context['save'] = True
            context['page_break'] = True

            if request.user.type == 1:
                hash_text_part = context.get('user_obj').full_name
            else:
                hash_text_part = context.get('user_obj').get_director_full_name

            hash_code = generate_hash_code(
                text=f"{hash_text_part}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
            )

            link = 'http://' + request.META['HTTP_HOST'] + f'/expertise/contract/{hash_code}'
            qr_code_path = create_qr(link)
            context['hash_code'] = hash_code
            context['qr_code'] = f"http://api2.unicon.uz/media/qr/{hash_code}.png"

            # Contract yaratib olamiz bazada id_code olish uchun
            client = context["user_obj"].userdata
            vps_service_contract = VpsServiceContract.objects.create(
                **request_objects_serializers.validated_data,
                # service=service_obj,
                contract_number=context['contract_number'],
                client=client,
                status=4,
                contract_status=1,  # new
                payed_cash=0,
                # base64file=base64code,
                hashcode=hash_code,
                contract_cash=configurations_total_price
                # like_preview_pdf=like_preview_pdf_path
            )
            vps_service_contract.save()

            context['id_code'] = vps_service_contract.id_code

            # rendered html file
            contract_file_for_base64_pdf = None

            template_name = "fizUzRuVPS.html"  # fizik
            if request.user.type == 2:  # yuridik
                template_name = "yurUzRuVPS.html"

            pdf = render_to_pdf(template_src=template_name, context_dict=context)
            if pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                contract_file_for_base64_pdf = f"{output_dir}/{context.get('contract_number')}_{hash_text_part}.pdf"
                with open(contract_file_for_base64_pdf, 'wb') as f:
                    f.write(pdf.content)
            else:
                error_response_500()

            if contract_file_for_base64_pdf is None:
                error_response_500()

            contract_file = open(contract_file_for_base64_pdf, 'rb').read()
            base64code = base64.b64encode(contract_file)

            # delete pdf file
            delete_file(contract_file_for_base64_pdf)
            # delete qr_code file
            delete_file(qr_code_path)

            # save the preview to the base because the contract is used depending on its status
            context['save'] = False
            # context['save'] = True
            like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)

            like_preview_pdf_path = None
            if like_preview_pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{hash_text_part}.pdf"
                with open(like_preview_pdf_path, 'wb') as f:
                    f.write(like_preview_pdf.content)
            if like_preview_pdf_path is None:
                error_response_500()

            vps_service_contract.base64file = base64code
            vps_service_contract.like_preview_pdf = like_preview_pdf_path
            vps_service_contract.save()

            for configuration_data in configurations:
                create_vps_configurations(configuration_data, vps_service_contract)

            # VpsContracts_Participants
            # if the amount of the contract is less than 10 million,
            # the director will not participate as a participant
            exclude_role = None
            # if vps_service_contract.contract_cash < 10_000_000:
            #     exclude_role = Role.RoleNames.DIRECTOR

            participants = create_contract_participants(
                service_obj=service_obj,
                exclude_role=exclude_role
            )
            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()

            for participant in participants:
                VpsContracts_Participants.objects.create(
                    contract=vps_service_contract,
                    role=participant.role,
                    participant_user=participant,
                    agreement_status=agreement_status
                ).save()

            return response.Response(
                data=VpsServiceContractResponseViaClientSerializers(vps_service_contract).data,
                status=201
            )

        template_name = "fizUzRuVPS.html"  # fizik
        if request.user.type == 2:  # yuridik
            template_name = "yurUzRuVPS.html"

        return render(request=request, template_name=template_name, context=context)


class VpsSavePkcs(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VpsPkcsSerializer

    @staticmethod
    def join2pkcs(pkcs7_1, pkcs7_2):
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
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1', data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        pkcs7_12 = dict_data['S:Envelope']['S:Body']['ns2:join2Pkcs7AttachedResponse']['return']
        d = json.loads(pkcs7_12)
        return d

    @staticmethod
    def verifyPkcs(pkcs):
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
            contract = VpsServiceContract.objects.get(pk=contract_id)
            role_names = VpsContracts_Participants.objects.filter(
                contract=contract
            ).values_list('role__name', flat=True)
            if request.user.role.name in role_names or request.user == contract.client:
                if not VpsPkcs.objects.filter(contract=contract).exists():
                    VpsPkcs.objects.create(contract=contract, pkcs7=pkcs7)
                else:
                    pkcs_exist_object = VpsPkcs.objects.get(contract=contract)
                    client_pkcs = pkcs_exist_object.pkcs7
                    new_pkcs7 = self.join2pkcs(pkcs7, client_pkcs)
                    pkcs_exist_object.pkcs7 = new_pkcs7
                    pkcs_exist_object.save()
            if request.user == contract.client:
                contract.contract_status = 3  # PAYMENT_IS_PENDING
                contract.is_confirmed_contract = 3  # CLIENT_CONFIRMED
                contract.save()
        except VpsServiceContract.DoesNotExist:
            return response.Response({'message': 'Bunday shartnoma mavjud emas'})
        return response.Response({'message': 'Success'})


class VpsGetUserContractsViews(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contracts = VpsServiceContract.objects.filter(client=request.user).order_by('-id')
        serializer = VpsGetUserContractsListSerializer(contracts, many=True)
        return response.Response(serializer.data)


class VpsContractDetail(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)
    permitted_roles = [
        Role.RoleNames.ADMIN,
        Role.RoleNames.ACCOUNTANT,
        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,
        Role.RoleNames.SECTION_SPECIALIST,
    ]

    def get(self, request, pk):
        client = None
        contract = VpsServiceContract.objects.select_related('client').get(pk=pk)
        contract_serializer = VpsContractSerializerForDetail(contract)

        # agar request user mijoz bo'lsa
        if request.user.role.name == Role.RoleNames.CLIENT and contract.client == request.user:
            client = request.user

        # agar reuqest user role permitted_roles tarkibida bo'lsa
        elif request.user.role.name in self.permitted_roles:
            client = contract.client
            participant = VpsContracts_Participants.objects.filter(
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

        if client.type == 1:  # fiz
            user = FizUser.objects.get(userdata=client)
            client_serializer = FizUserSerializerForContractDetail(user)
        else:
            user = YurUser.objects.get(userdata=client)
            client_serializer = YurUserSerializerForContractDetail(user)

        participants = VpsContracts_Participants.objects.filter(contract=contract).order_by('role_id')
        participant_serializer = VpsContractParticipantsSerializers(participants, many=True)

        try:
            expert_summary = VpsExpertSummary.objects.filter(
                Q(contract=contract),
                Q(user=request.user),
                (Q(user__group__in=request.user.group.all()) | Q(user__group=None))
            ).distinct()
            expert_summary_value = expert_summary[0].summary if expert_summary.exists() else 0

        except (VpsExpertSummary.DoesNotExist, IndexError):
            expert_summary_value = 0

        # projects_obj = ExpertiseServiceContractTarif.objects.filter(expertisetarifcontract__contract=contract)
        # projects_obj_serializer = ExpertiseServiceContractProjects(projects_obj, many=True)
        return response.Response(data={
            'contract': contract_serializer.data,
            'client': client_serializer.data,
            'participants': participant_serializer.data,
            # 'projects': projects_obj_serializer.data,
            'is_confirmed': True if int(expert_summary_value) == 1 else False
        }, status=200)


class VpsGetGroupContract(views.APIView):
    permission_classes = [IsRelatedToBackOffice]

    def get(self, request):

        # barcha contractlar
        barcha_data = VpsServiceContract.objects.order_by('-contract_date')
        self.check_object_permissions(request=request, obj=barcha_data)
        barcha = GroupVpsContractSerializerForBackoffice(barcha_data, many=True)

        # yangi contractlar
        if request.user.role.name == Role.RoleNames.DIRECTOR:
            contract_participants = VpsContracts_Participants.objects.filter(
                Q(role__name=Role.RoleNames.DEPUTY_DIRECTOR),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')

            director_accepted_contracts = VpsContracts_Participants.objects.filter(
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
            contract_participants = VpsContracts_Participants.objects.filter(
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
        yangi = GroupVpsContractSerializerForBackoffice(yangi_data, many=True)

        # kelishilgan contractlar
        contract_participants = VpsContracts_Participants.objects.filter(
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
        kelishilgan = GroupVpsContractSerializerForBackoffice(kelishilgan_data, many=True)

        # rad etilgan contractlar
        rejected_cancelled_data = barcha_data.filter(
            contract_status__in=[5, 6]  # REJECTED, CANCELLED
        ).order_by('-contract_date')
        self.check_object_permissions(request=request, obj=rejected_cancelled_data)
        rad_etildi = GroupVpsContractSerializerForBackoffice(rejected_cancelled_data, many=True)

        # expired contracts
        # Retrieve contract IDs where the user's role matches and agreement_status is 'Kelishildi'
        contract_participants = VpsContracts_Participants.objects.filter(
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
        expired = GroupVpsContractSerializerForBackoffice(expired_data, many=True)

        # last day contracts
        today = datetime.now()
        contract_participants = VpsContracts_Participants.objects.filter(
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
        lastday = GroupVpsContractSerializerForBackoffice(lastday_data, many=True)

        # expired accepted contracts
        contract_participants = VpsContracts_Participants.objects.filter(
            role=request.user.role,
            agreement_status__name='Kelishildi'
        ).values_list('contract', flat=True)

        expired_accepted_data = barcha_data.filter(
            id__in=contract_participants,
            contract_date__lt=datetime.now() - timedelta(days=1)
        ).select_related().order_by('-contract_date')
        self.check_object_permissions(request=request, obj=expired_accepted_data)
        expired_accepted = GroupVpsContractSerializerForBackoffice(expired_accepted_data, many=True)

        # in_time contracts
        # Retrieve contracts based on the specified conditions and ordering
        contracts_selected = VpsExpertSummary.objects.select_related('contract').filter(
            user=request.user
        ).order_by('-contract', '-contract__contract_date')
        # Filter the contracts that are in time based on the date comparison
        in_time_data = [
            element.contract for element in contracts_selected
            if element.contract.contract_date < element.date <= element.contract.contract_date + timedelta(days=1)
        ]
        self.check_object_permissions(request=request, obj=in_time_data)
        in_time = GroupVpsContractSerializerForBackoffice(in_time_data, many=True)

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


class VpsGetContractFile(views.APIView):
    permission_classes = ()

    def get(self, request, hash_code):
        if hash_code is None:
            return response.Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)

        contract = get_object_or_404(VpsServiceContract, hashcode=hash_code)
        if contract.contract_status == 4 or contract.contract_status == 3:  # PAYMENT_IS_PENDING ACTIVE
            # delete like pdf file test mode
            if contract.like_preview_pdf:
                delete_file(contract.like_preview_pdf.path)
                contract.like_preview_pdf = None
                contract.save()

            file_pdf_path, pdf_file_name = file_downloader(
                base64file=bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'),
                # base64file=bytes(contract.base64file[2:len(contract.base64file) - 1], 'ascii'),
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


class CreateVpsContractWithFile(generics.CreateAPIView):
    queryset = VpsServiceContract.objects.all()
    serializer_class = VpsCreateContractWithFileSerializers
    serializer_class_configuration = VpsTariffSummSerializer
    # serializer_class_contract = VpsCreateContractWithFileSerializersSerializers
    serializer_class_yur_user = YurUserForOldContractSerializers
    serializer_class_fiz_user = FizUserForOldContractSerializers
    permission_classes = [permissions.IsAuthenticated]  # -> for employee

    # parser_classes = [parsers.MultiPartParser]

    # def post(self, request):
    #     serializer_class_user = None
    #     contract_serializer = self.serializer_class_contract(data=request.data)
    #     contract_serializer.is_valid(raise_exception=True)
    #
    #     client_user = contract_serializer.validated_data.pop("client_user")
    #     user_type = client_user.validated_data.get("user_type")
    #     pin_or_tin = client_user.validated_data.get("pin_or_tin")
    #     file = request.FILES.get('file', None)
    #
    #     if not pin_or_tin or not file:
    #         responseErrorMessage(message="pin or tin and file not be empty", status_code=status.HTTP_400_BAD_REQUEST)
    #
    #     if UserData.objects.filter(username=pin_or_tin).exists():
    #         user_obj = UserData.objects.get(username=pin_or_tin)
    #     else:
    #         username = str(pin_or_tin)
    #         if user_type == 2:  # yur usertype
    #             director_firstname = request.data.get("director_firstname", None)
    #             password = director_firstname[0].upper() + username + director_firstname[-1].upper()
    #         else:
    #             first_name = request.data.get("first_name", None)
    #             password = first_name[0].upper() + username + first_name[-1].upper()
    #
    #         user_obj = UserData(
    #             username=username,
    #             type=1,
    #             role=Role.objects.get(name=Role.RoleNames.CLIENT),
    #         )
    #         user_obj.set_password(password)
    #         user_obj.save()
    #
    #     # if user is fiz human
    #     if user_type == 2:  # yur user
    #         user, _ = YurUser.objects.get_or_create(userdata=user_obj)
    #         serializer_class_user = self.serializer_class_yur_user(instance=user, data=request.data, partial=True)
    #         serializer_class_user.is_valid(raise_exception=True)
    #         serializer_class_user.save()
    #         u_type, hash_text_part = 'yuridik', user.get_director_full_name
    #     else:  # fiz user
    #         user, _ = FizUser.objects.get_or_create(userdata=user_obj)
    #         serializer_class_user = self.serializer_class_fiz_user(instance=user, data=request.data, partial=True)
    #         serializer_class_user.is_valid(raise_exception=True)
    #         serializer_class_user.save()
    #         u_type, hash_text_part = 'fizik', user.full_name
    #
    #     # request_objects_serializers = self.serializer_class_contract(data=request.data)
    #     # request_objects_serializers.is_valid(raise_exception=True)
    #
    #     service_obj = contract_serializer.validated_data.get("service")
    #     number, prefix = get_number_and_prefix(service_obj)
    #     contract_number = prefix + '-' + str(number)
    #
    #     configurations = contract_serializer.validated_data.pop("configuration")
    #     _, configurations_total_price, _ = get_configurations_context(configurations)
    #
    #     hash_code = generate_hash_code(
    #         text=f"{hash_text_part}{contract_number}{u_type}{datetime.now()}"
    #     )
    #
    #     # Contract yaratib olamiz bazada id_code olish uchun
    #     vps_service_contract = VpsServiceContract.objects.create(
    #         **contract_serializer.validated_data,
    #         contract_number=contract_number,
    #         client=user_obj,
    #         status=2,
    #         contract_status=3,  # active
    #         is_confirmed_contract=4,  # DONE
    #         payed_cash=0,
    #         hashcode=hash_code,
    #         contract_cash=configurations_total_price
    #     )
    #     vps_service_contract.save()
    #
    #     # contract file for base64 pdf -> before it file uploaded and created to db
    #     if file:
    #         premade_contract_file = VpsPremadeContractFile.objects.create(contract=vps_service_contract, file=file)
    #         file_path = premade_contract_file.file.path
    #         if os.path.exists(file_path):
    #             try:
    #                 contract_file = open(file_path, 'rb').read()
    #                 base64code = base64.b64encode(contract_file)
    #                 vps_service_contract.base64file = base64code
    #             except Exception as e:
    #                 logger.error(e)
    #         else:
    #             logger.info("The file does not exist.")
    #     vps_service_contract.save()
    #
    #     for configuration_data in configurations:
    #         create_vps_configurations(configuration_data, vps_service_contract)
    #
    #     # VpsContracts_Participants
    #     # if the amount of the contract is less than 10 million,
    #     # the director will not participate as a participant
    #     exclude_role = None
    #     # if vps_service_contract.contract_cash < 10_000_000:
    #     #     exclude_role = Role.RoleNames.DIRECTOR
    #
    #     participants = create_contract_participants(
    #         service_obj=service_obj,
    #         exclude_role=exclude_role
    #     )
    #     agreement_status = AgreementStatus.objects.filter(name='Kelishildi').first()
    #
    #     for participant in participants:
    #         VpsContracts_Participants.objects.create(
    #             contract=vps_service_contract,
    #             role=participant.role,
    #             participant_user=participant,
    #             agreement_status=agreement_status
    #         ).save()
    #
    #     return response.Response(status=status.HTTP_201_CREATED)

    # return response.Response({
    #     'user-data': serializer_class_user.data,
    #     'contract-data': self.serializer_class_yur_user(vps_service_contract).data,
    # }, status=status.HTTP_201_CREATED)

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     self.perform_create(serializer)
    #
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    #
    # def perform_create(self, serializer):
    #     client_user = serializer.validated_data.pop("client_user")
    #     user_type = client_user.validated_data.get("user_type")
    #     pin_or_tin = client_user.validated_data.get("pin_or_tin")
    #     file = request.FILES.get('file', None)
    #
    #     if not pin_or_tin or not file:
    #         responseErrorMessage(message="pin or tin and file not be empty", status_code=status.HTTP_400_BAD_REQUEST)
    #
    #     if UserData.objects.filter(username=pin_or_tin).exists():
    #         user_obj = UserData.objects.get(username=pin_or_tin)
    #     else:
    #         username = str(pin_or_tin)
    #         if user_type == 2:  # yur usertype
    #             director_firstname = request.data.get("director_firstname", None)
    #             password = director_firstname[0].upper() + username + director_firstname[-1].upper()
    #         else:
    #             first_name = request.data.get("first_name", None)
    #             password = first_name[0].upper() + username + first_name[-1].upper()
    #
    #         user_obj = UserData(
    #             username=username,
    #             type=1,
    #             role=Role.objects.get(name=Role.RoleNames.CLIENT),
    #         )
    #         user_obj.set_password(password)
    #         user_obj.save()
    #
    #     # if user is fiz human
    #     if user_type == 2:  # yur user
    #         user, _ = YurUser.objects.get_or_create(userdata=user_obj)
    #         serializer_class_user = self.serializer_class_yur_user(instance=user, data=request.data, partial=True)
    #         serializer_class_user.is_valid(raise_exception=True)
    #         serializer_class_user.save()
    #         u_type, hash_text_part = 'yuridik', user.get_director_full_name
    #     else:  # fiz user
    #         user, _ = FizUser.objects.get_or_create(userdata=user_obj)
    #         serializer_class_user = self.serializer_class_fiz_user(instance=user, data=request.data, partial=True)
    #         serializer_class_user.is_valid(raise_exception=True)
    #         serializer_class_user.save()
    #         u_type, hash_text_part = 'fizik', user.full_name
    #
    #     service_obj = serializer.validated_data.get("service")
    #     number, prefix = get_number_and_prefix(service_obj)
    #     contract_number = prefix + '-' + str(number)
    #
    #     configurations = serializer.validated_data.pop("configuration")
    #     _, configurations_total_price, _ = get_configurations_context(configurations)
    #
    #     hash_code = generate_hash_code(
    #         text=f"{hash_text_part}{contract_number}{u_type}{datetime.now()}"
    #     )
    #
    #     vps_service_contract = serializer.save(
    #         contract_number=contract_number,
    #         client=user_obj,
    #         status=2,
    #         contract_status=3,  # active
    #         is_confirmed_contract=4,  # DONE
    #         payed_cash=0,
    #         hashcode=hash_code,
    #         contract_cash=configurations_total_price
    #     )
    #
    #     # contract file for base64 pdf -> before it file uploaded and created to db
    #     if file:
    #         premade_contract_file = VpsPremadeContractFile.objects.create(contract=vps_service_contract, file=file)
    #         file_path = premade_contract_file.file.path
    #         if os.path.exists(file_path):
    #             try:
    #                 contract_file = open(file_path, 'rb').read()
    #                 base64code = base64.b64encode(contract_file)
    #                 vps_service_contract.base64file = base64code
    #             except Exception as e:
    #                 logger.error(e)
    #         else:
    #             logger.info("The file does not exist.")
    #     vps_service_contract.save()
    #
    #     for configuration_data in configurations:
    #         create_vps_configurations(configuration_data, vps_service_contract)
    #
    #     # VpsContracts_Participants
    #     # if the amount of the contract is less than 10 million,
    #     # the director will not participate as a participant
    #     exclude_role = None
    #     # if vps_service_contract.contract_cash < 10_000_000:
    #     #     exclude_role = Role.RoleNames.DIRECTOR
    #
    #     participants = create_contract_participants(
    #         service_obj=service_obj,
    #         exclude_role=exclude_role
    #     )
    #     agreement_status = AgreementStatus.objects.filter(name='Kelishildi').first()
    #
    #     for participant in participants:
    #         VpsContracts_Participants.objects.create(
    #             contract=vps_service_contract,
    #             role=participant.role,
    #             participant_user=participant,
    #             agreement_status=agreement_status
    #         ).save()

    def get_serializer(self, *args, **kwargs):
        # Customize the serializer instantiation here
        # Parse client_user and configurations as JSON objects
        client_user_data = self.parse_client_data(self.request.data.get("client_user"))
        configurations_data = self.parse_client_data(self.request.data.get("configuration"))

        # Update request.data with parsed data
        self.request.data["client_user"] = client_user_data
        self.request.data["configuration"] = configurations_data

        # You can modify the arguments or add additional logic as needed
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def perform_create(self, serializer):
        client_user = VpsUserForContractCreateSerializers(data=self.request.data.get("client_user"))
        client_user.is_valid(raise_exception=True)
        user_type = client_user.validated_data.get("user_type")
        pin_or_tin = client_user.validated_data.get("pin_or_tin")

        file = self.request.FILES.get('file', None)

        if not pin_or_tin or not file:
            return Response({"error": "pin or tin and file cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        user_obj = self.get_or_create_user(pin_or_tin, user_type)

        user, u_type, hash_text_part = self.get_user_and_info(user_type, user_obj)

        service_obj = serializer.validated_data.get("service")
        contract_number = self.generate_contract_number(service_obj)

        # configurations = serializer.validated_data.pop("configuration")
        configurations = self.serializer_class_configuration(data=self.request.data.get("configuration"), many=True)
        configurations.is_valid(raise_exception=True)

        configurations_total_price = self.get_configurations_total_price(configurations.data)

        hash_code = self.generate_hash_code(hash_text_part, contract_number, u_type)

        vps_service_contract = self.save_vps_service_contract(
            serializer, contract_number, user_obj,
            configurations_total_price, hash_code
        )

        self.handle_contract_file(vps_service_contract, file)

        self.create_vps_configurations(configurations.data, vps_service_contract)

        participants = self.create_contract_participants(service_obj)
        agreement_status = AgreementStatus.objects.filter(name='Kelishildi').first()

        self.create_contract_participant_objects(vps_service_contract, participants, agreement_status)

        return vps_service_contract

    def parse_client_data(self, client_data):
        try:
            return json.loads(client_data)
        except json.JSONDecodeError:
            return {}

    def get_or_create_user(self, pin_or_tin, user_type):
        try:
            return UserData.objects.get(username=pin_or_tin)
        except UserData.DoesNotExist:
            return self.create_user_obj(pin_or_tin, user_type)

    def create_user_obj(self, pin_or_tin, user_type):
        username = str(pin_or_tin)
        role = Role.objects.get(name=Role.RoleNames.CLIENT)

        if user_type == 2:  # yur usertype
            director_firstname = self.request.data.get("client_user").get("director_firstname", None)
            password = director_firstname[0].upper() + username + director_firstname[-1].upper()
        else:
            first_name = self.request.data.get("client_user").get("first_name", None)
            password = first_name[0].upper() + username + first_name[-1].upper()

        user_obj = UserData(
            username=username,
            type=1,
            role=role,
        )
        user_obj.set_password(password)
        user_obj.save()

        return user_obj

    def get_user_and_info(self, user_type, user_obj):
        update_data = self.request.data.get("client_user")
        if user_type == 2:  # yur user
            user, created = YurUser.objects.get_or_create(userdata=user_obj)
            if created:
                serializer_class_user = self.serializer_class_yur_user(instance=user, data=update_data, partial=True)
                serializer_class_user.is_valid(raise_exception=True)
                serializer_class_user.save()

            u_type, hash_text_part = 'yuridik', user.get_director_full_name
        else:  # fiz user
            user, created = FizUser.objects.get_or_create(userdata=user_obj)
            if created:
                serializer_class_user = self.serializer_class_fiz_user(instance=user, data=update_data, partial=True)
                serializer_class_user.is_valid(raise_exception=True)
                serializer_class_user.save()

            u_type, hash_text_part = 'fizik', user.full_name

        return user, u_type, hash_text_part

    def generate_contract_number(self, service_obj):
        number, prefix = get_number_and_prefix(service_obj)
        return prefix + '-' + str(number)

    def get_configurations_total_price(self, configurations):
        _, configurations_total_price, _ = get_configurations_context(configurations)
        return configurations_total_price

    def generate_hash_code(self, hash_text_part, contract_number, u_type):
        return generate_hash_code(text=f"{hash_text_part}{contract_number}{u_type}{datetime.now()}")

    def save_vps_service_contract(self, serializer, contract_number, user_obj, configurations_total_price, hash_code):
        vps_service_contract = serializer.save(
            contract_number=contract_number,
            client=user_obj,
            status=2,
            contract_status=3,  # active
            is_confirmed_contract=4,  # DONE
            payed_cash=0,
            hashcode=hash_code,
            contract_cash=configurations_total_price
        )
        return vps_service_contract

    def handle_contract_file(self, vps_service_contract, file):
        if file:
            premade_contract_file = VpsPremadeContractFile.objects.create(contract=vps_service_contract, file=file)
            file_path = premade_contract_file.file.path
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as contract_file:
                        contract_file_data = contract_file.read()
                    base64code = base64.b64encode(contract_file_data)
                    vps_service_contract.base64file = base64code
                except Exception as e:
                    logger.error(e)
                    return HttpResponseServerError()
            else:
                logger.info("The file does not exist.")
        vps_service_contract.save()

    def create_vps_configurations(self, configurations, vps_service_contract):
        for configuration_data in configurations:
            create_vps_configurations(configuration_data, vps_service_contract)

    def create_contract_participants(self, service_obj):
        exclude_role = None
        # if vps_service_contract.contract_cash < 10_000_000:
        #     exclude_role = Role.RoleNames.DIRECTOR

        participants = create_contract_participants(
            service_obj=service_obj,
            exclude_role=exclude_role
        )
        return participants

    def create_contract_participant_objects(self, vps_service_contract, participants, agreement_status):
        for participant in participants:
            VpsContracts_Participants.objects.create(
                contract=vps_service_contract,
                role=participant.role,
                participant_user=participant,
                agreement_status=agreement_status
            ).save()
