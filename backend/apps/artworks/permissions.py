"""
权限类 (Story 12-4)

定义 artworks 应用的权限控制逻辑。

职责:
- IsOwner: 验证用户是否拥有该章节所属的作品
- 遵循单一职责原则 (SRP)
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    验证用户是否拥有该章节所属的作品

    权限逻辑:
    - 获取 Chapter 对象
    - 检查 chapter.artwork.user 是否等于请求用户

    注意: Chapter 关联到 Artwork，不是 Project

    Story 12-4: 工作流控制 API 权限类
    """

    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限访问该对象

        Args:
            request: HTTP 请求对象
            view: DRF View 实例
            obj: Chapter 模型实例

        Returns:
            bool: 如果用户拥有该作品返回 True
        """
        # obj 应该是 Chapter 实例
        # 通过 chapter.artwork.user 验证所有权（Chapter 属于 Artwork）
        return obj.artwork.user == request.user
