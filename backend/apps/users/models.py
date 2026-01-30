"""
用户管理模型
使用Django默认User模型
"""

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """用户扩展信息

    Epic 8: 管理员后台系统增强
    Story 8.3: 密码重置功能
    Story 8.4: 强制修改密码
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="用户"
    )
    must_change_password = models.BooleanField(
        default=False, verbose_name="必须修改密码", help_text="用户下次登录时必须修改密码"
    )

    class Meta:
        verbose_name = "用户扩展信息"
        verbose_name_plural = "用户扩展信息"

    def __str__(self):
        return f"{self.user.username}的扩展信息"
