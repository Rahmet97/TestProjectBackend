import math

from django.conf import settings
from docxtpl import InlineImage, DocxTemplate
from docx.shared import Mm

import qrcode
from PIL import Image
from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FizUser, UserData, Role, YurUser
from accounts.permissions import AdminPermission, SuperAdminPermission
from accounts.serializers import FizUserSerializer, YurUserSerializer
from .models import Service, Tarif, Device, Offer, Document, SavedService, Element, UserContractTarifDevice, \
    UserDeviceCount
from .serializers import ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer, \
    OfferSerializer, DocumentSerializer, ElementSerializer
from .tasks import file_creator


class ListAllServicesAPIView(generics.ListAPIView):
    queryset = Service.objects.all()
    permission_classes = ()
    serializer_class = ServiceSerializer


class ListGroupServicesAPIView(APIView):
    permission_classes = ()

    def get(self, request):
        group_id = request.GET.get('group_id')
        print(group_id)
        services = Service.objects.filter(group_id=group_id)
        serializers = ServiceSerializer(services, many=True, context={'request': request})
        return Response(serializers.data)


class ServiceDetailAPIView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = ()


class UserDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.type == 1:
            user = FizUser.objects.get(userdata=request.user)
            serializer = FizUserSerializer(user)
            data = serializer.data
            data['u_type'] = 'Fizik'
        else:
            user = YurUser.objects.get(userdata=request.user)
            serializer = YurUserSerializer(user)
            data = serializer.data
            data['u_type'] = 'Yuridik'
        return Response(data)


class TarifListAPIView(generics.ListAPIView):
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
            return Response({'message': 'Bunday xizmat mavjud emas'})
        return Response(serializer.data)


class GetGroupAdminDataAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        service = Service.objects.get(pk=request.GET.get('service_id'))
        role = UserData.objects.get(group__service_id=service)
        # role_name = Role.objects.get(pk=role).name
        print(role)
        return Response(status=200)


class ServiceCreateAPIView(generics.CreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = (SuperAdminPermission,)


class DocumentCreateAPIView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (AdminPermission,)


class SavedServiceAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            saved_services = SavedService.objects.get(user=request.user)
        except SavedService.DoesNotExist:
            saved_services = None
        print(saved_services)
        if saved_services:
            services = saved_services.services.all()
        else:
            services = []
        serializer = ServiceSerializer(services, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Service ni saqlangan servicega qo'shish. Bu yerda service_id ni "
                                           "jo'natishiz kere bo'ladi")
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
            return Response({'message': 'Bu service oldindan mavjud'})
        return Response(status=200)


class DeleteSavedService(APIView):
    def delete(self, request, pk):
        try:
            saved_service = SavedService.objects.get(user=request.user)
            service = Service.objects.get(pk=pk)
            saved_service.services.remove(service)
        except Exception as e:
            return Response({'message': f"{e}"})
        return Response(status=204)


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
        })


class SelectedTarifDevicesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        devices = request.data['devices']
        electricity = 0
        lishniy_electricity = 0
        price = 0
        tarif = Tarif.objects.get(pk=request.data['tarif'])
        if tarif.name == 'Rack-1':
            for device in devices:
                electricity += device['electricity']
            if electricity > int(request.data['rack_count']) * 7500:
                lishniy_electricity = electricity-int(request.data['rack_count']) * 7500
            price = tarif.price*int(request.data['rack_count']) + math.ceil(lishniy_electricity/100) * 23000
        else:
            for device in devices:
                unit_count = int(device['device_count']) * int(device['units_count'])
                if int(device['electricity']) > 450:
                    lishniy_electricity = int(device['electricity'])-450
                price += tarif.price * unit_count + math.ceil(lishniy_electricity/100) * 23000 * int(device['device_count'])

        if 'rack_count' not in request.data.keys():
            request.data['rack_count'] = None
        user_selected_tarif_devices = UserContractTarifDevice.objects.create(
            client=request.user,
            service_id=request.data['service_id'],
            tarif=tarif,
            rack_count=request.data['rack_count'],
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


class CreateContractFileAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def hundreds(self, m):
        digits = {
            1: "bir", 2: "ikki", 3: "uch", 4: "to'rt", 5: "besh", 6: "olti", 7: "yetti", 8: "sakkiz", 9: "to'qqiz",
            10: "o'n", 20: "yigirma", 30: "o'ttiz", 40: "qirq", 50: "ellik", 60: "oltmish", 70: "yetmish", 80: "sakson",
            90: "to'qson"
        }

        d1 = m // 100
        d2 = (m // 10) % 10
        d3 = m % 10
        s1, s2, s3 = '', '', ''
        if d1 != 0:
            s1 = f'{digits[d1]} yuz '
        if d2 != 0:
            s2 = digits[d2 * 10] + ' '
        if d3 != 0:
            s3 = digits[d3] + ' '

        return s1 + s2 + s3

    def number2word(self, n):
        d1 = {0: "", 1: "ming ", 2: "million ", 3: "milliard ", 4: "trillion "}

        fraction = []
        while n > 0:
            r = n % 1000
            fraction.append(r)
            n //= 1000

        s = ''
        for i in range(len(fraction)):
            if fraction[i] != 0:
                yuz = self.hundreds(fraction[i]) + d1[i]
                s = yuz + s

        return s.rstrip()

    def create_qr(self, fullname, link, number):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        file_name = link.split('/')[-1]
        file_path = f"{settings.MEDIA_ROOT}/qr/"
        qr.add_data(f"{fullname}. {link}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        img.save(file_path + file_name.split('.')[0] + str(number) + '.png')
        return file_path + file_name.split('.')[0] + str(number) + '.png'

    def post(self, request):
        context = dict()
        if request.user.type == 2:
            context['u_type'] = 'yuridik'
            context['contract_number'] = request.data['number']
            context['year'] = datetime.now().year
            context['month'] = datetime.now().month
            context['day'] = datetime.now().day
            context['client'] = request.data['name']
            director = request.data['director_fullname'].split()
            context['director'] = f"{director[1][0]}.{director[2][0]}. {director[0]}"
            context['price'] = request.data['price'] * (12 - int(datetime.now().month))
            context['price_text'] = self.number2word(int(context['price']))
            context['price_month'] = request.data['price']
            context['price_month_text'] = self.number2word(int(context['price_month']))
            context['price_month_avans'] = request.data['price']
            context['price_month_avans_text'] = context['price_month_text']
            context['per_adr'] = request.data['per_adr']
            context['tin'] = request.data['tin']
            context['mfo'] = request.data['mfo']
            context['oked'] = request.data['oked']
            context['hr'] = request.data['hr']
            context['bank'] = request.data['bank']
            context['tarif'] = request.data['tarif']
            context['count'] = request.data['count']
            context['price2'] = request.data['price']
            context['host'] = 'http://' + request.META['HTTP_HOST']
            if int(request.data['save']):
                link = 'http://' + request.META['HTTP_HOST'] + '/media/Contract/' + request.data['number'] + '.docx'
                context['qr_unicon'] = self.create_qr('Maxmudov Maxsum Mubashirovich', link, 1)
                context['qr_client'] = self.create_qr(request.data['director_fullname'], link, 2)
            else:
                context['qr_unicon'] = ''
                context['qr_client'] = ''
        else:
            context['u_type'] = 'fizik'
            context['contract_number'] = request.data['number']
            context['year'] = datetime.now().year
            context['month'] = datetime.now().month
            context['day'] = datetime.now().day
            context['pport_issue_place'] = request.data['pport_issue_place']
            context['pport_issue_date'] = request.data['pport_issue_date']
            context['pport_no'] = request.data['pport_no']
            client_short = request.data['full_name'].split()
            context['client'] = f"{client_short[1][0]}.{client_short[2][0]}. {client_short[0]}"
            context['client_fullname'] = request.data['full_name']
            context['price'] = int(request.data['price'])*(12-int(datetime.now().month))
            context['price_text'] = self.number2word(int(context['price']))
            context['price_month'] = request.data['price']
            context['price_month_text'] = self.number2word(int(context['price_month']))
            context['price_month_avans'] = request.data['price']
            context['price_month_avans_text'] = context['price_month_text']
            context['per_adr'] = request.data['per_adr']
            context['pin'] = request.data['pin']
            context['tarif'] = request.data['tarif']
            context['count'] = request.data['count']
            context['price2'] = request.data['price']
            context['host'] = 'http://' + request.META['HTTP_HOST']
            if int(request.data['save']):
                link = 'http://' + request.META['HTTP_HOST'] + '/media/Contract/' + request.data['number'] + '.docx'
                context['qr_unicon'] = self.create_qr('Maxmudov Maxsum Mubashirovich', link, 1)
                context['qr_client'] = self.create_qr(context['client_fullname'], link, 2)
            else:
                context['qr_unicon'] = ''
                context['qr_client'] = ''
        contract_file = file_creator(context)
        return Response({'file_path': '/media/Contract/' + str(contract_file)})
