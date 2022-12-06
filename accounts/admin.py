from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources

admin.site.register((UserData, FizUser, YurUser, Permission, Role, Group, LogGroup, LogPermission, RolePermission))


class BankMFOResource(resources.ModelResource):
    class Meta:
        model = BankMFOName


@admin.register(BankMFOName)
class ViewAdmin(ImportExportModelAdmin):
    resource_class = BankMFOResource
