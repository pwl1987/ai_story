"""
用户删除级联处理 Signals

Epic 8 Story 8.9: 用户删除级联删除

功能:
1. 删除用户时级联删除用户资源
2. 删除管理员时转移系统资源所有权
3. 避免 ProtectedError
"""

from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete, sender=User)
def handle_user_deletion(sender, instance, **kwargs):
    """
    处理用户删除前的资源清理

    Epic 8 Story 8.9: 用户删除级联删除

    规则:
    - 系统资源 (is_system_default=True): 转移所有权给第一个可用的 superuser
    - 用户资源 (is_system_default=False): 级联删除

    Args:
        sender: User模型
        instance: 要删除的用户实例
        **kwargs: 其他参数
    """
    from apps.models.models import ModelProvider
    from apps.prompts.models import PromptTemplateSet

    # 获取第一个可用的 superuser（如果不是当前用户）
    alternative_superuser = (
        User.objects.filter(is_superuser=True).exclude(id=instance.id).order_by("id").first()
    )

    # 处理 ModelProvider
    user_models = ModelProvider.objects.filter(created_by=instance)

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
    user_prompt_sets = PromptTemplateSet.objects.filter(created_by=instance)

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
