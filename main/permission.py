from rest_framework import permissions

PERMITED_ROLES = ["iqtisodchi", "yurist", "dasturchi",  "bo'lim boshlig'i" "direktor o'rinbosari", "direktor"]

class IsAndPinnedToService(permissions.BasePermission):
    message = 'Bu user tizmga kirmagan yoki service ga pinned qilinmagan'

    def has_object_permission(self, request, view, obj):
        return (
            (obj.service.pinned_user == request.user) or \
            (request.user.role.name  != "mijoz") 
        )
    