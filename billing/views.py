import math
from _decimal import Decimal

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, views, response, status, permissions

from main.utils import responseErrorMessage

from accounts.models import Group

from billing.models import BillingLog, InvoiceElements
from billing.serializers import RequestSerializer, InvoiceElementsSerializer, VpsTariffSummSerializer

from contracts.models import Tarif, Element, TarifLog, Service
from contracts.serializers import TarifSerializer, ElementSerializer, GetElementSerializer
from vpsService.enum_utils import VpsDevicePriceEnum


class ElementAPIView(generics.CreateAPIView):
    queryset = Element.objects.all()
    serializer_class = ElementSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GetElementAPIView(generics.ListAPIView):
    queryset = Element.objects.all()
    serializer_class = GetElementSerializer
    permission_classes = (permissions.IsAuthenticated,)


class ElementUpdateAPIView(generics.RetrieveUpdateDestroyAPIView):
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


class VpsTariffSummAPIView(views.APIView):
    serializer_class = VpsTariffSummSerializer
    permission_classes = []

    @staticmethod
    def calculate(configuration, total_cash=0):
        calculate_data = dict()

        calculate_data[f"cpu * {configuration.get('count_vm')}"] = \
            configuration.get("cpu") * configuration.get('count_vm') * VpsDevicePriceEnum.CPU
        total_cash += configuration.get("cpu") * configuration.get('count_vm') * VpsDevicePriceEnum.CPU

        calculate_data[f"ram * {configuration.get('count_vm')}"] = \
            configuration.get("ram") * configuration.get('count_vm') * VpsDevicePriceEnum.RАМ
        total_cash += configuration.get("ram") * configuration.get('count_vm') * VpsDevicePriceEnum.RАМ

        if configuration.get("storage_type") == "ssd":
            calculate_data[f"ssd * {configuration.get('count_vm')}"] = \
                configuration.get("ram") * configuration.get('count_vm') * VpsDevicePriceEnum.SSD
            total_cash += configuration.get("storage_disk") * configuration.get('count_vm') * VpsDevicePriceEnum.SSD
        elif configuration.get("storage_type") == "hhd":
            calculate_data[f"hhd * {configuration.get('count_vm')}"] = \
                configuration.get("ram") * configuration.get('count_vm') * VpsDevicePriceEnum.HHD
            total_cash += configuration.get("storage_disk") * configuration.get('count_vm') * VpsDevicePriceEnum.HHD

        if configuration.get("internet"):
            total_cash += configuration.get("internet") * VpsDevicePriceEnum.INTERNET * configuration.get('count_vm')
        if configuration.get("tasix"):
            total_cash += configuration.get("tasix") * VpsDevicePriceEnum.TASIX * configuration.get('count_vm')
        if configuration.get("imut"):
            total_cash += configuration.get("imut") * VpsDevicePriceEnum.IMUT * configuration.get('count_vm')

        for os_version in configuration.get("operation_system_versions"):
            total_cash += os_version.price

        calculate_data["total_cash"] = total_cash
        return calculate_data

    def post(self, request):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        context = dict()
        for configuration_id, configuration in enumerate(serializer.validated_data):
            context[f"configuration {configuration_id + 1}*{configuration.get('count_vm')}"] = self.calculate(
                configuration=configuration
            )

        print(context)
        return response.Response({"data": context}, status=status.HTTP_200_OK)
