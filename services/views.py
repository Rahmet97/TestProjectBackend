from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import DeviceUnit, Rack, Unit
from .serializers import DeviceUnitSerializer, GetRackInformationSerializer, RackSerializer, UnitSerializer


class RackAPIView(APIView):
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
        units = Unit.objects.filter(rack=rack).order_by('number')
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


class UpdateRackAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        pass


class AddDeviceAPIView(APIView):
    permission_classes = ()

    def post(self, request):
        pass
