from rest_framework import permissions


class IsRelatedToExpertiseBackOffice(permissions.BasePermission):
    message = "You mustn't be the client of this objects."

    def has_permission(self, request, view):
        return (
            request.user and \
            request.user.is_authenticated and \
            request.user.role.name == "mijoz"
        )
