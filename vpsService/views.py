import base64
import hashlib
import os
import secrets
import string
import requests
from datetime import datetime
from docx import Document

from django.db.models import Q
from django.shortcuts import render
from django.conf import settings
from rest_framework import views, generics, permissions, response, status
from django.core.files.storage import default_storage

from accounts.models import UserData, YurUser, FizUser
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
    VpsExpertSummaryDocument,
)
from .permission import VpsServiceContractDeletePermission
from .serializers import (
    OperationSystemSerializers, OperationSystemVersionSerializers,
    VpsServiceContractCreateSerializers, VpsTariffSerializers, VpsGetUserContractsListSerializer
)
from .serializers import FileUploadSerializer


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


def convert_to_pdf(request):
    # Get the DOCX file from the request
    docx_file = request.FILES['docx_file']

    # Define the URL of your ONLYOFFICE Document Server
    document_server_url = 'http://documentserver/'

    # Define the conversion URL
    conversion_url = f'{document_server_url}Convert'

    # Set the conversion parameters
    conversion_params = {
        'async': 0,
        'filetype': 'pdf',
        'outputtype': 'stream',
    }

    # Send the conversion request
    response = requests.post(conversion_url, files={'file': docx_file}, data=conversion_params)

    # Check if the conversion was successful
    if response.status_code == 200:
        # Create a PDF file name
        pdf_file_name = 'converted.pdf'

        # Set the response headers to indicate it's a PDF file
        response['Content-Disposition'] = f'attachment; filename="{pdf_file_name}"'
        response['Content-Type'] = 'application/pdf'

        return response

    # Handle the case where conversion failed
    return HttpResponse('Conversion failed', status=response.status_code)


class CreateVpsServiceContractViaClientView(views.APIView):
    queryset = VpsServiceContract.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_objects_serializers = VpsServiceContractCreateSerializers(data=request.data, many=True)
        request_objects_serializers.is_valid(raise_exception=True)
        print("request_objects_serializers >> ", request_objects_serializers)
        return response.Response(data=request_objects_serializers.data)


