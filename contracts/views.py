from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FizUser, UserData, Role
from accounts.permissions import AdminPermission
from accounts.serializers import FizUserSerializer
from .models import Service, Tarif, Device, Offer
from .serializers import ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer, \
    OfferSerializer


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


class FizUserDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = FizUser.objects.get(userdata=request.user)
        serializer = FizUserSerializer(user)
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


class OfferDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = (AdminPermission,)


class GetGroupAdminDataAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        service = Service.objects.get(pk=request.data['service_id'])
        role = UserData.objects.get(group__service_id=service)
        # role_name = Role.objects.get(pk=role).name
        print(role)
        return Response(status=200)
