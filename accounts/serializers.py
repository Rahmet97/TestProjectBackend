from rest_framework import serializers
from .models import Group, RolePermission, Role, Permission, FizUser, YurUser, UserData, BankMFOName, UniconDatas


class GroupSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return Group.objects.create(**validated_data)

    class Meta:
        model = Group
        fields = "__all__"


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

    def create(self, validated_data):
        return Permission.objects.create(**validated_data)

    class Meta:
        model = Permission
        fields = "__all__"


class UserDataSerializer(serializers.ModelSerializer):
    role = RoleSerializer()
    group = GroupSerializer(many=True)

    class Meta:
        model = UserData
        fields = ('id', 'username', 'role', 'group', 'type')


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
    bank_mfo = serializers.SerializerMethodField()

    def create(self, validated_data):
        return YurUser.objects.create(**validated_data)

    @staticmethod
    def get_bank_mfo(obj):
        return obj.bank_mfo.mfo

    class Meta:
        model = YurUser
        fields = '__all__'


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
