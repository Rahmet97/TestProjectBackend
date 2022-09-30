from rest_framework import permissions

from .models import RolePermission


class SuperAdminPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class EmployeePermission(permissions.BasePermission):

    def has_permission(self, request, view):

        try:
            return bool(
                request.user
            )
        except:
            return False
