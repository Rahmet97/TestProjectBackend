from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import GroupCreateAPIView, GroupUpdateDeleteAPIView, PinUserToGroupRole, RoleCreateAPIView, \
    PermissionCreateAPIView, GroupListAPIView, PermissionListAPIView, RoleUpdateDeleteAPIView, \
    PermissionUpdateDeleteAPIView, GroupDetailAPIView, UpdateYurUserAPIView, UpdateFizUserAPIView

urlpatterns = [
    path('role-create', RoleCreateAPIView.as_view(), name='RoleCreate'),
    path('permission-create', PermissionCreateAPIView.as_view(), name='PermissionCreate'),
    path('group-create', GroupCreateAPIView.as_view(), name='CustomGroupCreate'),
    path('group-list', GroupListAPIView.as_view(), name='CustomGroupList'),
    path('permission-list', PermissionListAPIView.as_view(), name='PermissionList'),
    path('group-update-delete/<int:pk>/', GroupUpdateDeleteAPIView.as_view(), name='CustomGroupUpdateDelete'),
    path('group-detail/<int:pk>/', GroupDetailAPIView.as_view(), name='CustomGroupDetailAPIView'),
    path('pin-user', PinUserToGroupRole.as_view(), name='PinUserToGroupRole'),
    path('role-update-delete/<int:pk>/', RoleUpdateDeleteAPIView.as_view(), name='RoleUpdateDelete'),
    path('permission-update-delete/<int:pk>/', PermissionUpdateDeleteAPIView.as_view(), name='PermissionUpdateDelete'),
    path('update-yuruser/<int:pk>', UpdateYurUserAPIView.as_view(), name='UpdateYurUserAPIView'),
    path('update-fizuser/<int:pk>', UpdateFizUserAPIView.as_view(), name='UpdateFizUserAPIView'),
]
