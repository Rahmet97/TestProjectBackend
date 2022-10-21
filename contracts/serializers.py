from rest_framework import serializers

from accounts.serializers import GroupSerializer
from .models import Service, Tarif, Device, Contract, UserContractTarifDevice, UserDeviceCount, Offer, Document, \
    Element, TarifElement, SavedService


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    need_documents = DocumentSerializer(many=True)
    group = GroupSerializer()
    user_type = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    def get_user_type(self, obj):
        if obj.user_type == 1:
            return "Jismoniy"
        elif obj.user_type == 2:
            return "Yuridik"
        else:
            return "Jismoniy va Yuridik"

    def get_is_saved(self, obj):
        try:
            request = self.context.get('request', None)
            print(request)
            saved_service = SavedService.objects.get(user=request.user)
            if obj in saved_service.services.all():
                return True
            else:
                return False
        except:
            return False

    class Meta:
        model = Service
        fields = ('id', 'name', 'description', 'image', 'user_type', 'period', 'need_documents', 'group', 'is_saved')


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


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = '__all__'


class TarifElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarifElement
        fields = '__all__'



