from rest_framework import serializers
from django.db.models import Q, Sum

from contracts.models import UserContractTarifDevice
from contracts.serializers import DeviceSerializer, ContractSerializerForBackoffice

from .models import DevicePublisher, DeviceUnit, Rack, Unit, InternetProvider, ProviderContract


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class RackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rack
        fields = '__all__'


class InternetProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternetProvider
        fields = '__all__'


class ProviderContractSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProviderContract
        fields = '__all__'


class RackForGetSerializer(serializers.ModelSerializer):
    contract = ContractSerializerForBackoffice()
    provider = InternetProviderSerializer()
    provider_contract = ProviderContractSerializer()
    odf_count = serializers.SerializerMethodField()

    def get_odf_count(self, obj):
        if obj.contract:
            odf_count = UserContractTarifDevice.objects.get(contract=obj.contract).odf_count
        else:
            odf_count = 0
        return odf_count

    class Meta:
        model = Rack
        fields = '__all__'


class GetRackInformationSerializer(serializers.ModelSerializer):
    units = serializers.SerializerMethodField()
    electricity = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    @staticmethod
    def get_units(obj):
        devices = Unit.objects.filter(rack=obj).exclude(device=None)
        return devices.count()

    @staticmethod
    def get_electricity(obj):
        # elect = Unit.objects.filter(rack=obj).distinct().aggregate(Sum('device__electricity'))
        # Bu Django ORM script codeni boshqatan korish kk chunki duplicate malumotlarniyam hisob qoyishi mumkin bazada
        # filter_conditions = Q(rack__unit__contract=contract) & Q(status__name="o'rnatilgan")
        # empty_electricity = DeviceUnit.objects.filter(filter_conditions).distinct().aggregate(Sum('electricity'))
        return Unit.objects.filter(rack=obj).device_units.all().distinct().aggregate(Sum('electricity'))

    @staticmethod
    def get_percentage(obj):
        devices_count = Unit.objects.filter(rack=obj).exclude(device=None).count()
        return devices_count / obj.unit_count * 100

    class Meta:
        model = Rack
        fields = '__all__'


class DevicePublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevicePublisher
        fields = '__all__'


class DeviceUnitSerializer(serializers.ModelSerializer):
    device = DeviceSerializer()
    device_publisher = DevicePublisherSerializer()
    provider = InternetProviderSerializer()

    class Meta:
        model = DeviceUnit
        fields = '__all__'
