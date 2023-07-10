import math
from _decimal import Decimal

from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, views, response, status, permissions

from contracts.utils import NumbersToWord
from main.utils import responseErrorMessage

from accounts.models import Group

from billing.models import BillingLog, InvoiceElements
from billing.serializers import RequestSerializer, InvoiceElementsSerializer, VpsTariffSummSerializer

from contracts.models import Tarif, Element, TarifLog, Service
from contracts.serializers import TarifSerializer, ElementSerializer, GetElementSerializer
from vpsService.enum_utils import VpsDevicePriceEnum
from vpsService.models import OperationSystemVersion

num2word = NumbersToWord()


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


def calculate_vps(configuration: dict, total_cash=0) -> dict:
    """
        billing calculate vps service
    """
    calculate_data = dict()

    count_vm = configuration.get('count_vm')
    operation_system_versions = configuration.get("operation_system_versions", [])

    if count_vm != len(operation_system_versions):
        responseErrorMessage(
            message="count vm is equal to operation system versions count",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    ipv_address_count = sum(1 for os_version in operation_system_versions if os_version.get("ipv_address") is True)
    calculate_data["ipv_address_count"] = ipv_address_count
    calculate_data["ipv_address_price"] = ipv_address_count * VpsDevicePriceEnum.IPV4_ADDRESS
    calculate_data["ipv_address_price_text"] = num2word.change_num_to_word(int(calculate_data["ipv_address_price"]))
    total_cash += calculate_data["ipv_address_price"]

    # if operation_system_version has price
    # total_cash += sum(
    #     OperationSystemVersion.objects.get(id=os_version.get("operation_system_version")).price
    #     if os_version.get("operation_system_version") else 0
    #     for os_version in operation_system_versions
    # )
    # total_cash += sum(
    #     os_version.get("operation_system_version").price
    #     if os_version.get("operation_system_version") else 0
    #     for os_version in operation_system_versions
    # )

    storage_type, storage_disk = configuration.get("storage_type"), configuration.get("storage_disk")

    calculate_data["cpu"] = configuration.get("cpu") * count_vm * VpsDevicePriceEnum.CPU
    calculate_data["cpu_size"] = configuration.get("cpu") * count_vm
    calculate_data["cpu_price_text"] = num2word.change_num_to_word(int(calculate_data["cpu"]))
    total_cash += calculate_data["cpu"]

    calculate_data["ram"] = configuration.get("ram") * count_vm * VpsDevicePriceEnum.RАМ
    calculate_data["ram_size"] = configuration.get("ram") * count_vm
    calculate_data["ram_price_text"] = num2word.change_num_to_word(int(calculate_data["ram"]))
    total_cash += calculate_data["ram"]

    if storage_type == "ssd":
        calculate_data[f"storage_disk_price"] = storage_disk * count_vm * VpsDevicePriceEnum.SSD
        calculate_data[f"storage_disk_size"] = storage_disk * count_vm
        calculate_data[f"storage_disk_price_text"] = num2word.change_num_to_word(
            int(calculate_data["storage_disk_price"])
        )
        calculate_data["storage_type"] = storage_type
        total_cash += calculate_data["storage_disk_price"]
    elif storage_type == "hdd":
        calculate_data[f"storage_disk_price"] = storage_disk * count_vm * VpsDevicePriceEnum.HDD
        calculate_data[f"storage_disk_size"] = storage_disk * count_vm
        calculate_data[f"storage_disk_price_text"] = num2word.change_num_to_word(
            int(calculate_data["storage_disk_price"])
        )
        calculate_data["storage_type"] = storage_type
        total_cash += calculate_data["storage_disk_price"]

    # #######################
    # for create vps contract
    calculate_data[storage_type] = {
        f"{storage_type}": calculate_data[f"storage_disk_price"],
        f"{storage_type}_size": storage_disk * count_vm
    }
    # #######################

    internet = configuration.get("internet") or 0
    calculate_data["internet_size"] = max((internet - 10) * count_vm, 0)
    calculate_data["internet"] = calculate_data["internet_size"] * VpsDevicePriceEnum.INTERNET
    calculate_data["internet_price_text"] = num2word.change_num_to_word(int(calculate_data["internet"]))
    total_cash += calculate_data["internet"]

    tasix = configuration.get("tasix") or 0
    calculate_data["tasix_size"] = max((tasix - 100) * count_vm, 0)
    calculate_data["tasix"] = calculate_data["tasix_size"] * VpsDevicePriceEnum.TASIX
    calculate_data["tasix_price_text"] = num2word.change_num_to_word(int(calculate_data["tasix"]))
    total_cash += calculate_data["tasix"]

    imut = configuration.get("imut") or 0
    calculate_data["imut_size"] = imut * count_vm
    calculate_data["imut"] = calculate_data["imut_size"] * VpsDevicePriceEnum.IMUT
    calculate_data["imut_price_text"] = num2word.change_num_to_word(int(calculate_data["imut"]))
    total_cash += calculate_data["tasix"]

    calculate_data["total_cash"] = total_cash
    calculate_data["total_cash_price_text"] = num2word.change_num_to_word(int(total_cash))
    return calculate_data


class VpsTariffSummAPIView(views.APIView):
    serializer_class = VpsTariffSummSerializer
    permission_classes = []

    def post(self, request):
        serializer = self.serializer_class(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        context, configurations_total_price = [], 0
        for configuration_id, configuration in enumerate(serializer.validated_data):
            item = calculate_vps(configuration=configuration)
            configurations_total_price += item.get("total_cash", 0)
            context.append(item)

        return response.Response({
            "configurations_prices": context,
            "configurations_total_price": configurations_total_price,
            "configurations_total_price_text": num2word.change_num_to_word(int(configurations_total_price))
        }, status=status.HTTP_200_OK)
