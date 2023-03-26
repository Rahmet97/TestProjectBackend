from rest_framework import permissions


class IsAuthenticatedAndPinnedToService(permissions.BasePermission):
    message = 'Bu user tizmga kirmagan yoki service ga pinned qilinmagan'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.service.pinned_user == request.user
    