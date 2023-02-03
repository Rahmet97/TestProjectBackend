from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from contracts.models import UserDeviceCount
from .models import DeviceUnit, Rack, Unit, DevicePublisher, ProviderContract, DeviceStatus, InternetProvider
from .serializers import DeviceUnitSerializer, GetRackInformationSerializer, RackSerializer, UnitSerializer, \
    DevicePublisherSerializer, InternetProviderSerializer


class RackAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        number = int(request.data['number'])
        unit_count = int(request.data['unit_count'])
        rack = Rack.objects.create_rack(number=number, unit_count=unit_count)
        serializer = RackSerializer(rack)
        return Response(serializer.data)


class GetRackInfo(generics.ListAPIView):
    queryset = Rack.objects.all()
    serializer_class = GetRackInformationSerializer
    permission_classes = (IsAuthenticated,)


class RackDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        id = int(request.GET.get('rack_id'))
        rack = Rack.objects.get(pk=id)
        units = Unit.objects.filter(rack=rack).order_by('-number')
        devices = DeviceUnit.objects.filter(rack=rack).order_by('id')
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
        if int(request.data['contract_id']):
            contract = int(request.data['contract_id'])
        elif Rack.objects.get(pk=rack).contract:
            contract = Rack.objects.get(pk=rack).contract.id
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
        provider = int(request.data['provider'])
        if start <= end:
            if Provider.objects.filter(contract_number=contract_number).exists():
                provider_contract = ProviderContract.objects.get(contract_number=contract_number)
            else:
                provider_contract = ProviderContract.objects.create(
                    contract_number=contract_number,
                    contract_date=contract_date
                )
                provider_contract.save()
            device = DeviceUnit.objects.create(
                rack_id=rack,
                device_id=device_id,
                device_publisher_id=device_publisher,
                device_model_id=device_model,
                device_number=device_number,
                electricity=electricity,
                provider_contract=provider_contract,
                status=DeviceStatus.objects.get(name="o'rnatilgan"),
                provider=InternetProvider.objects.get(pk=provider)
            )
            device.save()
            for i in range(start, end+1):
                unit = Unit.objects.get(Q(number=i), Q(rack_id=rack))
                unit.device = device
                unit.is_busy = True
                unit.contract.id = contract
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
        return Response(serializer.data)


class DeleteDeviceAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        device_id = int(request.GET.get('device_id'))
        device = DeviceUnit.objects.get(pk=device_id)
        start = device.start
        end = device.end
        for i in range(start, end + 1):
            unit = Unit.objects.get(Q(number=i), Q(rack_id=rack))
            unit.device = None
            unit.is_busy = False
            unit.contract.id = None
            unit.save()
        device.status = DeviceStatus.objects.get(name="qaytarilgan")
        device.save()
        return Response(status=204)
