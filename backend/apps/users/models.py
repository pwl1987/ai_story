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


class UserProxy(User):
    """
    User Proxy Model - 重写delete方法实现级联删除

    Epic 8 Story 8.9: 用户删除级联删除

    功能:
    - 删除用户时级联删除用户资源
    - 删除管理员时转移系统资源所有权
    - 避免 ProtectedError
    """

    class Meta:
        proxy = True

    def delete(self, *args, **kwargs):
        """
        重写delete方法，处理资源级联删除

        Epic 8 Story 8.9: 用户删除级联删除

        规则:
        - 系统资源 (is_system_default=True): 转移所有权给第一个可用的 superuser
        - 用户资源 (is_system_default=False): 级联删除
        - 阻止删除最后一个 superuser
        """
        # 阻止删除最后一个 superuser
        if self.is_superuser:
            other_superusers = User.objects.filter(is_superuser=True).exclude(id=self.id)
            if not other_superusers.exists():
                raise Exception("不能删除最后一个超级用户")
        from apps.models.models import ModelProvider
        from apps.prompts.models import PromptTemplateSet

        # 获取第一个可用的 superuser（如果不是当前用户）
        alternative_superuser = (
            User.objects.filter(is_superuser=True).exclude(id=self.id).order_by("id").first()
        )

        # 处理 ModelProvider
        user_models = ModelProvider.objects.filter(created_by=self)

        for model in user_models:
            if model.is_system_default:
                # 系统资源：转移所有权
                if alternative_superuser:
                    model.created_by = alternative_superuser
                    model.save(update_fields=["created_by"])
                else:
                    # 如果没有其他 superuser，级联删除系统资源
                    model.delete()
            else:
                # 用户资源：级联删除
                model.delete()

        # 处理 PromptTemplateSet
        user_prompt_sets = PromptTemplateSet.objects.filter(created_by=self)

        for prompt_set in user_prompt_sets:
            if prompt_set.is_system_default:
                # 系统资源：转移所有权
                if alternative_superuser:
                    prompt_set.created_by = alternative_superuser
                    prompt_set.save(update_fields=["created_by"])
                else:
                    # 如果没有其他 superuser，级联删除系统资源
                    prompt_set.delete()
            else:
                # 用户资源：级联删除
                prompt_set.delete()

        # 调用父类的delete方法
        super().delete(*args, **kwargs)
