import base64
import hashlib
import json
import logging
import os
import requests
from datetime import datetime

import xmltodict
from docx import Document

from django.db.models import Q
from django.shortcuts import render, HttpResponse
from django.conf import settings
from rest_framework import views, generics, permissions, response, status
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view

from accounts.models import UserData, YurUser, FizUser, Role, UniconDatas
from billing.views import calculate_vps
from contracts.models import AgreementStatus, Service, Participant
from contracts.utils import error_response_500, render_to_pdf, delete_file, create_qr, generate_uid, hash_text
from contracts.views import num2word
from main.utils import responseErrorMessage
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
from .permission import VpsServiceContractDeletePermission
from .serializers import (
    OperationSystemSerializers, OperationSystemVersionSerializers,
    VpsTariffSerializers, VpsGetUserContractsListSerializer,
    VpsServiceContractCreateViaClientSerializers, ConvertDocx2PDFSerializer, ForceSaveFileSerializer, VpsPkcsSerializer,
    VpsServiceContractResponseViaClientSerializers
)
from .serializers import FileUploadSerializer
from .utils import get_configurations_context

logger = logging.getLogger(__name__)


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


# class VpsServiceContractDeleteAPIView(generics.DestroyAPIView):
#     queryset = VpsServiceContract.objects.all()
#     permission_classes = [VpsServiceContractDeletePermission]

class FileUploadAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            destination_path = f'{settings.MEDIA_ROOT}/Contract/{uploaded_file}'
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
        return response.Response({'file_url': file_url})


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


class CreateVpsServiceContractViaClientView(views.APIView):
    queryset = VpsServiceContract.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
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
        prefix = "VM"  # service_obj.group.prefix
        return number, prefix

    @staticmethod
    def generate_hash_code(text: str):
        hashcode = hashlib.md5(text.encode())
        hash_code = hashcode.hexdigest()
        return hash_code

    @staticmethod
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

    @staticmethod
    def create_vps_configurations(configuration_data: dict, contract: object):

        if configuration_data.pop("count_vm") != len(configuration_data.get("operation_system_versions")):
            contract.delete()

            responseErrorMessage(
                "count_vm is equal to count of operation system versions !!",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        tariff = configuration_data.pop("tariff")

        operation_system_versions = configuration_data.pop("operation_system_versions")
        for os_version in operation_system_versions:
            operation_system_version = os_version.get("operation_system_version")
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

    def post(self, request):
        context = dict()
        request_objects_serializers = VpsServiceContractCreateViaClientSerializers(data=request.data)
        request_objects_serializers.is_valid(raise_exception=True)

        number, prefix = self.get_number_and_prefix(request_objects_serializers.validated_data.get("service"))

        if request.user.type == 2:
            context['u_type'] = 'yuridik'
            context["user_obj"] = YurUser.objects.get(userdata=request.user)
        elif request.user.type == 1:
            context['u_type'] = 'fizik'
            context["user_obj"] = FizUser.objects.get(userdata=request.user)

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
                hash_text_part = context.get('user_obj').get_director_full_name()

            hash_code = self.generate_hash_code(
                text=f"{hash_text_part}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
            )

            link = 'http://' + request.META['HTTP_HOST'] + f'/expertise/contract/{hash_code}'
            qr_code_path = create_qr(link)
            context['hash_code'] = hash_code
            context['qr_code'] = f"http://api2.unicon.uz/media/qr/{hash_code}.png"

            # Contract yaratib olamiz bazada id_code olish uchun
            client = request.user
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
                self.create_vps_configurations(configuration_data, vps_service_contract)

            # VpsContracts_Participants
            # if the amount of the contract is less than 10 million,
            # the director will not participate as a participant
            exclude_role = None
            # if vps_service_contract.contract_cash < 10_000_000:
            #     exclude_role = Role.RoleNames.DIRECTOR

            participants = self.create_contract_participants(
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
            # if request.user == contract.client:
            #     contract.contract_status = 3  # PAYMENT_IS_PENDING
            #     contract.is_confirmed_contract = 3  # CLIENT_CONFIRMED
            #     contract.save()
        except VpsServiceContract.DoesNotExist:
            return response.Response({'message': 'Bunday shartnoma mavjud emas'})
        return response.Response({'message': 'Success'})
