"""
强制修改密码中间件

Epic 8: 管理员后台系统增强
Story 8.4: 强制修改密码

功能:
- 检查用户的must_change_password标志
- 如果为True，拦截所有请求（除白名单）
- 返回403 Forbidden，要求用户修改密码
- 修改密码后清除标志

Party Mode决策1: 纯Middleware方案
- 单一逻辑：所有请求统一检查
- 覆盖所有请求：API和Admin都检查
- 安全第一：请求管道最外层
"""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class MustChangePasswordMiddleware(MiddlewareMixin):
    """
    强制修改密码中间件

    检查已认证用户的must_change_password标志，
    如果为True，则拦截请求并返回403 Forbidden。

    白名单路径:
    - /api/auth/change-password/ - 修改密码API
    - /api/auth/login/ - 登录API
    - /api/auth/logout/ - 登出API
    - /admin/login/ - Admin登录
    - /admin/logout/ - Admin登出
    - /static/ - 静态文件
    - /media/ - 媒体文件

    安全考虑:
    - 只检查已认证用户
    - 不影响未认证用户（由其他中间件处理）
    - 白名单路径不受影响
    """

    # 白名单路径前缀
    WHITE_LIST_PREFIXES = [
        "/api/auth/change-password",
        "/api/auth/login",
        "/api/auth/logout",
        "/admin/login",
        "/admin/logout",
        "/static/",
        "/media/",
    ]

    def process_request(self, request):
        """
        处理请求

        Args:
            request: HttpRequest对象

        Returns:
            JsonResponse if user must change password, None otherwise
        """
        # 1. 检查用户是否已认证
        if not request.user.is_authenticated:
            # 未认证用户，跳过检查（由其他中间件处理认证）
            return None

        # 2. 检查是否在白名单路径
        if self._is_white_listed_path(request.path):
            # 白名单路径，跳过检查
            return None

        # 3. 检查must_change_password标志
        try:
            if request.user.profile.must_change_password:
                # 用户需要修改密码，返回403
                return JsonResponse(
                    {
                        "error": "必须修改密码后才能访问系统",
                        "error_code": "MUST_CHANGE_PASSWORD",
                        "change_password_url": "/api/auth/change-password/",
                    },
                    status=403,
                )
        except AttributeError:
            # UserProfile不存在（可能是测试环境），跳过检查
            pass

        # 4. 用户正常，允许访问
        return None

    def _is_white_listed_path(self, path):
        """
        检查路径是否在白名单中

        Args:
            path: 请求路径

        Returns:
            bool: True如果在白名单中，False否则
        """
        return any(
            path.startswith(prefix) or path == prefix.rstrip("/")
            for prefix in self.WHITE_LIST_PREFIXES
        )
