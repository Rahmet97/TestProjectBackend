from rest_framework import serializers
from django.contrib.postgres.fields import ArrayField

from billing.models import InvoiceElements


class RequestSerializer(serializers.Serializer):
    service = serializers.IntegerField()
    tariff = serializers.IntegerField()
    count = serializers.IntegerField(default=0)
    elements = serializers.JSONField()


class ResponseSerializer(serializers.Serializer):
    amounts = ArrayField(serializers.JSONField(), size=15)
    total = serializers.FloatField()


class InvoiceElementsSerializer(serializers.ModelSerializer):
    group = serializers.SerializerMethodField()

    def get_group(self, obj):
        return obj.service.group.name

    class Meta:
        model = InvoiceElements
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add a custom field to the representation
        data['group_service'] = {
            "group": instance.service.group.name,
            "service": instance.service.name
        }
        return data
