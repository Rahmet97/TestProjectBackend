from rest_framework import permissions

from accounts.models import Role
from contracts.models import Service


class ApplicationPermission(permissions.BasePermission):
    message = "You don't have permission for this section"
    permitted_roles = [
        Role.RoleNames.ADMIN,

        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,
        Role.RoleNames.SECTION_SPECIALIST,
    ]

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.role is not None)
        )

    def has_object_permission(self, request, view, obj):
        return (
                (obj.service.pinned_user == request.user) or
                (request.user.role.name in self.permitted_roles)
        )


class MonitoringPermission(permissions.BasePermission):
    message = "You don't have permission for this section"
    permitted_roles = [
        Role.RoleNames.ADMIN,
        Role.RoleNames.ACCOUNTANT,
        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,
        Role.RoleNames.SECTION_SPECIALIST,
    ]

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.role is not None) and
                (
                        (request.user.role.name in self.permitted_roles) or
                        (Service.objects.filter(pinned_user=request.user).exists())
                )
        )


class IsRelatedToBackOffice(permissions.BasePermission):
    message = "You do not have permission to view this datas"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role.name != Role.RoleNames.CLIENT
        )


class ConfirmContractPermission(permissions.BasePermission):
    message = "You don't have permission for this section"
    permitted_roles = [
        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,
    ]

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.role is not None) and
                request.user.role.name in self.permitted_roles
        )
