from datetime import datetime

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
    # date = serializers.DateTimeField(read_only=True)

    day_time = serializers.DateField(write_only=True)
    time = serializers.TimeField(write_only=True)

    def get_group(self, obj):
        return obj.service.group.name

    class Meta:
        model = InvoiceElements
        # fields = '__all__'
        exclude = ["date"]

    def update(self, instance, validated_data):
        # extract the date and time fields from the validated data
        day_time = validated_data.get('day_time', instance.date.date())
        time = validated_data.get('time', instance.date.time())

        # get the time component of the time field using datetime.time()
        time_component = time.time() if isinstance(time, datetime) else time

        # combine the date and time fields into a single datetime object
        combined_datetime = datetime.combine(day_time, time_component)

        # update the instance's date field with the combined datetime object
        instance.date = combined_datetime

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
        data['day_time'] = instance.date.date()
        data['time'] = instance.date.time()
        return data
