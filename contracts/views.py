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


class ListAllServicesAPIView(generics.ListAPIView):
    queryset = Service.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ServiceSerializer


class ListGroupServicesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        group_id = request.GET.get('group_id')
        print(group_id)
        services = Service.objects.filter(group_id=group_id)
        serializers = ServiceSerializer(services, many=True)
        return Response(serializers.data)


class ServiceDetailAPIView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = (IsAuthenticated,)


class UserDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.type == 1:
            user = FizUser.objects.get(userdata=request.user)
            serializer = FizUserSerializer(user)
            serializer.data['type'] = 'Fizik'
        else:
            user = YurUser.objects.get(userdata=request.user)
            serializer = YurUserSerializer(user)
            serializer.data['type'] = 'Yuridik'
        return JsonResponse(serializer.data)


class TarifListAPIView(generics.ListAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class DeviceListAPIView(generics.ListAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)


class UserContractTarifDeviceCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        request.data['client'] = request.user
        data = UserContractTarifDeviceSerializer(request.data)
        data.is_valid(raise_exception=True)
        data.save()
        return JsonResponse(data.data)


class OfferCreateAPIView(generics.CreateAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = (AdminPermission,)


class OfferDetailAPIView(APIView):
    serializer_class = OfferSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        service_id = request.data['service_id']
        offer = Offer.objects.get(service_id=service_id)
        serializer = OfferSerializer(offer)
        return Response(serializer.data)


class GetGroupAdminDataAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        service = Service.objects.get(pk=request.data['service_id'])
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
            if saved_services:
                services = saved_services.services.all()
            else:
                services = []
            serializer = ServiceSerializer(services, many=True)
            return Response(serializer.data)
        except:
            return Response([])

    @swagger_auto_schema(operation_summary="Service ni saqlangan servicega qo'shish. Bu yerda service_id ni jo'natishiz kere bo'ladi")
    def post(self, request):
        service_id = request.data['service_id']
        user = request.user
        service = Service.objects.get(pk=service_id)
        saved_service = SavedService.objects.create(user=user)
        saved_service.services.add(service)
        saved_service.save()
        return Response(status=201)


class TarifAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        group_id = request.data['group_id']

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
        units_count = 0
        electricity = 0
        lishniy_unit = 0
        lishniy_electricity = 0
        for device in devices:
            units_count += device['device_count'] * device['units_count']
            electricity += device['electricity']
        tarif = Tarif.objects.get(pk=request.data['tarif'])
        if tarif.name == 'Rack-1':
            if units_count > request.data['rack_count']*42:
                lishniy_unit = units_count - request.data['rack_count']*42
            if electricity > 7500:
                lishniy_electricity = electricity-7500
            price = tarif.price*request.data['rack_count'] + lishniy_unit*23000 + lishniy_electricity*0.23
        else:
            if units_count > 0:
                lishniy_unit = units_count - 1
            if electricity > 450:
                lishniy_electricity = electricity-450
            price = tarif.price + lishniy_unit*23000 + lishniy_electricity*230

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
