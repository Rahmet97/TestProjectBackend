from rest_framework import serializers
from .models import Application

from accounts.serializers import FizUserSerializerForContractDetail, YurUserSerializerForContractDetail


class ApplicationSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    service = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ["user", "service", "name", "phone", "email", "message", "created_at", "file"]
        # exclude = ["user"]
    
    def get_user(self, obj):
        user = obj.pinned_user
        if user.user_type == 1:  # fiz
            serializer = FizUserSerializerForContractDetail(user)
            data = serializer.data
            data['u_type'] = 'Fizik'
        else:
            serializer = YurUserSerializerForContractDetail(user)
            data = serializer.data
            data['u_type'] = 'Yuridik'
        return data
    
    def get_service(self, obj):
        return {
            "pk": obj.service.pk,
            "name": obj.service.name
        }
