from rest_framework import permissions


class IsRelatedToExpertise(permissions.BasePermission):
    message = 'You must be the owner of this object.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if True:
            
            return obj.client == request.user
        return False