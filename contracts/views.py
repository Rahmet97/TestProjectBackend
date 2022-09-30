from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.models import FizUser
from accounts.serializers import FizUserSerializer
from .models import Service, Tarif, Device
from .serializers import ServiceSerializer, TarifSerializer, DeviceSerializer, UserContractTarifDeviceSerializer


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
        print(request.user.role)
        user = FizUser.objects.get(user=request.user)
        serializer = FizUserSerializer(user)
        return JsonResponse(serializer.data)


class TarifListAPIView(generics.ListAPIView):
    queryset = Tarif
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class DeviceListAPIView(generics.ListAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = (IsAuthenticated,)


class UserContractTarifDeviceCreateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        request.data['client'] = request.user
        data = UserContractTarifDeviceSerializer(request.data)
        data.is_valid(raise_exception=True)
        data.save()
        return JsonResponse(data.data)
