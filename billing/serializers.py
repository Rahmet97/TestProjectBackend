from rest_framework import serializers
from django.contrib.postgres.fields import ArrayField


class RequestSerializer(serializers.Serializer):
    service = serializers.IntegerField()
    tariff = serializers.IntegerField()
    count = serializers.IntegerField()
    device_count = serializers.IntegerField(default=0)
    elements = ArrayField(serializers.JSONField(), size=15)


class ResponseSerializer(serializers.Serializer):
    amounts = ArrayField(serializers.JSONField(), size=15)
    total = serializers.FloatField()
