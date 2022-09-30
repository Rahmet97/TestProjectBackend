from django.contrib import admin
from .models import *

admin.site.register((UserData, FizUser, YurUser, Permission, Role, Group, LogGroup, LogPermission, RolePermission))
