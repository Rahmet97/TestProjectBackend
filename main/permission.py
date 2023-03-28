from rest_framework import permissions


class IsAndPinnedToService(permissions.BasePermission):
    message = 'Bu user tizmga kirmagan yoki service ga pinned qilinmagan'

    def has_object_permission(self, request, view, obj):
        return obj.service.pinned_user == request.user
    