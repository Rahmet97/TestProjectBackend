import math

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
        elements = request.data['elements']
        device_count = elements['device_count']
        odf_count = elements['odf_count']
        electricity = elements['electricity']

        amount = tariff.price * count
        if device_count is not None and tariff.name == 'Unit-1':
            electr = Element.objects.get(Q(keyword='electricity'), Q(cost=0), Q(tariff=tariff)).cost * device_count
        else:
            electr = Element.objects.get(Q(keyword='electricity'), Q(cost=0), Q(tariff=tariff)).cost * count
        price_e = Element.objects.get(Q(keyword='electricity'), Q(tariff=tariff))
        if electricity > electr:
            price_electricity = math.ceil((electricity - electr) / price_e.quantity) * price_e.cost
        else:
            price_electricity = 0
        price_o = Element.objects.get(Q(keyword='odf'), Q(tariff=tariff))
        if odf_count is not None:
            price_odf = (odf_count - 1) * price_o.cost
        else:
            price_odf = 0

        amount += price_odf + price_electricity
        data = {
            'elements': [
                {
                    'element': tariff.name,
                    'price': tariff.price,
                    'count': count,
                    'amount': tariff.price * count
                },
                {
                    'element': 'electricity',
                    'price': price_e,
                    'count': electricity,
                    'amount': price_electricity
                },
                {
                    'element': 'odf',
                    'price': price_o,
                    'count': odf_count,
                    'amount': price_odf
                },
            ],
            'amount': amount
        }
        return Response(data)
