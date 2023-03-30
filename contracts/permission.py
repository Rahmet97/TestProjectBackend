from rest_framework import permissions


class IsOwnContractPermission(permissions.BasePermission):
    message = 'User bu contractni yaratmagan'

    def has_object_permission(self, request, view, obj):
        return obj.client == request.user
    