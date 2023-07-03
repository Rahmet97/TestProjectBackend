import logging

from rest_framework import serializers

from contracts.models import Service
from .models import Group, RolePermission, Role, Permission, FizUser, YurUser, UserData, BankMFOName, UniconDatas

logger = logging.getLogger(__name__)


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = ["id", "name", "slug"]


class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = "__all__"


class ContactFizUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FizUser
        fields = ('',)


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = "__all__"


class PermissionSerializer(serializers.ModelSerializer):

    # def create(self, validated_data):
    #     return Permission.objects.create(**validated_data)

    class Meta:
        model = Permission
        fields = "__all__"


class UserDataSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    # group = GroupSerializer(many=True)

    class Meta:
        model = UserData
        fields = ('id', 'username', 'role',  'type')  # 'group', 'type')

    def to_representation(self, instance):
        context = super().to_representation(instance)

        # services = []
        # for group in instance.group.all():
        #     services.extend(ServiceSerializer(group.service_group.all(), many=True).data)
        #
        # services = [
        #     service for group in instance.group.all()
        #     for service in ServiceSerializer(group.service_group.all(), many=True).data
        # ]

        context["service"] = [
            service for group in instance.group.all()
            for service in ServiceSerializer(group.service_group.all(), many=True).data
        ]
        return context


class FizUserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return FizUser.objects.create(**validated_data)

    class Meta:
        model = FizUser
        fields = '__all__'


class FizUserSerializerForContractDetail(serializers.ModelSerializer):
    userdata = UserDataSerializer()

    class Meta:
        model = FizUser
        fields = '__all__'


class BankMFONameSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankMFOName
        fields = '__all__'


class YurUserSerializerForContractDetail(serializers.ModelSerializer):
    userdata = UserDataSerializer()
    bank_mfo = BankMFONameSerializer()

    class Meta:
        model = YurUser
        fields = '__all__'


class YurUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = YurUser
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["bank_mfo"] = instance.bank_mfo.mfo
        return rep


class PinUserToGroupRoleSerializer(serializers.Serializer):
    user = serializers.IntegerField()
    group = serializers.IntegerField()
    role = serializers.IntegerField()


# For old contracts
class FizUserForOldContractSerializers(serializers.ModelSerializer):
    class Meta:
        model = FizUser
        fields = ["first_name", "mid_name", "sur_name", "per_adr", "mob_phone_no", "email", "pport_no", "pin"]


class YurUserForOldContractSerializers(serializers.ModelSerializer):
    class Meta:
        model = YurUser
        fields = [
            "name", "per_adr", "director_firstname", "director_lastname", "director_middlename",
            "bank_mfo", "paymentAccount", "xxtut", "ktut", "oked", "position", "tin"
        ]


class UniconDatasHistoricalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniconDatas.history.model
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["bank_mfo"] = instance.bank_mfo.mfo

        if instance.history_user:
            history_user = UserData.objects.get(id=instance.history_user.id)
            if history_user.type == 1:  # fizik
                history_user = FizUser.objects.get(userdata=history_user).get_short_full_name
            else:
                history_user = YurUser.objects.get(userdata=history_user).get_director_short_full_name
            representation["history_user"] = history_user

        return representation


class UniconDataSerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UniconDatas
        fields = '__all__'

    @staticmethod
    def get_history(obj):
        history = obj.history.all().order_by("-id")[:10]
        serialized_history = []
        for index, h in enumerate(history):
            old_data = UniconDatasHistoricalSerializer(history[index - 1]).data if index > 0 else None
            new_data = UniconDatasHistoricalSerializer(h).data
            new_data['old_history'] = old_data
            serialized_history.append(new_data)
        return serialized_history

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["bank_mfo"] = instance.bank_mfo.mfo
        return representation
