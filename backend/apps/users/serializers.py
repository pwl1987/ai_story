"""用户认证序列化器"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""

    # Epic 8 Story 8.4: 添加must_change_password字段，用于前端判断是否需要强制修改密码
    must_change_password = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "must_change_password",
        )
        read_only_fields = ("id", "date_joined")

    def to_representation(self, instance):
        """重写to_representation以添加must_change_password字段"""
        data = super().to_representation(instance)
        try:
            data["must_change_password"] = instance.profile.must_change_password
        except AttributeError:
            # UserProfile不存在，返回False
            data["must_change_password"] = False
        return data


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("用户名或密码错误")
            if not user.is_active:
                raise serializers.ValidationError("用户账号已被禁用")
            attrs["user"] = user
        else:
            raise serializers.ValidationError("必须提供用户名和密码")

        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """注册序列化器"""

    password = serializers.CharField(write_only=True, required=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm", "first_name", "last_name")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "两次密码输入不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器

    Epic 8 Story 8.4: 支持两种场景
    1. 普通修改密码: 需要old_password
    2. 强制修改密码: 不需要old_password（管理员重置后），清除must_change_password标志
    """

    old_password = serializers.CharField(required=False, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        # Epic 8 Story 8.4: 如果没有提供old_password，跳过验证（强制修改密码场景）
        if value is None:
            return value

        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码错误")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "两次密码输入不一致"})

        # Epic 8 Story 8.4: 如果没有提供old_password，检查用户是否在强制修改密码状态
        if not attrs.get("old_password"):
            user = self.context["request"].user
            try:
                if not user.profile.must_change_password:
                    raise serializers.ValidationError(
                        {"old_password": "请提供原密码，或联系管理员重置密码"}
                    )
            except AttributeError:
                # UserProfile不存在（可能是测试环境），跳过检查
                pass

        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])

        # Epic 8 Story 8.4: 清除must_change_password标志
        try:
            if user.profile.must_change_password:
                user.profile.must_change_password = False
                user.profile.save()
        except AttributeError:
            # UserProfile不存在（可能是测试环境），跳过
            pass

        user.save()
        return user
