"""用户认证视图"""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    用户登录视图
    POST /api/v1/users/login/
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # 生成JWT token
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "登录成功",
                "data": {
                    "user": UserSerializer(user).data,
                    "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
                },
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    """
    用户注册视图
    POST /api/v1/users/register/
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成JWT token
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "success": True,
                "message": "注册成功",
                "data": {
                    "user": UserSerializer(user).data,
                    "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """
    用户登出视图
    POST /api/v1/users/logout/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({"success": True, "message": "登出成功"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "message": "登出失败", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    获取/更新用户信息
    GET/PUT/PATCH /api/v1/users/profile/
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({"success": True, "message": "更新成功", "data": serializer.data})


class ChangePasswordView(APIView):
    """
    修改密码
    POST /api/v1/users/change-password/
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"success": True, "message": "密码修改成功"}, status=status.HTTP_200_OK)
