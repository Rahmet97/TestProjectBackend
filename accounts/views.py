import logging
from datetime import datetime

from django.db import transaction
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, response, views, permissions

from main.utils import responseErrorMessage

from .models import Group, Role, Permission, UserData, YurUser, FizUser, BankMFOName, RolePermission, UniconDatas
from .permissions import SuperAdminPermission, WorkerPermission
from .serializers import (
    GroupSerializer, RoleSerializer, PermissionSerializer, PinUserToGroupRoleSerializer,
    YurUserSerializer, FizUserSerializer, BankMFONameSerializer, UniconDataSerializer
)

logger = logging.getLogger(__name__)


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


class RoleListAPIView(generics.ListAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (SuperAdminPermission,)


class RoleCreateAPIView(views.APIView):
    permission_classes = (SuperAdminPermission,)

    def post(self, request):
        group_id = request.POST.get('group', None)
        role_name = request.POST.get('role_name')
        permission_list = request.POST.get('permissions')

        if Role.objects.filter(name=role_name).exists():
            role = Role.objects.get(name=role_name)
        else:
            role = Role.objects.create(name=role_name)
            role.save()

        if group_id is not None:
            group = Group.objects.get(pk=group_id)
        else:
            group = None

        for permission in permission_list:
            permission_detail = Permission.objects.get(pk=permission['permission_id'])
            if not RolePermission.objects.filter(Q(group=group), Q(role=role),
                                                 Q(permissions=permission_detail)).exists():
                role_permission = RolePermission.objects.create(
                    group=group,
                    role=role,
                    permissions=permission_detail,
                    create=bool(int(permission['create'])),
                    read=bool(int(permission['read'])),
                    update=bool(int(permission['update'])),
                    delete=bool(int(permission['delete']))
                )
                role_permission.save()

        return response.Response(status=200)


class RoleUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = (SuperAdminPermission,)

    def update(self, request, *args, **kwargs):
        role = self.get_object()
        serializer = self.get_serializer(instance=role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        role.refresh_from_db()  # Reload the object from the database with the updated values

        # Create the historical record with the user and user_role fields
        if request.user.is_authenticated:
            # history_record = role.history.last()
            history_record = role.history.first()
            history_record.history_user = request.user
            # history_record.user_role = user_role
            history_record.save()

        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()


class RoleDetailAPIView(generics.RetrieveAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [SuperAdminPermission]


class PermissionCreateAPIView(generics.CreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (SuperAdminPermission,)


class PermissionListAPIView(generics.ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    # cache_backend = RedisCache

    def get_queryset(self):
        role_permissions = RolePermission.objects.filter(
            Q(group__in=self.request.user.group.all()),
            Q(role=self.request.user.role),
            # (
            #         Q(create=True) |
            #         Q(read=True) |
            #         Q(update=True) |
            #         Q(delete=True)
            # )
        ).values('permissions')
        logging.error(f"144 role_permissions --> permissions: {role_permissions}")
        queryset = Permission.objects.filter(pk__in=role_permissions)
        return queryset


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


class GetUsersForBackOffice(views.APIView):
    permission_classes = []

    def get(self, request):
        query = request.GET.get('query')
        if query not in ["wl", "ee"]:
            return responseErrorMessage(message="404 NOT FOUND ERROR", status_code=status.HTTP_404_NOT_FOUND)

        user_datas_fiz, user_datas_yur = None, None
        if query == "wl":
            user_datas_fiz = FizUser.objects.filter(userdata__status_action=2, userdata__type=1)
            user_datas_yur = YurUser.objects.filter(userdata__status_action=2, userdata__type=2)
        elif query == "ee":
            user_datas_fiz = FizUser.objects.filter(userdata__status_action=3, userdata__type=1)
            user_datas_yur = YurUser.objects.filter(userdata__status_action=3, userdata__type=2)

        serialized_data = {
            "fiz_users": FizUserSerializer(user_datas_fiz, many=True).data,
            "yur_users": YurUserSerializer(user_datas_yur, many=True).data
        }

        return response.Response(data=serialized_data, status=status.HTTP_200_OK)


class GetUsersDetailForBackOffice(views.APIView):
    permission_classes = []

    def post(self, request, pk):
        user = UserData.objects.get(pk=pk)
        user.status_action = 3
        user.save()


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
    serializer_class = UniconDataSerializer
    permission_classes = [WorkerPermission]

    def refresh_unicon_data(self):
        # Delete all UniconDatas objects
        UniconDatas.objects.all().delete()
        # Get the YurUser object for the director with the "direktor" role
        unicon_director_obj = YurUser.objects.get(userdata__role__name="direktor")
        # Serialize the director object using YurUserSerializer
        unicon_director_serializer = YurUserSerializer(unicon_director_obj)
        # Get the serialized data for the director object
        unicon_data = unicon_director_serializer.data
        # Get the bank MFO for the director object
        bank_mfo = unicon_director_obj.bank_mfo
        # Add the bank MFO and short name to the serialized data
        unicon_data["bank_mfo"] = bank_mfo.pk
        unicon_data["short_name"] = unicon_data["name"]
        # Create a new instance of the serializer class with the updated data
        unicon_serializer = self.serializer_class(data=unicon_data)
        # Check if the data is valid and raise an exception if it's not
        unicon_serializer.is_valid(raise_exception=True)
        # Save the serialized data to a new UniconDatas object
        unicon_serializer.save()

    def get_obj(self):
        if UniconDatas.objects.count() == 1:
            return UniconDatas.objects.last()

        self.refresh_unicon_data()
        return UniconDatas.objects.last()

    # Unicon data larini olish ya'ni unicon directorini
    def get(self, request):
        serializer = self.serializer_class(self.get_obj())
        return response.Response(data=serializer.data, status=status.HTTP_200_OK)

    # Unicon data larini ozgartirish ya'ni unicon directorini
    def patch(self, request):
        if request.data.get("bank_mfo") is not None:
            bank_mfo = BankMFOName.objects.get(mfo=request.data.get("bank_mfo"))
            request.data["bank_mfo"] = bank_mfo.pk

        unicon_obj = self.get_obj()
        serializer = self.serializer_class(unicon_obj, request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        unicon_obj.refresh_from_db()  # Reload the object from the database with the updated values
        # Create the historical record with the user and user_role fields
        if request.user.is_authenticated:
            history_record = unicon_obj.history.first()
            history_record.history_user = request.user
            history_record.save()

        return response.Response(data=serializer.data, status=status.HTTP_200_OK)
