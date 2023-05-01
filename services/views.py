from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from contracts.models import UserDeviceCount, Contract, UserContractTarifDevice
from contracts.serializers import ContractSerializerForContractList, ContractSerializerForBackoffice
from .models import DeviceUnit, Rack, Unit, DevicePublisher, ProviderContract, DeviceStatus, InternetProvider
from .serializers import DeviceUnitSerializer, GetRackInformationSerializer, RackSerializer, UnitSerializer, \
    DevicePublisherSerializer, InternetProviderSerializer, RackForGetSerializer


class RackAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        number = int(request.data['number'])
        unit_count = int(request.data['unit_count'])
        rack = Rack.objects.create_rack(number=number, unit_count=unit_count)
        serializer = RackSerializer(rack)
        return Response(serializer.data)


class GetRackInfo(generics.ListAPIView):
    queryset = Rack.objects.all().order_by('number')
    serializer_class = GetRackInformationSerializer
    permission_classes = (IsAuthenticated,)


class RackDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        id = int(request.GET.get('rack_id'))
        rack = Rack.objects.get(pk=id)
        units = Unit.objects.filter(rack=rack).order_by('-number')
        devices = DeviceUnit.objects.filter(Q(rack=rack), Q(status__name="o'rnatilgan")).order_by('id')
        rack_data = RackSerializer(rack)
        units_data = UnitSerializer(units, many=True)
        devices_data = DeviceUnitSerializer(devices, many=True)
        return Response({
            'rack': rack_data.data,
            'units': units_data.data,
            'devices': devices_data.data
        })
    
    def post(self, request):
        id = int(request.data('rack_id'))
        rack = Rack.objects.get(pk=id)
        rack.is_sold = (not rack.is_sold)
        rack.save()
        serializer = RackSerializer(rack)
        return Response(serializer.data)


class UpdateRackAPIView(generics.RetrieveUpdateAPIView):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RackForGetSerializer(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        provider_contract_number = request.data.get('provider_contract_number', None)
        provider_contract_date = request.data.get('provider_contract_date', None)
        if ProviderContract.objects.filter(contract_number=provider_contract_number).exists():
            provider_contract = ProviderContract.objects.get(contract_number=provider_contract_number)
            request.data['provider_contract'] = provider_contract.id
        elif provider_contract_number and provider_contract_date:
            provider_contract = ProviderContract.objects.create(
                contract_number=provider_contract_number,
                contract_date=provider_contract_date 
            )
            provider_contract.save()
            request.data['provider_contract'] = provider_contract.id
        else:
            provider_contract = None
            request.data['provider_contract'] = provider_contract

        return super().put(request, *args, **kwargs)


class DevicePublisherAPIView(generics.ListAPIView):
    queryset = DevicePublisher.objects.all()
    serializer_class = DevicePublisherSerializer
    permission_classes = (IsAuthenticated,)


class ListInternetProviderAPIView(generics.ListAPIView):
    queryset = InternetProvider.objects.all()
    serializer_class = InternetProviderSerializer
    permission_classes = (IsAuthenticated,)
    

class AddDeviceAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        rack = int(request.data['rack'])
        start = int(request.data['start'])
        end = int(request.data['end'])
        rack_data = Rack.objects.get(pk=rack)
        if int(request.data['contract_id']):
            contract = int(request.data['contract_id'])
        elif Rack.objects.get(pk=rack).contract:
            contract = rack_data.contract.id
        else:
            return Response({
                'success': False,
                'message': 'Rack sotib olinmagan'
            })
        device_id = int(request.data['device_id'])
        device_publisher = int(request.data['device_publisher'])
        device_model = request.data['device_model']
        device_number = request.data['device_number']
        electricity = request.data['electricity']
        contract_number = request.data['contract_number']
        contract_date = request.data['contract_date']
        provider = request.data['provider']
        if start <= end:
            if contract_number and contract_date:
                if ProviderContract.objects.filter(contract_number=contract_number).exists():
                    provider_contract = ProviderContract.objects.get(contract_number=contract_number)
                else:
                    provider_contract = ProviderContract.objects.create(
                        contract_number=contract_number,
                        contract_date=contract_date
                    )
                    provider_contract.save()
            else:
                provider_contract = rack_data.provider_contract
            if not provider:
                provider = rack_data.provider.id
            device = DeviceUnit.objects.create(
                rack_id=rack,
                device_id=device_id,
                device_publisher_id=device_publisher,
                device_model=device_model,
                device_number=device_number,
                electricity=electricity,
                provider_contract=provider_contract,
                status=DeviceStatus.objects.get(name="o'rnatilgan"),
                provider=InternetProvider.objects.get(pk=int(provider)),
                start=start,
                end=end
            )
            device.save()
            for i in range(start, end+1):
                unit = Unit.objects.get(Q(number=i), Q(rack_id=rack))
                unit.device = device
                unit.is_busy = True
                unit.contract = Contract.objects.get(pk=contract)
                unit.save()
            data = {
                'success': True,
                'message': "Muvaffaqiyatli qo'shildi"
            }
            return Response(data, status=200)
        else:
            data = {
                'success': False,
                'message': "Start keyword end keyworddan kichkina yoki teng bo'lishi kerak"
            }
            return Response(data, status=405)


class DeviceUnitDetail(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        device_id = int(request.GET.get('device_id'))
        device = DeviceUnit.objects.get(pk=device_id)
        serializer = DeviceUnitSerializer(device)
        unit = Unit.objects.get(Q(number=device.start), Q(rack=device.rack))
        contract = Contract.objects.get(contract_number=unit.contract.contract_number)
        contract_serializer = ContractSerializerForBackoffice(contract)
        odf_count = UserContractTarifDevice.objects.get(contract=unit.contract).odf_count
        if device.provider_contract:
            device_contract_number = device.provider_contract.contract_number
            device_contract_date= device.provider_contract.contract_date
        else:
            device_contract_number = None
            device_contract_date = None
        data = {
            'device': serializer.data,
            'contract': contract_serializer.data,
            'provider_contract_number': device_contract_number,
            'provider_contract_date': device_contract_date,
            'odf_count': odf_count
        }
        return Response(data)


class DeleteDeviceAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        device_id = int(request.data['device_id'])
        device = DeviceUnit.objects.get(pk=device_id)
        start = device.start
        end = device.end
        for i in range(start, end + 1):
            unit = Unit.objects.get(Q(number=i), Q(rack_id=device.rack.id))
            unit.device = None
            unit.is_busy = False
            unit.contract = None
            unit.save()
        device.status = DeviceStatus.objects.get(name="qaytarilgan")
        device.save()
        return Response(status=204)
