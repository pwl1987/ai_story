"""模型管理Admin配置"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import ModelProvider, ModelUsageLog


class ModelProviderAdminForm(forms.ModelForm):
    """ModelProvider自定义表单，用于验证executor_class"""

    class Meta:
        model = ModelProvider
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 如果实例存在且有provider_type，动态设置executor_class的choices
        if self.instance and self.instance.provider_type:
            executor_choices = self.instance.get_executor_choices()
            if executor_choices:
                self.fields["executor_class"].widget = forms.Select(
                    choices=[("", "--- 请选择执行器 ---"), *executor_choices]
                )

    def clean_executor_class(self):
        """验证executor_class是否有效"""
        executor_class = self.cleaned_data.get("executor_class")
        provider_type = self.cleaned_data.get("provider_type")

        if not executor_class:
            # 如果未填写，使用默认执行器
            if self.instance:
                temp_instance = ModelProvider(provider_type=provider_type)
                executor_class = temp_instance.get_default_executor()
                return executor_class
            return executor_class

        # 验证执行器是否在允许的选项中
        if self.instance:
            temp_instance = ModelProvider(provider_type=provider_type)
            valid_executors = [choice[0] for choice in temp_instance.get_executor_choices()]

            if executor_class not in valid_executors:
                raise ValidationError(f'执行器 "{executor_class}" 不适用于类型 "{provider_type}"')

        return executor_class


@admin.register(ModelProvider)
class ModelProviderAdmin(admin.ModelAdmin):
    form = ModelProviderAdminForm
    list_display = [
        "name",
        "provider_type",
        "executor_class",
        "is_active",
        "priority",
        "created_at",
    ]
    list_filter = ["provider_type", "is_active"]
    search_fields = ["name", "model_name", "executor_class"]

    fieldsets = (
        ("基本信息", {"fields": ("name", "provider_type", "is_active", "priority")}),
        ("API配置", {"fields": ("api_url", "api_key", "model_name", "timeout")}),
        (
            "执行器配置",
            {
                "fields": ("executor_class",),
                "description": "选择该模型使用的执行器类。如果不选择，将使用默认执行器。",
            },
        ),
        (
            "LLM参数",
            {
                "fields": ("max_tokens", "temperature", "top_p"),
                "classes": ("collapse",),
                "description": "仅适用于LLM类型的模型",
            },
        ),
        ("限流配置", {"fields": ("rate_limit_rpm", "rate_limit_rpd"), "classes": ("collapse",)}),
        (
            "额外配置",
            {
                "fields": ("extra_config",),
                "classes": ("collapse",),
                "description": "JSON格式的额外配置参数",
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """保存前自动设置默认执行器"""
        if not obj.executor_class:
            obj.executor_class = obj.get_default_executor()
        super().save_model(request, obj, form, change)


@admin.register(ModelUsageLog)
class ModelUsageLogAdmin(admin.ModelAdmin):
    list_display = ["model_provider", "status", "tokens_used", "latency_ms", "created_at"]
    list_filter = ["status", "created_at"]
    readonly_fields = ["created_at"]
