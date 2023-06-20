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
    def calculate(configuration, total_cash=VpsDevicePriceEnum.IPV4_ADDRESS):
        calculate_data = dict()

        count_vm = configuration.get('count_vm')
        operation_system_versions = configuration.get("operation_system_versions", [])
        if count_vm != len(operation_system_versions):
            responseErrorMessage(
                message="count vm is equal to operation system versions count",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        storage_type = configuration.get("storage_type")
        storage_disk = configuration.get("storage_disk")

        calculate_data[f"cpu * {count_vm}"] = configuration.get("cpu") * count_vm * VpsDevicePriceEnum.CPU
        total_cash += configuration.get("cpu") * count_vm * VpsDevicePriceEnum.CPU

        calculate_data[f"ram * {count_vm}"] = configuration.get("ram") * count_vm * VpsDevicePriceEnum.RАМ
        total_cash += configuration.get("ram") * count_vm * VpsDevicePriceEnum.RАМ

        if storage_type == "ssd":
            calculate_data[f"ssd * {count_vm}"] = storage_disk * count_vm * VpsDevicePriceEnum.SSD
            total_cash += calculate_data[f"ssd * {count_vm}"]
        elif storage_type == "hhd":
            calculate_data[f"hhd * {count_vm}"] = storage_disk * count_vm * VpsDevicePriceEnum.HHD
            total_cash += calculate_data[f"hhd * {count_vm}"]

        internet, tasix = configuration.get("internet", 0), configuration.get("tasix", 0)
        if configuration.get("internet") and internet >= 10:
            total_cash += (internet-10) * VpsDevicePriceEnum.INTERNET * count_vm

        if configuration.get("tasix") and tasix >= 100:
            total_cash += (tasix-100) * VpsDevicePriceEnum.TASIX * count_vm

        if configuration.get("imut"):
            total_cash += configuration.get("imut", 0) * VpsDevicePriceEnum.IMUT * count_vm

        total_cash += sum(os_version.price for os_version in operation_system_versions)

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

        return response.Response({"data": context}, status=status.HTTP_200_OK)
