import os
import base64
import hashlib
import json
import math
import xmltodict
from decimal import Decimal

import requests
from django.http import HttpResponse
from django.core.exceptions import ValidationError

from datetime import datetime, timedelta

from django.db.models import Q, Sum
from django.shortcuts import redirect, render, get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, validators, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FizUser, UserData, Role, YurUser
from accounts.permissions import AdminPermission, SuperAdminPermission, WorkerPermission

from accounts.serializers import (
    FizUserSerializer, FizUserSerializerForContractDetail, YurUserSerializerForContractDetail,
    FizUserForOldContractSerializers, YurUserForOldContractSerializers
)

from services.models import Rack, Unit, DeviceUnit

from .permission import IsAuthenticatedAndOwner
from main.utils import responseErrorMessage

from .models import (
    Service, Tarif, Device, Offer, Document, SavedService, Element, UserContractTarifDevice,
    UserDeviceCount, Contract, Status, ContractStatus, AgreementStatus, Pkcs, ExpertSummary, Contracts_Participants,
    ConnetMethod, Participant, OldContractFile, ServiceParticipants
)

from .serializers import (
    ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer,
    OfferSerializer, DocumentSerializer, ElementSerializer, ContractSerializer, PkcsSerializer,
    ContractSerializerForContractList, ContractSerializerForBackoffice, ExpertSummarySerializer,
    ContractParticipantsSerializers, ExpertSummarySerializerForSave, ContractSerializerForDetail,
    ConnectMethodSerializer, AddOldContractSerializers, UserOldContractTarifDeviceSerializer,
    MonitoringContractSerializer, ServiceCreateSerializer
)

from .utils import (
    error_response_404, create_qr, NumbersToWord, convert_docx_to_pdf,
    delete_file, render_to_pdf, error_response_500
)

from .tasks import file_creator, file_downloader, generate_contract_number

num2word = NumbersToWord()


class ListAllServicesAPIView(generics.ListAPIView):
    queryset = Service.objects.all().order_by('id')
    permission_classes = ()
    serializer_class = ServiceSerializer


class ListGroupServicesAPIView(APIView):
    permission_classes = ()

    def get(self, request):
        group_id = request.GET.get('group_id')
        services = Service.objects.filter(group_id=group_id)
        serializers = ServiceSerializer(
            services, many=True, context={'request': request}
        )
        return Response(serializers.data)


class ServiceDetailAPIView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = ()


class UserDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        # Get values from request query parameters
        pin_or_tin = request.GET.get('pot')
        u_type = request.GET.get('ut')
        user, data = None, None

        # Check if pin_or_tin and u_type are present
        if pin_or_tin and u_type:
            if int(u_type) == 1:
                user = get_object_or_404(FizUser, pin=pin_or_tin)
                serializer = FizUserSerializerForContractDetail(user)
                data = serializer.data
                data['u_type'] = 'Fizik'
            elif int(u_type) == 2:
                user = get_object_or_404(YurUser, tin=pin_or_tin)
                serializer = YurUserSerializerForContractDetail(user)
                data = serializer.data
                data['u_type'] = 'Yuridik'

        # If pin_or_tin and u_type are not present, check user type and retrieve user object accordingly
        if user is None:
            if request.user.type == 1:
                user = get_object_or_404(FizUser, userdata=request.user)
                serializer = FizUserSerializerForContractDetail(user)
                data = serializer.data
                data['u_type'] = 'Fizik'
            else:
                user = get_object_or_404(YurUser, userdata=request.user)
                serializer = YurUserSerializerForContractDetail(user)
                data = serializer.data
                data['u_type'] = 'Yuridik'

            # Check if user role is not 'mijoz' and retrieve with_eds field from ServiceParticipants model
            if request.user.role.name != 'mijoz':
                try:
                    if request.user.role.name != 'direktor':
                        with_ads = ServiceParticipants.objects.get(
                            Q(role=request.user.role),
                            Q(participant__service__group=request.user.group)
                        ).with_eds
                    else:
                        with_ads = ServiceParticipants.objects.get(
                            Q(role=request.user.role),
                            Q(participant__service__group__name='Data Markaz')
                        ).with_eds
                    data["with_ads"] = with_ads
                except ServiceParticipants.DoesNotExist:
                    pass

        # Return data as a response
        return Response(data)


