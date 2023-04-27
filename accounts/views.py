from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, response, views, permissions

from .models import Group, Role, Permission, UserData, YurUser, FizUser, BankMFOName
from .permissions import SuperAdminPermission, WorkerPermission
from .serializers import (
    GroupSerializer, RoleSerializer, PermissionSerializer, PinUserToGroupRoleSerializer,
    YurUserSerializer, FizUserSerializer, BankMFONameSerializer
)


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
    permission_classes = (permissions.IsAuthenticated,)


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
    permission_classes = (permissions.IsAuthenticated,)
    # cache_backend = RedisCache


class PermissionUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (SuperAdminPermission,)


class PinUserToGroupRole(views.APIView):
    permission_classes = (SuperAdminPermission,)

    @swagger_auto_schema(
        operation_summary="Userni Gruppaga va Role ga biriktirish",
        query_serializer=PinUserToGroupRoleSerializer()
    )
    def post(self, request):
        user = UserData.objects.get(pk=request.data['user'])
        user.group = Group.objects.get(pk=request.data['group'])
        user.role = Role.objects.get(pk=request.data['role'])
        user.save()

        return response.Response(status=200)


class UpdateYurUserAPIView(generics.UpdateAPIView):
    queryset = YurUser.objects.all()
    serializer_class = YurUserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UpdateFizUserAPIView(generics.UpdateAPIView):
    queryset = FizUser.objects.all()
    serializer_class = FizUserSerializer
    permission_classes = (permissions.IsAuthenticated,)


class GetBankNameAPIView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        mfo = request.GET.get('mfo')
        bank = BankMFOName.objects.get(mfo=mfo)
        serializer = BankMFONameSerializer(bank)
        return response.Response(serializer.data)


class GetCurrentTimeAPIView(views.APIView):
    permission_classes = ()

    def get(self, request):
        current_time = datetime.now()
        return response.Response({'current_time': current_time})


class UniconDataAPIView(views.APIView):
    serializer_class = YurUserSerializer
    permission_classes = [WorkerPermission]

    @staticmethod
    def get_obj():
        return YurUser.objects.get(userdata__role__name="direktor")  # , tin="123456789")

    # Unicon data larini olish ya'ni unicon directorini
    def get(self, request):
        serializer = self.serializer_class(self.get_obj())
        return response.Response(data=serializer.data, status=status.HTTP_200_OK)

    # Unicon data larini ozgartirish ya'ni unicon directorini
    def patch(self, request):
        serializer = self.serializer_class(self.get_obj(), request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.data.get("bank_mfo") is not None:
            bank_mfo = BankMFOName.objects.get(mfo=request.data.get("bank_mfo"))
            serializer.save(bank_mfo=bank_mfo)
        else:
            serializer.save()
        return response.Response(data=serializer.data, status=status.HTTP_200_OK)
