from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from accounts.models import Group
from billing.models import BillingLog
from billing.serializers import RequestSerializer
from contracts.models import Tarif, Element, TarifLog, Service
from contracts.serializers import TarifSerializer, ElementSerializer


class TariffCreateAPIView(CreateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class TariffUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Tarif.objects.all()
    serializer_class = TarifSerializer
    permission_classes = (IsAuthenticated,)


class ElementAPIView(ListCreateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)


class ElementUpdateAPIView(RetrieveUpdateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (IsAuthenticated,)


class ColocationTariffSummAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        group = Group.objects.get(pk=int(request.data['group']))
        service = Service.objects.get(pk=int(request.data['service']))
        tariff = Tarif.objects.get(pk=int(request.data['tariff']))
        count = int(request.data['count'])
        device_count = request.data.get('device_count', None)
        odf_count = request.data.get('odf_count', None)
        electricity = request.data['electricity']



        return Response({})
