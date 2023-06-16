from datetime import datetime
from django.utils import timezone

from rest_framework import serializers
from django.contrib.postgres.fields import ArrayField

from billing.models import InvoiceElements
from vpsService.models import VpsDevice, OperationSystemVersion, VpsTariff


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
    # date = serializers.DateTimeField(read_only=True)

    day_time = serializers.DateField(write_only=True)
    time = serializers.TimeField(write_only=True)

    def get_group(self, obj):
        return obj.service.group.name

    class Meta:
        model = InvoiceElements
        exclude = ["date"]

    def update(self, instance, validated_data):
        # extract the date and time fields from the validated data
        day_time = validated_data.get('day_time', instance.date.date())
        time = validated_data.get('time', instance.date.time())

        # get the time component of the time field using datetime.time()
        time_component = time.time() if isinstance(time, datetime) else time

        # combine the date and time fields into a single datetime object
        combined_datetime = timezone.make_aware(
            datetime.combine(day_time, time_component), timezone.get_current_timezone()
        )

        # update the instance's date field with the combined datetime object
        instance.date = combined_datetime
        instance.service = validated_data.get("service", instance.service.pk)
        instance.is_automate = validated_data.get("is_automate", instance.is_automate)

        # save and return the updated instance
        instance.save()
        return instance

    def create(self, validated_data):
        # Extract the relevant data from validated_data
        day_time = validated_data.pop('day_time')
        time = validated_data.pop('time')

        # combine the date and time fields into a single datetime object
        combined_datetime = datetime.combine(day_time, time)

        # Create a new instance of the model with the validated data
        obj = InvoiceElements.objects.create(date=combined_datetime, **validated_data)

        # Perform any additional processing or validation on the instance here
        # ...

        # Return the new instance
        return obj

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add a custom field to the representation
        data['group_service'] = {
            "group": instance.service.group.name,
            "service": instance.service.name
        }
        # Convert the datetime object to the local time zone
        local_time = timezone.localtime(instance.date)
        data['day_time'] = local_time.date()
        data['time'] = local_time.time()
        return data


# VPS Serializer for billing automations
class VpsTariffSummSerializer(serializers.ModelSerializer):
    tariff = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=VpsTariff.objects.all(), write_only=True
    )
    operation_system_versions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=OperationSystemVersion.objects.all(),  write_only=True
    )

    count_vm = serializers.IntegerField()

    class Meta:
        model = VpsDevice
        fields = [
            "id", "tariff", "storage_type", "storage_disk", "cpu", "ram", "internet", "tasix", "imut",
            "operation_system_versions", "count_vm"
        ]