class TarifListAPIView(generics.ListAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class TariffCreateAPIView(generics.CreateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class TariffUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class DeviceListAPIView(generics.ListAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)


class OfferCreateAPIView(generics.CreateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = (AdminPermission,)


class OfferDetailAPIView(APIView):
    serializer_class = OfferSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            service_id = request.GET.get('service_id')
            offer = Offer.objects.get(service_id=service_id)
            serializer = OfferSerializer(offer, context={'request': request})
        except Offer.DoesNotExist:
            return Response({'message': 'Bunday xizmat mavjud emas'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetGroupAdminDataAPIView(APIView):
    permission_classes = ()

    def get(self, request):
        service_id = request.GET.get('service_id')
        service = Service.objects.get(pk=service_id)
        user = UserData.objects.get(
            Q(group__service=service), Q(role__name="bo'lim boshlig'i")
        )
        dt = FizUser.objects.get(userdata=user)
        serializer = FizUserSerializer(dt)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetPinnedUserDataAPIView(APIView):
    permission_classes = ()

    def get(self, request):
        service_id = request.GET.get('service_id')
        user = Service.objects.get(pk=service_id).pinned_user
        dt = FizUser.objects.get(userdata=user)
        serializer = FizUserSerializer(dt)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ServiceCreateAPIView(generics.CreateAPIView):
    # parser_classes = (MultiPartParser,)
    parser_classes = (FormParser,)
    queryset = Service.objects.all()
    serializer_class = ServiceCreateSerializer
    # permission_classes = (SuperAdminPermission,)

    # def perform_create(self, serializer):
    #     need_documents = self.request.data.get('need_documents')
    #     user_type = self.request.data.get('user_type')
    #     print(type(need_documents), need_documents)
    #
    #     if not need_documents or not user_type:
    #         response = responseErrorMessage(
    #             "need_documents and user_type are required fields",
    #             status_code=status.HTTP_400_BAD_REQUEST
    #         )
    #         raise ValidationError(response.data)
    #
    #     need_documents = json.dumps(need_documents)
    #     user_type = int(user_type)
    #
    #     serializer.save(
    #         need_documents=need_documents,
    #         user_type=user_type
    #     )


class SavedServiceAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        services = []
        try:
            saved_services = SavedService.objects.get(user=request.user)
        except SavedService.DoesNotExist:
            saved_services = None

        if saved_services:
            services = saved_services.services.all()

        serializer = ServiceSerializer(services, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Service ni saqlangan servicega qo'shish. Bu yerda service_id ni " "jo'natishiz kere bo'ladi"
    )
    def post(self, request):
        service_id = request.data['service_id']
        user = request.user
        service = Service.objects.get(pk=service_id)
        if SavedService.objects.filter(user=user).exists():
            saved_service = SavedService.objects.get(user=user)
        else:
            saved_service = SavedService.objects.create(user=user)
        if service not in saved_service.services.all():
            saved_service.services.add(service)
            saved_service.save()
        else:
            return Response({'message': 'Bu service oldindan mavjud'}, status=status.HTTP_302_FOUND)
        return Response(status=status.HTTP_200_OK)


class DeleteSavedService(APIView):
    def delete(self, request, pk):
        try:
            saved_service = SavedService.objects.get(user=request.user)
            service = Service.objects.get(pk=pk)
            saved_service.services.remove(service)
        except Exception as e:
            return Response({'message': f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TarifAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        group_id = request.GET.get('group_id')

        tarifs = Tarif.objects.filter(group_id=group_id)
        tarif_serializer = TarifSerializer(tarifs, many=True)

        elements = Element.objects.filter(group_id=group_id)
        element_serializer = ElementSerializer(elements, many=True)

        devices = Device.objects.all()
        device_serializer = DeviceSerializer(devices, many=True)

        return Response({
            'tarifs': tarif_serializer.data,
            'elements': element_serializer.data,
            'devices': device_serializer.data
        }, status=status.HTTP_200_OK)


class ConnectMethodListAPIView(generics.ListAPIView):
    queryset = ConnetMethod.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ConnectMethodSerializer


class SelectedTarifDevicesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        devices = request.data['devices']
        electricity = 0
        lishniy_electricity = 0
        price = 0
        tarif = Tarif.objects.get(pk=int(request.data['tarif']))
        if tarif.name == 'Rack-1':
            for device in devices:
                electricity += int(device['electricity']) * int(device['device_count'])
            if electricity > int(request.data['rack_count']) * 7500:
                lishniy_electricity = electricity - int(request.data['rack_count']) * 7500
            price = tarif.price * int(request.data['rack_count']) + math.ceil(lishniy_electricity / 100) * 23000
        else:
            for device in devices:
                unit_count = int(device['device_count']) * int(device['units_count'])
                if int(device['electricity']) > 450:
                    lishniy_electricity = int(device['electricity']) - 450
                price += tarif.price * unit_count + math.ceil(lishniy_electricity / 100) * 23000 * int(
                    device['device_count'])

        if not request.data['rack_count']:
            request.data['rack_count'] = None
        if not request.data['odf_count']:
            request.data['odf_count'] = None
        else:
            price += int(request.data['odf_count']) * int(
                ConnetMethod.objects.get(pk=int(request.data['connect_method'])).price)
        user_selected_tarif_devices = UserContractTarifDevice.objects.create(
            contract_id=request.data['contract_id'],
            client=request.user,
            service_id=request.data['service_id'],
            tarif=tarif,
            rack_count=request.data['rack_count'],
            connect_method=ConnetMethod.objects.get(
                pk=int(request.data['connect_method'])),
            odf_count=request.data['odf_count'],
            price=price
        )
        user_selected_tarif_devices.save()
        for device in devices:
            user_device_count = UserDeviceCount.objects.create(
                user=user_selected_tarif_devices,
                device_id=device['id'],
                device_count=device['device_count'],
                units_count=device['units_count'],
                electricity=device['electricity'],
            )
            user_device_count.save()
        return Response({'price': price})


# class CreateContractFileAPIView(APIView):
#     permission_classes = (IsAuthenticated,)

#     def post(self, request):
#         context = dict()
#         tarif = Tarif.objects.get(pk=int(request.data['tarif'])).name

#         try:
#             number = Contract.objects.last().id + 1
#         except AttributeError:
#             number = 1
#         prefix = Service.objects.get(pk=int(request.data['service_id'])).group.prefix

#         if request.user.type == 2:
#             context['u_type'] = 'yuridik'
#             context['contract_number'] = prefix + '-' + str(number)  # --
#             context['year'] = datetime.now().year
#             context['month'] = datetime.now().month
#             context['day'] = datetime.now().day
#             context['client'] = request.data['name']
#             context['client_fullname'] = request.data['director_fullname']
#             director = request.data['director_fullname'].split()
#             context['director'] = f"{director[1][0]}.{director[2][0]}.{director[0]}"
#             context['price'] = int(request.data['price']) * 12 - int(datetime.now().month)
#             context['price_text'] = num2word.change_num_to_word(int(context['price']))
#             context['price_month'] = request.data['price']
#             context['price_month_text'] = num2word.change_num_to_word(int(context['price_month']))
#             context['price_month_avans'] = request.data['price']
#             context['price_month_avans_text'] = context['price_month_text']
#             context['per_adr'] = request.data['per_adr']
#             context['tin'] = request.data['tin']
#             context['mfo'] = request.data['mfo']
#             context['oked'] = request.data['oked']
#             context['hr'] = request.data['hr']
#             context['bank'] = request.data['bank']
#             context['tarif'] = tarif
#             context['count'] = request.data['count']
#             context['price2'] = request.data['price']
#             context['host'] = 'http://' + request.META['HTTP_HOST']
#         else:
#             context['u_type'] = 'fizik'
#             context['contract_number'] = prefix + '-' + str(number)
#             context['year'] = datetime.now().year
#             context['month'] = datetime.now().month
#             context['day'] = datetime.now().day
#             context['pport_issue_place'] = request.data['pport_issue_place']
#             context['pport_issue_date'] = request.data['pport_issue_date']
#             context['pport_no'] = request.data['pport_no']
#             client_short = request.data['full_name'].split()
#             context['client'] = f"{client_short[1][0]}.{client_short[2][0]}.{client_short[0]}"
#             context['client_fullname'] = request.data['full_name']
#             context['price'] = int(request.data['price']) * (12 - int(datetime.now().month) + 1)
#             context['price_text'] = num2word.change_num_to_word(int(context['price']))
#             context['price_month'] = request.data['price']
#             context['price_month_text'] = num2word.change_num_to_word(int(context['price_month']))
#             context['price_month_avans'] = request.data['price']
#             context['price_month_avans_text'] = context['price_month_text']
#             context['per_adr'] = request.data['per_adr']
#             context['pin'] = request.data['pin']
#             context['tarif'] = tarif
#             context['count'] = request.data['count']
#             context['price2'] = request.data['price']
#             context['host'] = 'http://' + request.META['HTTP_HOST']

#         context['qr_code'] = ''
#         # -------
#         # dxoc file
#         # contract_file_for_preview = file_creator(context, 1)
#         # pdf file
#         # contract_file_for_preview_pdf = convert_docx_to_pdf(str(contract_file_for_preview))
#         # docx file ni ochirish
#         # delete_file(contract_file_for_preview)
#         # -------
#         hashcode = hashlib.md5()
#         hashcode.update(base64.b64encode(open(contract_file_for_preview_pdf, 'rb').read()))
#         hash_code = hashcode.hexdigest()

#         link = 'http://' + request.META['HTTP_HOST'] + '/contracts/contract?hash=' + hash_code

#         # direktor = YurUser.objects.get(userdata__role__name="direktor")
#         # direktor_fullname = f"{direktor.director_lastname} {direktor.first_name} {direktor.mid_name}"

#         # context['qr_code'] = create_qr(link)
#         # # -------
#         # # docx file
#         # contract_file_for_base64 = file_creator(context, 0)
#         # # pdf file
#         # contract_file_for_base64_pdf = convert_docx_to_pdf(str(contract_file_for_base64))
#         # # docx fileni ochirish
#         # # delete_file(contract_file_for_base64)
#         # # -------
#         # contract_file = open(contract_file_for_base64_pdf, 'rb').read()

#         # base64code = base64.b64encode(contract_file)

#         if int(request.data['save']):

#             context['qr_code'] = create_qr(link)
#             # -------
#             # rendered html file
#             contract_file_for_base64 = file_creator(context, 0)
#             # pdf file
#             contract_file_for_base64_pdf = convert_docx_to_pdf(str(contract_file_for_base64))
#             # -------
#             contract_file = open(contract_file_for_base64_pdf, 'rb').read()

#             base64code = base64.b64encode(contract_file)

#             status = Status.objects.filter(name='Yangi').first()
#             contract_status = ContractStatus.objects.filter(name='Yangi').first()
#             agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()

#             if request.user.role.name == 'mijoz':
#                 client = request.user
#             else:
#                 client = request.data['client']

#             contract = Contract.objects.create(
#                 service_id=int(request.data['service_id']),
#                 contract_number=context['contract_number'],
#                 contract_date=datetime.now(),
#                 client=client,
#                 status=status,
#                 contract_status=contract_status,
#                 contract_cash=int(context['price_month']),
#                 payed_cash=0,
#                 tarif_id=int(request.data['tarif']),
#                 base64file=base64code,
#                 hashcode=hash_code,
#             )
#             contract.save()

#             # pdf fileni ochirish
#             # delete_file(contract_file_for_base64)

#             # service = contract.service.name

#             participants = Participant.objects.get(service_id=int(request.data['service_id'])).participants.all()
#             for participant in participants:
#                 Contracts_Participants.objects.create(
#                     contract=contract,
#                     role=participant,
#                     agreement_status=agreement_status
#                 ).save()

#             serializer = ContractSerializer(contract)
#             return Response(serializer.data)

#         # Saqlanmedigan filelarni logikasini qolishim kk
#         # qr_code fileni ochirish kk
#         # 
#         # return Response({
#         #     'file_path': '/media/Contract/' + str(contract_file_for_preview_pdf).split('/')[-1],
#         #     'file_path_doc': '/media/Contract/' + str(contract_file_for_preview).split('/')[-1],
#         #     'base64file': base64code
#         # })
#         return 


class CreateContractFileAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def generate_hash_code(text: str):
        hashcode = hashlib.md5(text.encode())
        hash_code = hashcode.hexdigest()
        return hash_code

    def post(self, request):
        context = dict()
        tarif = Tarif.objects.get(pk=int(request.data['tarif'])).name

        try:
            number = Contract.objects.last().id + 1
        except AttributeError:
            number = 1
        prefix = Service.objects.get(pk=int(request.data['service_id'])).group.prefix

        if request.user.type == 2:
            context['u_type'] = 'yuridik'
            context['contract_number'] = prefix + '-' + str(number)  # --
            context['year'] = datetime.now().year
            context['month'] = datetime.now().month
            context['day'] = datetime.now().day
            context['client'] = request.data['name']
            context['client_fullname'] = request.data['director_fullname']
            director = request.data['director_fullname'].split()
            context['director'] = f"{director[1][0]}.{director[2][0]}.{director[0]}"
            context['price'] = int(request.data['price']) * 12 - int(datetime.now().month)
            context['price_text'] = num2word.change_num_to_word(int(context['price']))
            context['price_month'] = request.data['price']
            context['price_month_text'] = num2word.change_num_to_word(int(context['price_month']))
            context['price_month_avans'] = request.data['price']
            context['price_month_avans_text'] = context['price_month_text']
            context['per_adr'] = request.data['per_adr']
            context['tin'] = request.data['tin']
            context['mfo'] = request.data['mfo']
            context['oked'] = request.data['oked']
            context['hr'] = request.data['hr']
            context['bank'] = request.data['bank']
            context['tarif'] = tarif
            context['count'] = request.data['count']
            context['price2'] = request.data['price']
            context['host'] = 'http://' + request.META['HTTP_HOST']
            context["get_director_short_full_name"] = YurUser.objects.get(
                userdata=request.user).get_director_short_full_name
        else:
            context['u_type'] = 'fizik'
            context['contract_number'] = prefix + '-' + str(number)
            context['year'] = datetime.now().year
            context['month'] = datetime.now().month
            context['day'] = datetime.now().day
            context['pport_issue_place'] = request.data['pport_issue_place']
            context['pport_issue_date'] = request.data['pport_issue_date']
            context['pport_no'] = request.data['pport_no']
            client_short = request.data['full_name'].split()
            context['client'] = f"{client_short[1][0]}.{client_short[2][0]}.{client_short[0]}"
            context['client_fullname'] = request.data['full_name']
            context['price'] = int(request.data['price']) * (12 - int(datetime.now().month) + 1)
            context['price_text'] = num2word.change_num_to_word(int(context['price']))
            context['price_month'] = request.data['price']
            context['price_month_text'] = num2word.change_num_to_word(int(context['price_month']))
            context['price_month_avans'] = request.data['price']
            context['price_month_avans_text'] = context['price_month_text']
            context['per_adr'] = request.data['per_adr']
            context['pin'] = request.data['pin']
            context['tarif'] = tarif
            context['count'] = request.data['count']  # tariff count
            context['price2'] = request.data['price']  # jami summa
            context['host'] = 'http://' + request.META['HTTP_HOST']
            context["get_short_full_name"] = FizUser.objects.get(userdata=request.user).get_short_full_name

        context['qr_code'] = ''
        context['save'] = False
        # context['devices'] = request.data.get("devices", None)
        context['page_break'] = False
        context['datetime'] = datetime.now().strftime('%d.%m.%Y')

        if int(request.data['save']):
            context['save'] = True
            context['page_break'] = True
            context['contract_number'] = prefix + '-' + str(number)  # --
            context['id_code'] = f'C{number}'
            hash_code = self.generate_hash_code(
                text=f"{context.get('client_fullname')}{context.get('contract_number')}{context.get('u_type')}{datetime.now()}"
            )

            link = 'http://' + request.META['HTTP_HOST'] + f'/contracts/contract/{hash_code}'
            qr_code_path = create_qr(link)
            context['hash_code'] = hash_code
            context['qr_code'] = f"http://api2.unicon.uz/media/qr/{hash_code}.png"

            # -------
            # rendered html file
            # contract_file_for_base64 = file_creator(context, 0)
            # pdf file
            # contract_file_for_base64_pdf = convert_docx_to_pdf(str(contract_file_for_base64))
            contract_file_for_base64_pdf = None

            template_name = "shablonFizik.html"  # fizik
            if request.user.type == 2:  # yuridik
                template_name = "shablonYuridik.html"

            pdf = render_to_pdf(template_src=template_name, context_dict=context)
            if pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                contract_file_for_base64_pdf = f"{output_dir}/{context.get('contract_number')}_{context.get('client_fullname').replace(' ', '_')}.pdf"
                with open(contract_file_for_base64_pdf, 'wb') as f:
                    f.write(pdf.content)
            else:
                error_response_500()

            if contract_file_for_base64_pdf is None:
                error_response_500()

            # -------
            contract_file = open(contract_file_for_base64_pdf, 'rb').read()
            base64code = base64.b64encode(contract_file)

            # direktor = YurUser.objects.get(userdata__role__name="direktor")
            # direktor_fullname = f"{direktor.director_lastname} {direktor.first_name} {direktor.mid_name}"

            status = Status.objects.filter(name='Yangi').first()
            contract_status = ContractStatus.objects.filter(name='Yangi').first()
            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()
            client = request.user

            # pdf fileni ochirish
            delete_file(contract_file_for_base64_pdf)
            # qr_code fileni ochirish
            delete_file(qr_code_path)

            # -------
            # preview ni bazaga ham saqlab ketishim kk chunki contractni statusiga qarab foydalanish uchun
            context['save'] = False
            like_preview_pdf = render_to_pdf(template_src=template_name, context_dict=context)
            like_preview_pdf_path = None
            if like_preview_pdf:
                output_dir = '/usr/src/app/media/Contract/pdf'
                os.makedirs(output_dir, exist_ok=True)
                like_preview_pdf_path = f"{output_dir}/{context.get('contract_number')}_{context.get('client_fullname')}.pdf"
                with open(like_preview_pdf_path, 'wb') as f:
                    f.write(like_preview_pdf.content)
            elif like_preview_pdf_path is None:
                error_response_500()
            else:
                error_response_500()

            contract = Contract.objects.create(
                service_id=int(request.data['service_id']),
                contract_number=context['contract_number'],
                contract_date=datetime.now(),
                client=client,
                status=status,
                contract_status=contract_status,
                contract_cash=int(context['price_month']),
                payed_cash=0,
                tarif_id=int(request.data['tarif']),
                base64file=base64code,
                hashcode=hash_code,
                like_preview_pdf=like_preview_pdf_path
            )
            contract.save()

            # service = contract.service.name

            participants = Participant.objects.get(service_id=int(request.data['service_id'])).participants.all()
            for participant in participants:
                Contracts_Participants.objects.create(
                    contract=contract,
                    role=participant,
                    agreement_status=agreement_status
                ).save()

            serializer = ContractSerializer(contract)
            return Response(serializer.data)

        template_name = "shablonFizik.html"  # fizik
        if request.user.type == 2:  # yuridik
            template_name = "shablonYuridik.html"

        return render(request=request, template_name=template_name, context=context)


class SavePkcs(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PkcsSerializer

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
        res = requests.post('http://dsv-server-vpn-client:9090/dsvs/pkcs7/v1',
                            data=xml, headers=headers)
        dict_data = xmltodict.parse(res.content)
        response = dict_data['S:Envelope']['S:Body']['ns2:verifyPkcs7Response']['return']
        d = json.loads(response)
        return d

    def post(self, request):
        contract_id = int(request.data['contract_id'])
        pkcs7 = request.data['pkcs7']
        try:
            contract = Contract.objects.get(pk=contract_id)
            if request.user.role in Contracts_Participants.objects.filter(contract=contract).values('role'):
                if not Pkcs.objects.filter(contract=contract).exists():
                    pkcs = Pkcs.objects.create(contract=contract, pkcs7=pkcs7)
                    pkcs.save()
                else:
                    pkcs_exist_object = Pkcs.objects.get(contract=contract)
                    client_pkcs = pkcs_exist_object.pkcs7
                    new_pkcs7 = self.join2pkcs(pkcs7, client_pkcs)
                    pkcs_exist_object.pkcs7 = new_pkcs7
                    pkcs_exist_object.save()
        except Contract.DoesNotExist:
            return Response({'message': 'Bunday shartnoma mavjud emas'})
        return Response({'message': 'Success'})


class GetContractFile(APIView):
    permission_classes = ()

    def get(self, request, hash_code):
        if hash_code is None:
            return Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)
        contract = get_object_or_404(Contract, hashcode=hash_code)

        if contract.contract_status.name == "To'lov kutilmoqda" or contract.contract_status.name == 'Aktiv':
            # delete like pdf file test mode
            if contract.like_preview_pdf:
                delete_file(contract.like_preview_pdf.path)
                contract.like_preview_pdf = None
                contract.save()

            file_pdf_path, pdf_file_name = file_downloader(
                bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'), contract.id
            )
            if os.path.exists(file_pdf_path):
                with open(file_pdf_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/pdf")
                    response['Content-Disposition'] = f'attachment; filename="{pdf_file_name}"'
                    delete_file(file_pdf_path)
                    return response
        else:
            if contract.like_preview_pdf:
                # Open the file and create a response with the PDF data
                with open(contract.like_preview_pdf.path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename={contract.contract_number}.pdf'
                    return response

        return Response(data={"message": "404 not found error"}, status=status.HTTP_404_NOT_FOUND)


class GetUserContracts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        contracts = Contract.objects.filter(client=request.user)
        serializer = ContractSerializerForContractList(contracts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetContractFileWithID(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pk = request.GET.get('pk')
        contract = Contract.objects.get(pk=pk)
        file_pdf = file_downloader(
            bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'), contract.id)
        return redirect(u'/media/Contract/' + file_pdf)


class ContractDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        contract = Contract.objects.select_related('client').get(pk=pk)
        contract_serializer = ContractSerializerForDetail(contract)
        try:
            if request.user.role.name != 'direktor':
                contract_participants = Contracts_Participants.objects.filter(contract=contract).get(
                    Q(role=request.user.role),
                    Q(contract__service__group=request.user.group))
            else:
                contract_participants = Contracts_Participants.objects.filter(
                    contract=contract).get(role=request.user.role)
        except Contracts_Participants.DoesNotExist:
            contract_participants = None

        if (request.user.role.name == "bo'lim boshlig'i" or
            request.user.role.name == "direktor o'rinbosari" or
            request.user.role.name == "dasturchi" or
            request.user.role.name == "direktor") and \
                (contract_participants.agreement_status.name == "Yuborilgan"):
            agreement_status = AgreementStatus.objects.get(name="Ko'rib chiqilmoqda")
            contract_participants.agreement_status = agreement_status
            contract_participants.save()

        client = contract.client

        if client.type == 2:
            user = YurUser.objects.get(userdata=client)
            client_serializer = YurUserSerializerForContractDetail(user)
        else:
            user = FizUser.objects.get(userdata=client)
            client_serializer = FizUserSerializer(user)

        participants = Contracts_Participants.objects.filter(contract=contract).order_by('role_id')
        participant_serializer = ContractParticipantsSerializers(participants, many=True)
        try:
            if request.user.role.name == 'direktor':
                expert_summary_value = ExpertSummary.objects.get(
                    Q(contract=contract),
                    Q(user=request.user),
                    Q(user__group=request.user.group)
                ).summary
            else:
                expert_summary_value = ExpertSummary.objects.get(
                    Q(contract=contract),
                    Q(user=request.user),
                    Q(user__group=request.user.group)
                ).summary
        except ExpertSummary.DoesNotExist:
            expert_summary_value = 0

        if int(expert_summary_value) == 1:
            expert_summary = True
        else:
            expert_summary = False

        return Response(
            {
                'contract': contract_serializer.data,
                'client': client_serializer.data,
                'participants': participant_serializer.data,
                'is_confirmed': expert_summary
            }, status=status.HTTP_200_OK
        )


class GetGroupContract(APIView):
    permission_classes = (IsAuthenticated,)

    # @cache_page(60 * 15, cache='default')
    def get(self, request):
        group = request.user.group
        if request.user.role.name != "mijoz":

            contracts = None
            barcha_data = Contract.objects.all().order_by('-condition', '-contract_date')
            barcha = ContractSerializerForBackoffice(barcha_data, many=True)
            if request.user.role.name == 'direktor':
                contract_participants = Contracts_Participants.objects.filter(
                    Q(role__name="direktor o'rinbosari"),
                    Q(agreement_status__name='Kelishildi')
                ).values('contract')
                director_accepted_contracts = Contracts_Participants.objects.filter(
                    Q(role__name='direktor'), Q(agreement_status__name='Kelishildi')
                ).values('contract')
                yangi_data = Contract.objects.filter(Q(id__in=contract_participants), Q(contract_status__name="Yangi")) \
                    .exclude(Q(id__in=director_accepted_contracts)).select_related().order_by('-condition',
                                                                                              '-contract_date')
            else:
                contract_participants = Contracts_Participants.objects.filter(
                    Q(role=request.user.role),
                    (Q(agreement_status__name='Yuborilgan') |
                     Q(agreement_status__name="Ko'rib chiqilmoqda"))
                ).values('contract')
                yangi_data = Contract.objects.filter(Q(id__in=contract_participants),
                                                     Q(contract_status__name="Yangi")).exclude(
                    Q(contract_status__name="Bekor qilingan") | Q(contract_status__name="Rad etilgan")).select_related() \
                    .order_by('-condition', '-contract_date')
            yangi = ContractSerializerForBackoffice(yangi_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(role=request.user.role),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')
            kelishilgan_data = Contract.objects.filter(id__in=contract_participants).select_related() \
                .order_by('-condition', '-contract_date')
            kelishilgan = ContractSerializerForBackoffice(kelishilgan_data, many=True)
            rad_etildi_data = Contract.objects.filter(Q(contract_status__name='Bekor qilingan') | \
                                                      Q(contract_status__name="Rad etilgan")) \
                .order_by('-condition', '-contract_date')
            rad_etildi = ContractSerializerForBackoffice(
                rad_etildi_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            expired_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__lt=datetime.now() - timedelta(days=1))).select_related().exclude(
                Q(contract_status__name='Bekor qilingan') | Q(contract_status__name="Rad etilgan")) \
                .order_by('-condition', '-contract_date')
            expired = ContractSerializerForBackoffice(expired_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(role=request.user.role),
                (Q(agreement_status__name='Yuborilgan') |
                 Q(agreement_status__name="Ko'rib chiqilmoqda"))
            ).values('contract')
            lastday_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__day=datetime.now().day),
                Q(contract_date__month=datetime.now().month),
                Q(contract_date__year=datetime.now().year)).exclude(
                Q(contract_status__name='Bekor qilingan') | Q(contract_status__name='Rad etilgan')).select_related() \
                .order_by('-condition', '-contract_date')
            lastday = ContractSerializerForBackoffice(lastday_data, many=True)
            contract_participants = Contracts_Participants.objects.filter(
                Q(role=request.user.role),
                Q(agreement_status__name='Kelishildi')
            ).values('contract')
            expired_accepted_data = Contract.objects.filter(
                Q(id__in=contract_participants),
                Q(contract_date__lt=datetime.now() - timedelta(days=1))
            ).select_related().order_by('-condition', '-contract_date')
            expired_accepted = ContractSerializerForBackoffice(
                expired_accepted_data, many=True)
            contracts_selected = ExpertSummary.objects.select_related('contract').filter(
                Q(user=request.user)).order_by('-contract__condition', '-contract__contract_date')
            in_time_data = [element.contract for element in contracts_selected if
                            element.contract.contract_date < element.date <= element.contract.contract_date + timedelta(
                                days=1)]
            in_time = ContractSerializerForBackoffice(in_time_data, many=True)
            contracts = {
                'barcha': barcha.data,
                'yangi': yangi.data,
                'kelishildi': kelishilgan.data,
                'rad_etildi': rad_etildi.data,
                'expired': expired.data,
                'lastday': lastday.data,
                'expired_accepted': expired_accepted.data,
                'in_time': in_time.data
            }
            return Response(contracts)
        else:
            contracts = Contract.objects.filter(
                Q(service__group=group), Q(condition=3))
            serializer = ContractSerializerForBackoffice(contracts, many=True)
            return Response(serializer.data)


class ConfirmContract(APIView):
    permission_classes = (WorkerPermission,)

    def post(self, request):
        contract = Contract.objects.get(pk=int(request.data['contract']))
        self.check_object_permissions(request=request, obj=contract)

        if int(request.data['summary']) == 1:  # 1 -> muofiq, 0 -> muofiq emas
            agreement_status = AgreementStatus.objects.get(name='Kelishildi')
        else:
            agreement_status = AgreementStatus.objects.get(name='Rad etildi')
            contract.contract_status = ContractStatus.objects.get(name='Rad etilgan')

        contracts_participants = Contracts_Participants.objects.get(
            Q(contract=contract),
            Q(role=request.user.role),
            # Q(contract__service__group__name='Data Markaz'),
        )
        contracts_participants.agreement_status = agreement_status
        contracts_participants.save()
        contract.condition += 1

        try:
            cntrct = Contracts_Participants.objects.get(
                Q(contract=contract),
                Q(role__name='direktor'),
                Q(agreement_status__name='Kelishildi')
            )
        except Contracts_Participants.DoesNotExist:
            cntrct = None

        if cntrct:
            contract.contract_status = ContractStatus.objects.get(name="To'lov kutilmoqda")
        contract.save()

        request.data._mutable = True
        request.data['user'] = request.user.id

        try:
            documents = request.FILES.getlist('documents', None)
        except:
            documents = None

        summary = ExpertSummarySerializerForSave(
            data=request.data, context={'documents': documents}
        )
        summary.is_valid(raise_exception=True)
        summary.save()

        return Response(status=200)


class DeleteUserContract(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        contract_id = request.data['contract']
        contract = Contract.objects.get(pk=contract_id)
        contract.contract_status = ContractStatus.objects.get(name="Bekor qilingan")
        contract.save()

        return Response({'message': 'Deleted'}, status=status.HTTP_200_OK)


class GetRackContractDetailWithNumber(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        contract_number = request.GET.get('contract_number')
        rack_id = int(request.GET.get('rack_id'))
        contract = Contract.objects.get(contract_number=contract_number)
        serializer = ContractSerializerForBackoffice(contract)
        try:
            user_contract_tariff_device = UserContractTarifDevice.objects.get(
                Q(contract=contract),
                Q(tarif__name='Rack-1')
            )
        except UserContractTarifDevice.DoesNotExist:
            data = {
                'success': False,
                'message': 'Shartnoma rack ga tuzilmagan yoki bunday shartnoma mavjud emas!'
            }
            return Response(data, status=405)
        rack_count = user_contract_tariff_device.rack_count
        filled = Rack.objects.filter(Q(is_sold=True), Q(contract=contract)).count()
        empty = rack_count - filled
        odf_count = user_contract_tariff_device.odf_count
        provider = ConnetMethod.objects.get(pk=user_contract_tariff_device.connect_method.id)
        provider_serializer = ConnectMethodSerializer(provider)
        electricity = 7500
        devices = DeviceUnit.objects.filter(rack_id=rack_id).order_by('id')
        s = 0
        for i in devices:
            s += i.electricity
        data = {
            'contract': serializer.data,
            'count': rack_count,
            'empty': empty,
            'odf_count': odf_count,
            'provider': provider_serializer.data,
            'electricity': electricity,
            'busy_electricity': s
        }
        return Response(data)


class GetUnitContractDetailWithNumber(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        contract_number = request.GET.get('contract_number')
        contract = Contract.objects.get(contract_number=contract_number)
        serializer = ContractSerializerForBackoffice(contract)
        try:
            user_contract_tariff_device = UserContractTarifDevice.objects.get(
                Q(contract=contract),
                Q(tarif__name='Unit-1')
            )
        except UserContractTarifDevice.DoesNotExist:
            data = {
                'success': False,
                'message': 'Shartnoma unit ga tuzilmagan yoki bunday shartnoma mavjud emas!'
            }
            return Response(data, status=405)
        user_device_count = UserDeviceCount.objects.filter(
            user=user_contract_tariff_device
        )
        summ = 0
        electricity = 0
        for i in user_device_count:
            summ += i.device_count * i.units_count
            electricity += i.electricity * i.units_count

        empty_electricity = DeviceUnit.objects.filter(
            Q(rack__unit__contract=contract),
            Q(status__name="o'rnatilgan")
        )
        test = empty_electricity.aggregate(Sum('electricity'))
        print(empty_electricity)
        print(test)

        empty = summ - Unit.objects.filter(Q(is_busy=True), Q(contract=contract)).count()
        odf_count = user_contract_tariff_device.odf_count

        provider = ConnetMethod.objects.get(
            pk=user_contract_tariff_device.connect_method.id
        )

        provider_serializer = ConnectMethodSerializer(provider)
        data = {
            'contract': serializer.data,
            'count': summ,
            'empty': empty,
            'odf_count': odf_count,
            'provider': provider_serializer.data,
            'electricity': electricity,
            'empty_electricity': empty_electricity
        }
        return Response(data)


# BackOffice da admin eski qog'ozdegi shartnomalarni scaner qilib tizimga qo'shadi
def total_old_contract_price(electricity, tarif_pk, tarif_count, connect_method_pk, connect_method_count=None,
                             if_tarif_is_unit=None):
    tarif = Tarif.objects.get(id=tarif_pk.id)
    connect_method = ConnetMethod.objects.get(id=connect_method_pk.id)

    price = tarif.price * tarif_count

    if tarif.name == 'Rack-1':
        working_electricity = tarif_count * 7500
        if electricity > working_electricity:
            price += math.ceil((electricity - working_electricity) / 100) * 23_000

    else:
        working_electricity = if_tarif_is_unit * 450
        if electricity > working_electricity:
            a = Decimal(math.ceil((electricity - working_electricity) / 100) * 23000)
            price += a

    if connect_method.name == 'ODF':

        if connect_method_count > 1:
            price += (connect_method_count - 1) * connect_method.price

    return price


class AddOldContractsViews(APIView):
    serializer_class_yur_user = YurUserForOldContractSerializers
    serializer_class_fiz_user = FizUserForOldContractSerializers
    serializer_class_contract = AddOldContractSerializers
    serializer_class_contract_tarif_device = UserOldContractTarifDeviceSerializer

    permission_classes = [IsAuthenticated]
    userTtype = {
        "fiz": True,
        "yur": False
    }

    def post(self, request, *args, **kwargs):
        # Get the value of the "type" argument from the URL
        # Look up the corresponding constant value in the model based on the string argument
        type_u = self.userTtype.get(kwargs.get("usertype", "").lower(), None)
        # If the argument is not recognized, return a 404 error response
        if type_u is None:
            error_response_404()

        role_user = Role.objects.get(name="mijoz")

        # if user is fiz human
        if type_u:
            pin = request.data.get("pin", None)
            first_name = request.data.get("first_name", None)
            file = request.FILES.get('file', None)

            if not pin or not first_name or not file:
                raise validators.ValidationError(detail={
                    "error msg": "pin, file or first name will not be empty"
                }, code=status.HTTP_400_BAD_REQUEST)

            if UserData.objects.filter(username=pin).exists():
                user_obj = UserData.objects.get(username=pin)
            else:
                user_obj = UserData(
                    username=str(pin),
                    type=1,
                    first_name=first_name,
                    last_name=request.data.get("last_name"),
                    role=role_user
                )
                user_obj.set_password(first_name[0].upper() + pin + first_name[-1].upper())
                user_obj.save()
            if FizUser.objects.filter(userdata=user_obj).exists():
                user = FizUser.objects.get(userdata=user_obj)
            else:
                serializer_class_user = self.serializer_class_fiz_user(data=request.data)
                serializer_class_user.is_valid(raise_exception=True)
                user = serializer_class_user.save(
                    userdata=user_obj, user_type=1
                )

            contract_tarif_device_serializer = self.serializer_class_contract_tarif_device(data=request.data)
            contract_tarif_device_serializer.is_valid(raise_exception=True)

            price_total_old_contract = total_old_contract_price(
                electricity=contract_tarif_device_serializer.validated_data.get("total_electricity"),
                tarif_pk=contract_tarif_device_serializer.validated_data.get("tarif"),
                tarif_count=contract_tarif_device_serializer.validated_data.get("rack_count"),
                connect_method_pk=contract_tarif_device_serializer.validated_data.get("connect_method"),
                connect_method_count=contract_tarif_device_serializer.validated_data.get("odf_count"),
                if_tarif_is_unit=int(request.data.get("if_tarif_is_unit", 0))
            )

            # today = datetime.now().date()
            # prefix = 'CC'
            # id_code = generate_contract_number(today, prefix)

            contract_serializer = self.serializer_class_contract(data=request.data)
            contract_serializer.is_valid(raise_exception=True)
            contract = contract_serializer.save(
                client=user_obj,
                # id_code=id_code,
                contract_cash=price_total_old_contract,
                payed_cash=0,  # payed cash is 0, now
                status=Status.objects.get(name="Jarayonda"),
                contract_status=ContractStatus.objects.get(name="Aktiv")
            )

            file = request.FILES.get('file', None)
            if file:
                OldContractFile.objects.create(contract=contract, file=file)

            contract_tarif_device = contract_tarif_device_serializer.save(
                contract=contract, client=user_obj, price=price_total_old_contract
            )

            UserDeviceCount.objects.create(
                user=contract_tarif_device,
                device=Device.objects.get(name='Server'),
                device_count=int(request.data.get("if_tarif_is_unit", 0)),
                units_count=contract_tarif_device_serializer.validated_data.get("rack_count"),
                electricity=contract_tarif_device_serializer.validated_data.get("total_electricity")
            )

            service_participants = ServiceParticipants.objects.filter(participant__service=contract.service)

            kelishildi = AgreementStatus.objects.get(name="Kelishildi")

            for obj in service_participants:
                Contracts_Participants.objects.create(
                    contract=contract,
                    role=obj.role,
                    agreement_status=kelishildi
                )

            return Response({
                'user-data': self.serializer_class_fiz_user(user).data,
                'contract-data': self.serializer_class_contract(contract).data,
                'tarif': self.serializer_class_contract_tarif_device(contract_tarif_device).data
            }, status=status.HTTP_201_CREATED)

        # else user is Yur human
        else:
            tin = request.data.get("tin", None)
            director_firstname = request.data.get("director_firstname", None)
            file = request.FILES.get('file', None)

            if not tin or not director_firstname or not file:
                raise validators.ValidationError(detail={
                    "error msg": "tin, file or director-firstname will not be empty"
                }, code=status.HTTP_400_BAD_REQUEST)

            if UserData.objects.filter(username=tin).exists():
                user_obj = UserData.objects.get(username=tin)
            else:
                user_obj = UserData(
                    username=str(request.data.get("tin")),
                    type=2,
                    role=role_user,
                )
                user_obj.set_password(director_firstname[0].upper() + tin + director_firstname[-1].upper())
                user_obj.save()
            if YurUser.objects.filter(userdata=user_obj).exists():
                user = YurUser.objects.get(userdata=user_obj)
            else:
                serializer_class_user = self.serializer_class_yur_user(data=request.data)
                serializer_class_user.is_valid(raise_exception=True)
                user = serializer_class_user.save(
                    userdata=user_obj, user_type=2
                )

            contract_tarif_device_serializer = self.serializer_class_contract_tarif_device(data=request.data)
            contract_tarif_device_serializer.is_valid(raise_exception=True)

            price_total_old_contract = total_old_contract_price(
                electricity=contract_tarif_device_serializer.validated_data.get("total_electricity"),
                tarif_pk=contract_tarif_device_serializer.validated_data.get("tarif"),
                tarif_count=contract_tarif_device_serializer.validated_data.get("rack_count"),
                connect_method_pk=contract_tarif_device_serializer.validated_data.get("connect_method"),
                connect_method_count=contract_tarif_device_serializer.validated_data.get("odf_count"),
                if_tarif_is_unit=int(request.data.get("if_tarif_is_unit", 0))

            )

            # today = datetime.now().date()
            # prefix = 'CC'
            # id_code = generate_contract_number(today, prefix)

            contract_serializer = self.serializer_class_contract(data=request.data)
            contract_serializer.is_valid(raise_exception=True)
            contract = contract_serializer.save(
                client=user_obj,
                # id_code=id_code,
                contract_cash=price_total_old_contract,
                payed_cash=0,  # payed cash is 0, now
                status=Status.objects.get(name="Jarayonda"),
                contract_status=ContractStatus.objects.get(name="Aktiv")
            )

            file = request.FILES.get('file', None)
            if file:
                OldContractFile.objects.create(contract=contract, file=file)

            contract_tarif_device = contract_tarif_device_serializer.save(
                contract=contract, client=user_obj, price=price_total_old_contract
            )

            UserDeviceCount.objects.create(
                user=contract_tarif_device,
                device=Device.objects.get(name='Server'),
                device_count=int(request.data.get("if_tarif_is_unit", 0)),
                units_count=contract_tarif_device_serializer.validated_data.get("rack_count"),
                electricity=contract_tarif_device_serializer.validated_data.get("total_electricity")
            )

            service_participants = ServiceParticipants.objects.filter(participant__service=contract.service)

            for obj in service_participants:
                Contracts_Participants.objects.create(
                    contract=contract,
                    role=obj.role,
                    agreement_status=AgreementStatus.objects.get(name="Kelishildi")
                )

            return Response({
                'user-data': self.serializer_class_yur_user(user).data,
                'contract-data': self.serializer_class_contract(contract).data,
                'tarif': self.serializer_class_contract_tarif_device(contract_tarif_device).data
            }, status=status.HTTP_201_CREATED)


class MonitoringContractViews(APIView):
    permission_classes = [IsAuthenticated]

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

        # if payed_percentage:  # this condition does not work
        #     query |= Q(payed_information__payed_percentage=payed_percentage)

        if contract_cash:
            query |= Q(contract_cash=contract_cash)

        if query_year:
            query |= Q(contract_date__year=query_year)

        # execute the query and retrieve the matching books
        contracts = Contract.objects.filter(query)
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
            # payed_percentage=request.GET.get("payed_percentage"),
        )
        serializer = MonitoringContractSerializer(contracts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonitoringContractDetailViews(generics.RetrieveAPIView):
    queryset = Contract.objects.all()
    serializer_class = MonitoringContractSerializer
    permission_classes = [IsAuthenticated]


class EndContractAPIView(APIView):
    def post(self, request):
        contract_id = request.POST.get('contract_id', None)
        expiration_date = request.POST.get('expiration_date', None)

        contract = Contract.objects.get(pk=contract_id)
        contract.expiration_date = expiration_date
        contract.save()
        return Response(status=200)