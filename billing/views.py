import math
from _decimal import Decimal

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, views, response, status, permissions

from main.utils import responseErrorMessage

from accounts.models import Group

from billing.models import BillingLog, InvoiceElements
from billing.serializers import RequestSerializer, InvoiceElementsSerializer

from contracts.models import Tarif, Element, TarifLog, Service
from contracts.serializers import TarifSerializer, ElementSerializer, GetElementSerializer


class ElementAPIView(generics.CreateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GetElementAPIView(generics.ListAPIView):
    queryset = Element.objects.all()
    serializer_class = GetElementSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ElementUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (permissions.IsAuthenticated,)


class InvoiceElementsAPIView(generics.ListCreateAPIView):
    queryset = InvoiceElements.objects.all()
    serializer_class = InvoiceElementsSerializer
    permission_classes = (permissions.IsAuthenticated,)


class InvoiceElementsUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = InvoiceElements.objects.all()
    serializer_class = InvoiceElementsSerializer
    # permission_classes = (permissions.IsAuthenticated,)


class ColocationTariffSummAPIView(views.APIView):
    permission_classes = ()

    def post(self, request):
        try:
            group = Group.objects.get(pk=int(request.data.get('group', 0)))
        except Group.DoesNotExist:
            group = None
        try:
            service = Service.objects.get(pk=int(request.data.get('service', 0)))
        except Service.DoesNotExist:
            service = None
        try:
            tariff = Tarif.objects.get(pk=int(request.data.get('tariff', 0)))
        except Tarif.DoesNotExist:
            tariff = None
        count = int(request.data['count'])
        elements = request.data['elements']
        device_count = elements['device_count']
        odf_count = elements['odf_count']
        electricity = elements['electricity']

        amount = tariff.price * count
        if device_count is not None and tariff.name == 'Unit-1':
            electr = Element.objects.get(Q(keyword='electricity'), Q(cost=0), Q(tariff=tariff)).quantity * device_count
        else:
            electr = Element.objects.get(Q(keyword='electricity'), Q(cost=0), Q(tariff=tariff)).quantity * count
        print(59, electr)
        price_e = Element.objects.get(Q(keyword='electricity'), Q(tariff=tariff), Q(cost__gt=0))
        print(61, price_e.cost)
        if electricity > electr:
            price_electricity = math.ceil((electricity - electr) / price_e.quantity) * price_e.cost
        else:
            price_electricity = 0
        print(66, price_electricity)
        price_o = Element.objects.get(Q(keyword='odf'), Q(tariff=tariff))
        if odf_count is not None:
            price_odf = (odf_count - 1) * price_o.cost
        else:
            price_odf = 0
        print(72, price_odf)

        amount += price_odf + price_electricity
        print(75, amount)
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
                    'price': price_e.cost,
                    'count': electricity,
                    'amount': price_electricity
                },
                {
                    'element': 'odf',
                    'price': price_o.cost,
                    'count': odf_count,
                    'amount': price_odf
                },
            ],
            'amount': amount
        }
        return response.Response(data)


class ExpertiseTariffSummAPIView(views.APIView):
    permission_classes = []

    @staticmethod
    def validate_data(projects):
        for project in projects:
            if project.get("is_discount") and project.get("discount_price") is None:
                return False
            if not project.get("is_discount") and project.get("price") is None:
                return False
        return True

    @staticmethod
    def get_cash(project):

        if project["is_discount"] and project.get("discount_price") is not None:
            return project["discount_price"]
        return project["price"]

    def calculate(self, projects):

        total_cash = Decimal(0)
        for project in projects:
            total_cash += Decimal(self.get_cash(project))
        return total_cash

    def post(self, request):
        projects = request.data.get("projects")

        if not projects:
            return responseErrorMessage(message="Fill in the input", status_code=status.HTTP_400_BAD_REQUEST)

        if not self.validate_data(projects=projects):
            return responseErrorMessage(message="Fill in the input", status_code=status.HTTP_400_BAD_REQUEST)

        res = self.calculate(projects=projects)
        return response.Response({"total_cash": res}, status=status.HTTP_200_OK)

