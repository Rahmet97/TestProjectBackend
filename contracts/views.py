from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FizUser, UserData, Role, YurUser
from accounts.permissions import AdminPermission, SuperAdminPermission
from accounts.serializers import FizUserSerializer, YurUserSerializer
from .models import Service, Tarif, Device, Offer, Document, SavedService
from .serializers import ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer, \
    OfferSerializer, DocumentSerializer


class ListAllServicesAPIView(generics.ListAPIView):
    queryset = Service.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ServiceSerializer


class ListGroupServicesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        group_id = request.data['group_id']
        services = Service.objects.filter(group_id=group_id)
        serializers = ServiceSerializer(services, many=True)
        return JsonResponse(serializers.data)


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
        saved_services = SavedService.objects.get(user=request.user)
        services = saved_services.services.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(operation_summary="Service ni saqlangan servicega qo'shish. Bu yerda service_id ni jo'natishiz kere bo'ladi")
    def post(self, request):
        service_id = request.data['service_id']
        user = request.user
        service = Service.objects.get(pk=service_id)
        saved_service = SavedService.objects.create(user=user)
        saved_service.services.add(service)
        saved_service.save()
        return Response(status=201)

