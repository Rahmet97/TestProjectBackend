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


class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role.name == "bo'lim boshlig'i"
        except:
            return False


class DirectorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role.name == "direktor"
        except:
            return False


class DeputyDirectorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.role.name == "bo'lim boshlig'i" or request.user.role.name == "direktor o'rinbosari" or request.user.role.name == "direktor"
        except:
            return False


class WorkerPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        try:
            return request.user.role != '' and request.user.role.name != 'mijoz'
        except:
            return False
