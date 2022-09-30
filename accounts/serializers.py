from rest_framework import serializers
from .models import Group, RolePermission, Role, Permission, FizUser, YurUser


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


class FizUserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return FizUser.objects.create(**validated_data)

    class Meta:
        model = FizUser
        fields = '__all__'


class YurUserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return YurUser.objects.create(**validated_data)

    class Meta:
        model = YurUser
        fields = '__all__'
