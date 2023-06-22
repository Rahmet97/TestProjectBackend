from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export import resources

admin.site.register((UserData, Permission, Role, Group, LogGroup, LogPermission))


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["group", "role", "permissions"]


@admin.register(FizUser)
class FizUserAdmin(admin.ModelAdmin):
    list_display = ["pin", "get_short_full_name", "get_user_role", "display_groups"]

    def display_groups(self, obj):
        return ", ".join(group.name for group in obj.userdata.group.all())
    display_groups.short_description = "Groups"


@admin.register(YurUser)
class YurUserAdmin(admin.ModelAdmin):
    list_display = ["tin", "get_director_short_full_name", "get_user_role", "display_groups"]

    def display_groups(self, obj):
        return ", ".join(group.name for group in obj.userdata.group.all())
    display_groups.short_description = "Groups"


class BankMFOResource(resources.ModelResource):
    class Meta:
        model = BankMFOName


@admin.register(BankMFOName)
class ViewAdmin(ImportExportModelAdmin):
    resource_class = BankMFOResource


@admin.register(Departament)
class DepartamentAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]


@admin.register(DepartamentGroup)
class DepartamentGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(UniconDatas)
class UniconDatasAdmin(admin.ModelAdmin):
    pass
