from rest_framework import permissions

from accounts.models import Role


class IsRelatedToExpertiseBackOffice(permissions.BasePermission):
    message = "You do not have permission to view this datas"

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role.name != Role.RoleNames.CLIENT
        )