# class CreateVpsServiceContractViaClientView(views.APIView):
#     queryset = VpsServiceContract.objects.all()
#     permission_classes = [permissions.IsAuthenticated]
#
#     @staticmethod
#     def generate_hash_code(text: str):
#         hashcode = hashlib.md5(text.encode())
#         hash_code = hashcode.hexdigest()
#         return hash_code
#
#     @staticmethod
#     def create_contract_participants(service_id: int, exclude_role=None):
#         participants = Participant.objects.get(service_id=service_id).participants.all().exclude(name=exclude_role)
#         users = []
#         service_group = Service.objects.get(id=service_id).group
#         for role in participants:
#
#             query = Q(role=role) & (Q(group=service_group) | Q(group=None))
#
#             try:
#                 matching_user = UserData.objects.get(query)
#                 print(f"User {matching_user.id}: {matching_user.role.name}")
#
#                 users.append(matching_user)
#             except UserData.DoesNotExist:
#                 print("No matching user found")
#             except UserData.MultipleObjectsReturned:
#                 print("Multiple matching users found")
#
#         return users
#
#     def post(self, request):
#         context = dict()
#         request_objects_serializers = VpsServiceContractCreateSerializers(data=request.data, many=True)
#         request_objects_serializers.is_valid(raise_exception=True)
#
#         try:
#             number = int(VpsServiceContract.objects.last().contract_number.split("-")[-1]) + 1
#         except AttributeError:
#             number = 1
#         # prefix = Service.objects.get(pk=int(request.data['service_id'])).group.prefix
#         prefix = Service.objects.get(pk=int(request.data['service'])).group.prefix
#
#         if request.user.type == 2:  # yur
#             context['u_type'] = 'yuridik'
#             context["user_obj"] = YurUser.objects.get(
#                 tin=request_objects_serializers.validated_data.get("user_tin_or_pin")
#             )
#         elif request.user.type == 1:  # fiz
#             context['u_type'] = 'fizik'
#             context["user_obj"] = FizUser.objects.get(
#                 pin=request_objects_serializers.validated_data.get("user_tin_or_pin")
#             )
#
#         context['contract_number'] = context['contract_number'] = prefix + '-' + str(number)  # --
#
#         date = request_objects_serializers.validated_data.get("contract_date")
#         context['datetime'] = datetime.fromisoformat(str(date)).strftime('%d.%m.%Y')
#
#         context['price'] = request_objects_serializers.validated_data.get("contract_cash")
#         context['price_text'] = num2word.change_num_to_word(int(context['price']))
#
#         context['withoutnds_price'] = float(context['price']) * 0.88
#         context['withoutnds_price_text'] = num2word.change_num_to_word(int(context['withoutnds_price']))
#
#         context['onlynds_price'] = float(context['price']) * 0.12
#         context['onlynds_price_text'] = num2word.change_num_to_word(int(context['onlynds_price']))
#
#         context['configuration'] = request_objects_serializers.validated_data.get("configuration")
#
#         context['host'] = 'http://' + request.META['HTTP_HOST']
#         context['qr_code'] = ''
#         context['save'] = False
#         context['page_break'] = False
#
#         if int(request.data['save']):
#             context['save'] = True
#             context['page_break'] = True
#
#             hash_code = self.generate_hash_code(
#                 text=f"{context.get('user_obj').get_director_short_full_name}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
#             )
#
#             link = 'http://' + request.META['HTTP_HOST'] + f'/expertise/contract/{hash_code}'
#             qr_code_path = create_qr(link)
#             context['hash_code'] = hash_code
#             context['qr_code'] = f"http://api2.unicon.uz/media/qr/{hash_code}.png"
#
#             # Contract yaratib olamiz bazada id_code olish uchun
#             user_stir = request_objects_serializers.validated_data.pop('user_tin_or_pin')
#             configuration_datas = request_objects_serializers.validated_data.pop('configuration')
#
#             client = UserData.objects.get(username=user_stir)
#             expertise_service_contract = VpsServiceContract.objects.create(
#                 **request_objects_serializers.validated_data,
#                 service=int(request.data['service']),
#                 client=client,
#                 status=4,
#                 contract_status=1,  # new
#                 is_confirmed_contract=3,  # CLIENT_CONFIRMED
#                 payed_cash=0,
#                 # base64file=base64code,
#                 hashcode=hash_code,
#                 # like_preview_pdf=like_preview_pdf_path
#             )
#             expertise_service_contract.save()
#
#             context['id_code'] = expertise_service_contract.id_code
#
#             # rendered html file
#             contract_file_for_base64_pdf = None
#             template_name = "shablonYuridik.html"
#             pdf = render_to_pdf(template_src=template_name, context_dict=context)
#             if pdf:
#                 output_dir = '/usr/src/app/media/Contract/pdf'
#                 os.makedirs(output_dir, exist_ok=True)
#                 contract_file_for_base64_pdf = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
#                 with open(contract_file_for_base64_pdf, 'wb') as f:
#                     f.write(pdf.content)
#             else:
#                 error_response_500()
#
#             if contract_file_for_base64_pdf is None:
#                 error_response_500()
#
#             contract_file = open(contract_file_for_base64_pdf, 'rb').read()
#             base64code = base64.b64encode(contract_file)
#
#             # pdf fileni ochirish
#             delete_file(contract_file_for_base64_pdf)
#             # qr_code fileni ochirish
#             delete_file(qr_code_path)
#
#             # preview ni bazaga ham saqlab ketishim kk chunki contractni statusiga qarab foydalanish uchun
#             context['save'] = False
#             like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)
#
#             like_preview_pdf_path = None
#             if like_preview_pdf:
#                 output_dir = '/usr/src/app/media/Contract/pdf'
#                 os.makedirs(output_dir, exist_ok=True)
#                 like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('user_obj').get_director_short_full_name}.pdf"
#                 with open(like_preview_pdf_path, 'wb') as f:
#                     f.write(like_preview_pdf.content)
#             if like_preview_pdf_path is None:
#                 error_response_500()
#
#             expertise_service_contract.base64file = base64code
#             expertise_service_contract.like_preview_pdf = like_preview_pdf_path
#             expertise_service_contract.save()
#
#             for configuration_data in configuration_datas:
#                 operation_system_version_ids = configuration_data.configuration_data
#                 vps_device_tariff = None
#
#                 if configuration_data.tariff_id is not None:
#                     vps_device_tariff = VpsTariff.objects.get(id=configuration_data.tariff_id)
#
#                 for operation_system_version_id in operation_system_version_ids:
#                     operation_system_version = OperationSystemVersion.objects.get(id=operation_system_version_id)
#
#                     vps_device_get = VpsDevice.objects.get_or_create(
#                         storage_type=vps_device_tariff.vps_device if vps_device_tariff else configuration_data.vps_device,
#                         storage_disk=vps_device_tariff.storage_disk if vps_device_tariff else configuration_data.storage_disk,
#                         cpu=vps_device_tariff.cpu if vps_device_tariff else configuration_data.cpu,
#                         ram=vps_device_tariff.ram if vps_device_tariff else configuration_data.ram,
#                         internet=vps_device_tariff.internet if vps_device_tariff else configuration_data.internet,
#                         tasix=vps_device_tariff.tasix if vps_device_tariff else configuration_data.tasix,
#
#                         operation_system=operation_system_version.operation_system.first(),
#                         operation_system_version=operation_system_version
#                     )
#
#                     VpsContractDevice.objects.create(
#                         contract=expertise_service_contract,
#                         device=vps_device_get
#                     )
#
#             # ExpertiseContracts_Participants
#             # if the amount of the contract is less than 10 million,
#             # the director will not participate as a participant
#             exclude_role = None
#             # if expertise_service_contract.contract_cash < 10_000_000:
#             #     exclude_role = "direktor"
#
#             service_id = int(request.data['service'])
#             participants = self.create_contract_participants(service_id=service_id, exclude_role=exclude_role)
#             agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()
#
#             for participant in participants:
#                 VpsContracts_Participants.objects.create(
#                     contract=expertise_service_contract,
#                     role=participant.role,
#                     participant_user=participant,
#                     agreement_status=agreement_status
#                 ).save()
#
#             return response.Response(data={"message": "Created Expertise Service Contract"}, status=201)
#
#         template_name = "shablonYuridik.html"
#         return render(request=request, template_name=template_name, context=context)
