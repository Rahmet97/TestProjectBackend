from rest_framework import serializers
from .models import Service, Tarif, Device, Contract, UserContractTarifDevice, UserDeviceCount, Offer, Document, \
    Element, TarifElement


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class TarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarif
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class ContractSerializer(serializers.ModelSerializer):

    contract_number = serializers.SerializerMethodField()

    def get_contract_number(self, obj):
        group_names = obj.service.group.name.split()
        c_number = ''
        for i in group_names:
            c_number += i[0]
        return c_number

    class Meta:
        model = Contract
        fields = '__all__'


class UserContractTarifDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserContractTarifDevice
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class UserDeviceCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceCount
        fields = '__all__'


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = '__all__'


class TarifElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarifElement
        fields = '__all__'



