"""
Admin Mixins - 可复用的Admin功能

Epic 8 Story 8.11: 系统资源视觉标记
"""

from django.utils.html import format_html


class SystemResourceBadgeMixin:
    """
    系统资源视觉标记Mixin

    Epic 8 Story 8.11: 系统资源视觉标记

    功能:
    - 为系统资源（is_system_default=True）显示金色星标
    - 为用户资源显示灰色用户图标
    - 统一的视觉样式

    使用方法:
    class MyModelAdmin(SystemResourceBadgeMixin, admin.ModelAdmin):
        list_display = ["system_resource_badge", "name", ...]
    """

    def system_resource_badge(self, obj):
        """
        显示系统资源标记

        Epic 8 Story 8.11: 系统资源视觉标记

        Args:
            obj: 模型实例

        Returns:
            str: HTML格式的标记
        """
        if obj.is_system_default:
            return format_html('<span style="color: #D4AF37; font-weight: bold;">🌟 系统级</span>')
        return format_html('<span style="color: #808080;">👤 用户级</span>')

    system_resource_badge.short_description = "资源类型"
