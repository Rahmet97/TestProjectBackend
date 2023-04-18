from django.contrib import admin
from .models import DevicePublisher, DeviceUnit, Rack, Unit, DeviceStatus, InternetProvider, ProviderContract


admin.site.register((Rack, Unit, DevicePublisher, DeviceUnit, DeviceStatus, InternetProvider, ProviderContract))


class RackResource(resources.ModelResource):
    class Meta:
        model = Rack


@admin.register(Rack)
class RackAdmin(ImportExportModelAdmin):
    resource_class = RackResource


class UnitResource(resources.ModelResource):
    class Meta:
        model = Unit


@admin.register(Unit)
class UnitAdmin(ImportExportModelAdmin):
    resource_class = UnitResource


class DevicePublisherResource(resources.ModelResource):
    class Meta:
        model = DevicePublisher


@admin.register(DevicePublisher)
class DevicePublisherAdmin(ImportExportModelAdmin):
    resource_class = DevicePublisherResource


class DeviceUnitResource(resources.ModelResource):
    class Meta:
        model = DeviceUnit


@admin.register(DeviceUnit)
class DeviceUnitAdmin(ImportExportModelAdmin):
    resource_class = DeviceUnitResource


class DeviceStatusResource(resources.ModelResource):
    class Meta:
        model = DeviceStatus


@admin.register(DeviceStatus)
class DeviceStatusAdmin(ImportExportModelAdmin):
    resource_class = DeviceStatusResource


class InternetProviderResource(resources.ModelResource):
    class Meta:
        model = InternetProvider


@admin.register(InternetProvider)
class InternetProviderAdmin(ImportExportModelAdmin):
    resource_class = InternetProviderResource
