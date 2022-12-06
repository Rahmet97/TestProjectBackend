from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Group, Role, Permission, UserData, YurUser, FizUser, BankMFOName
from rest_framework import generics

from .permissions import SuperAdminPermission, EmployeePermission, AdminPermission
from .serializers import GroupSerializer, RoleSerializer, PermissionSerializer, PinUserToGroupRoleSerializer, \
    YurUserSerializer, FizUserSerializer, BankMFONameSerializer


class GroupCreateAPIView(generics.CreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (SuperAdminPermission,)


class GroupListAPIView(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = ()


class GroupUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (SuperAdminPermission,)


class GroupDetailAPIView(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)


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

    @swagger_auto_schema(operation_summary="Userni Gruppaga va Role ga biriktirish", query_serializer=PinUserToGroupRoleSerializer)
    def post(self, request):
        user = UserData.objects.get(pk=request.data['user'])
        user.group = Group.objects.get(pk=request.data['group'])
        user.role = Role.objects.get(pk=request.data['role'])
        user.save()

        return Response(status=200)


class UpdateYurUserAPIView(generics.UpdateAPIView):
    queryset = YurUser.objects.all()
    serializer_class = YurUserSerializer
    permission_classes = (IsAuthenticated,)


class UpdateFizUserAPIView(generics.UpdateAPIView):
    queryset = FizUser.objects.all()
    serializer_class = FizUserSerializer
    permission_classes = (IsAuthenticated,)


class GetBankNameAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        mfo = request.GET.get('mfo')
        bank = BankMFOName.objects.get(mfo=mfo)
        serializer = BankMFONameSerializer(bank)
        return Response(serializer.data)
