from django.contrib import admin
from .models import DevicePublisher, DeviceUnit, Rack, Unit, DeviceStatus, InternetProvider, ProviderContract


admin.site.register((Rack, Unit, DevicePublisher, DeviceUnit, DeviceStatus))
