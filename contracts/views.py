import base64
import hashlib
import json
import math
import xmltodict

import requests
from django.conf import settings

import qrcode
from datetime import datetime

from django.db.models import Q
from django.shortcuts import redirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FizUser, UserData, Role, YurUser
from accounts.permissions import AdminPermission, SuperAdminPermission, DeputyDirectorPermission
from accounts.serializers import FizUserSerializer, YurUserSerializer, FizUserSerializerForContractDetail, \
    YurUserSerializerForContractDetail
from .models import Service, Tarif, Device, Offer, Document, SavedService, Element, UserContractTarifDevice, \
    UserDeviceCount, Contract, Status, ContractStatus, AgreementStatus, Pkcs, ExpertSummary, Contracts_Participants, \
    ConnetMethod
from .serializers import ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer, \
    OfferSerializer, DocumentSerializer, ElementSerializer, ContractSerializer, PkcsSerializer, \
    ContractSerializerForContractList, ContractSerializerForBackoffice, ExpertSummarySerializer, \
    ContractParticipantsSerializers, ExpertSummarySerializerForSave, ContractSerializerForDetail, \
    ConnectMethodSerializer
from .tasks import file_creator, file_downloader


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
            serializer = FizUserSerializerForContractDetail(user)
            data = serializer.data
            data['u_type'] = 'Fizik'
        else:
            user = YurUser.objects.get(userdata=request.user)
            serializer = YurUserSerializerForContractDetail(user)
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

        if 'rack_count' not in request.data.keys():
            request.data['rack_count'] = None
        if 'odf_count' not in request.data.keys():
            request.data['odf_count'] = None
        else:
            price += int(request.data['odf_count'])*23000
        user_selected_tarif_devices = UserContractTarifDevice.objects.create(
            client=request.user,
            service_id=request.data['service_id'],
            tarif=tarif,
            rack_count=request.data['rack_count'],
            connect_method=ConnetMethod.objects.get(pk=int(request.data['connect_method'])),
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
        img.save(file_path + file_name.split('.')[0] + '_' + str(number) + '.png')
        return file_path + file_name.split('.')[0] + '_' + str(number) + '.png'

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
            context['contract_number'] = prefix + '-' + str(number)
            context['year'] = datetime.now().year
            context['month'] = datetime.now().month
            context['day'] = datetime.now().day
            context['client'] = request.data['name']
            context['client_fullname'] = request.data['director_fullname']
            director = request.data['director_fullname'].split()
            context['director'] = f"{director[1][0]}.{director[2][0]}.{director[0]}"
            context['price'] = int(request.data['price']) * (12 - int(datetime.now().month))
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
            context['tarif'] = tarif
            context['count'] = request.data['count']
            context['price2'] = request.data['price']
            context['host'] = 'http://' + request.META['HTTP_HOST']
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
            context['price_text'] = self.number2word(int(context['price']))
            context['price_month'] = request.data['price']
            context['price_month_text'] = self.number2word(int(context['price_month']))
            context['price_month_avans'] = request.data['price']
            context['price_month_avans_text'] = context['price_month_text']
            context['per_adr'] = request.data['per_adr']
            context['pin'] = request.data['pin']
            context['tarif'] = tarif
            context['count'] = request.data['count']
            context['price2'] = request.data['price']
            context['host'] = 'http://' + request.META['HTTP_HOST']
        context['qr_unicon'] = ''
        context['qr_client'] = ''
        contract_file_for_preview = file_creator(context, 1)
        hashcode = hashlib.md5()
        hashcode.update(base64.b64encode(open('/usr/src/app/media/Contract/' + contract_file_for_preview, 'rb').read()))
        hash_code = hashcode.hexdigest()
        link = 'http://' + request.META['HTTP_HOST'] + '/contracts/contract?hash=' + hash_code
        context['qr_unicon'] = self.create_qr('Maxmudov Maxsum Mubashirovich', link, 1)
        context['qr_client'] = self.create_qr(context['client_fullname'], link, 2)
        contract_file = open('/usr/src/app/media/Contract/' + str(file_creator(context, 0)), 'rb').read()
        base64code = base64.b64encode(contract_file)

        if int(request.data['save']):
            status = Status.objects.filter(name='Yangi').first()
            contract_status = ContractStatus.objects.filter(name='Yangi').first()
            agreement_status = AgreementStatus.objects.filter(name='Yuborilgan').first()
            contract = Contract.objects.create(
                service_id=int(request.data['service_id']),
                contract_number=context['contract_number'],
                contract_date=datetime.now(),
                status=status,
                contract_status=contract_status,
                contract_cash=int(context['price_month']),
                payed_cash=0,
                tarif_id=int(request.data['tarif']),
                base64file=base64code,
                hashcode=hash_code
            )
            contract.save()
            contracts_participants = Contracts_Participants.objects.create(
                contract=contract,
                userdata=request.user
            )
            print(agreement_status)
            contracts_participants.save()
            service = contract.service.name
            if service.lower() == 'co-location':
                director = UserData.objects.get(role__name="direktor")
                deputy_director = UserData.objects.get(role__name="direktor o'rinbosari")
                d_head = UserData.objects.get(role__name="bo'lim boshlig'i")
                Contracts_Participants.objects.create(
                    contract=contract,
                    userdata=director,
                    agreement_status=agreement_status
                ).save()
                Contracts_Participants.objects.create(
                    contract=contract,
                    userdata=deputy_director,
                    agreement_status=agreement_status
                ).save()
                Contracts_Participants.objects.create(
                    contract=contract,
                    userdata=d_head,
                    agreement_status=agreement_status
                ).save()
            serializer = ContractSerializer(contract)
            return Response(serializer.data)
        return Response({
            'file_path': '/media/Contract/' + str(contract_file_for_preview),
            'base64file': base64code
        })


class SavePkcs(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PkcsSerializer

    def join2pkcs(self, pkcs7_1, pkcs7_2):
        print('422', pkcs7_1, pkcs7_2)
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
        print(437, dict_data)
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
        print(456, dict_data)
        response = dict_data['S:Envelope']['S:Body']['ns2:verifyPkcs7Response']['return']
        d = json.loads(response)
        return d

    def post(self, request):
        contract_id = int(request.data['contract_id'])
        pkcs7 = request.data['pkcs7']
        print(464, self.verifyPkcs(pkcs7))
        try:
            contract = Contract.objects.get(pk=contract_id)
            if request.user in contract.participants.all():
                if not Pkcs.objects.filter(contract=contract).exists():
                    pkcs = Pkcs.objects.create(contract=contract, pkcs7=pkcs7)
                    pkcs.save()
                else:
                    print('id', contract.id)
                    pkcs_exist_object = Pkcs.objects.get(contract=contract)
                    print(474, pkcs_exist_object)
                    client_pkcs = pkcs_exist_object.pkcs7
                    new_pkcs7 = self.join2pkcs(pkcs7, client_pkcs)
                    print(477, new_pkcs7)
                    pkcs_exist_object.pkcs7 = new_pkcs7
                    pkcs_exist_object.save()
        except Contract.DoesNotExist:
            return Response({'message': 'Bunday shartnoma mavjud emas'})
        return Response({'message': 'Success'})


class GetContractFile(APIView):
    permission_classes = ()

    def get(self, request):
        hashcode = request.GET.get('hash')
        contract = Contract.objects.get(hashcode=hashcode)
        file_pdf = file_downloader(bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'), contract.id)
        return redirect(u'/media/Contract/' + file_pdf)


class GetUserContracts(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        contracts = Contract.objects.filter(participants=request.user)
        serializer = ContractSerializerForContractList(contracts, many=True)
        return Response(serializer.data)


class GetContractFileWithID(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pk = request.GET.get('pk')
        contract = Contract.objects.get(pk=pk)
        file_pdf = file_downloader(bytes(contract.base64file[2:len(contract.base64file) - 1], 'utf-8'), contract.id)
        return redirect(u'/media/Contract/' + file_pdf)


class ContractDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        contract = Contract.objects.get(pk=pk)
        contract_serializer = ContractSerializerForDetail(contract)
        contract_participants = Contracts_Participants.objects.filter(contract=contract).get(userdata=request.user)
        if (request.user.role.name == "bo'lim boshlig'i" or request.user.role.name == "direktor o'rinbosari") \
                and contract_participants.agreement_status.name == "Yuborilgan":
            agreement_status = AgreementStatus.objects.get(name="Ko'rib chiqilmoqda")
            contract_participants.agreement_status = agreement_status
            contract_participants.save()
        client = Contracts_Participants.objects.filter(contract=contract)
        if client.get(agreement_status=None).userdata.type == 2:
            user = YurUser.objects.get(userdata=client.get(agreement_status=None).userdata)
            client_serializer = YurUserSerializer(user)
        else:
            user = FizUser.objects.get(userdata=client.get(agreement_status=None).userdata)
            client_serializer = FizUserSerializer(user)
        participants = client.exclude(agreement_status=None)
        participant_serializer = ContractParticipantsSerializers(participants, many=True)
        expert_summary = ExpertSummary.objects.filter(
            Q(contract=contract),
            Q(user=request.user)).exclude(
            Q(contract__contracts_participants__agreement_status__name='Yuborilgan'),
            Q(contract__contracts_participants__agreement_status__name="Ko'rib chiqilmoqda")
        ).exists()
        return Response(
            {
                'contract': contract_serializer.data,
                'client': client_serializer.data,
                'participants': participant_serializer.data,
                'is_confirmed': expert_summary
            }
        )


class GetGroupContract(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        group = request.user.group
        if request.user.role.name.lower() == "bo'lim boshlig'i" \
                or request.user.role.name.lower() == "direktor o'rinbosari" \
                or request.user.role.name.lower() == 'direktor':
            contracts = Contract.objects.filter(service__group=group).order_by('condition', '-contract_date')
        else:
            contracts = Contract.objects.filter(service__group=group).exclude(participants=None)  # , Q(condition=3))
        serializer = ContractSerializerForBackoffice(contracts, many=True)
        return Response(serializer.data)


class ConfirmContract(APIView):
    permission_classes = (DeputyDirectorPermission,)

    def post(self, request):
        contract = Contract.objects.get(pk=int(request.data['contract']))
        if int(request.data['summary']) == 1:
            agreement_status = AgreementStatus.objects.get(name='Kelishildi')
        else:
            agreement_status = AgreementStatus.objects.get(name='Rad etildi')
            contract.contract_status = ContractStatus.objects.get(name='Bekor qilingan')
        contracts_participants = Contracts_Participants.objects.get(Q(userdata=request.user), Q(contract=contract))
        contracts_participants.agreement_status = agreement_status
        contracts_participants.save()
        contract.condition += 1
        if contract.condition == 3:
            contract.contract_status = ContractStatus.objects.get(name="To'lov kutilmoqda")
        contract.save()
        request.data['user'] = request.user.id
        summary = ExpertSummarySerializerForSave(data=request.data)
        summary.is_valid(raise_exception=True)
        summary.save()
        return Response(status=200)


class DeleteUserContract(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        id = request.data['id']

