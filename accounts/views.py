from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Group, Role, Permission, UserData
from rest_framework import generics

from .permissions import SuperAdminPermission, EmployeePermission
from .serializers import GroupSerializer, RoleSerializer, PermissionSerializer


class GroupCreateAPIView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (SuperAdminPermission,)


class GroupListAPIView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)


class GroupUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (SuperAdminPermission,)


class RoleCreateAPIView(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (SuperAdminPermission,)


class RoleUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (SuperAdminPermission,)


class PermissionCreateAPIView(generics.CreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (SuperAdminPermission,)


class PermissionListAPIView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (IsAuthenticated,)


class PermissionUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (SuperAdminPermission,)


class PinUserToGroupRole(APIView):
    permission_classes = (SuperAdminPermission,)

    def post(self, request):
        user = UserData.objects.get(pk=request.data['user'])
        user.group = Group.objects.get(pk=request.data['group'])
        user.role = Role.objects.get(pk=request.data['role'])
        user.save()

        return Response(status=200)
