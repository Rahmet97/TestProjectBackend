from rest_framework import permissions

from accounts.models import Role


class VpsServiceContractDeletePermission(permissions.BasePermission):
    message = "You don't have permission for this section"
    permitted_roles = [
        Role.RoleNames.ADMIN,

        Role.RoleNames.DIRECTOR,
        Role.RoleNames.DEPUTY_DIRECTOR,
        Role.RoleNames.DEPARTMENT_BOSS,
        Role.RoleNames.SECTION_HEAD,

        # Role.RoleNames.CLIENT,
    ]

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.role is not None)
        )

    def has_object_permission(self, request, view, obj):
        return (
                (obj.client == request.user) or
                (request.user.role.name in self.permitted_roles)
        )
