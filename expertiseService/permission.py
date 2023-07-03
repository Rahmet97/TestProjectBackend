from rest_framework import permissions

from accounts.models import Role


class ExpertiseConfirmContractPermission(permissions.BasePermission):
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
