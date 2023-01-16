from django.contrib import admin
from .models import DevicePublisher, DeviceUnit, Rack, Unit


admin.site.register((Rack, Unit, DevicePublisher, DeviceUnit))