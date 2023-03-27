from rest_framework import serializers
from .models import Application

from accounts.models import FizUser, YurUser
from accounts.serializers import FizUserForOldContractSerializers, YurUserForOldContractSerializers


class ApplicationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    service = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ["pk", "user", "service", "name", "phone", "email", "message", "created_at", "file"]


    @staticmethod
    def get_user(obj):
        user_obj = obj.user
        print("user >>>> ", user_obj)
        if user_obj.type == 1:  # fiz
            serializer = FizUserForOldContractSerializers(FizUser.objects.get(userdata=user_obj))
            data = serializer.data
            data['u_type'] = 'Fizik'
        else:
            serializer = YurUserForOldContractSerializers(YurUser.objects.get(userdata=user_obj))
            data = serializer.data
            data['u_type'] = 'Yuridik'
        return data
    
    @staticmethod
    def get_service(obj):
        return {
            "pk": obj.service.pk,
            "name": obj.service.name
        }
    