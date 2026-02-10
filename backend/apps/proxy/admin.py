"""
Django Admin配置 - 代理管理模块

Story 9.1: ProxyConfig Admin界面
- 列表显示：name, protocol, get_host_port, is_active, is_healthy, priority, last_used_at
- 筛选器：protocol, is_active, is_healthy
- 搜索：name
- 只读字段：password_encrypted, created_at, updated_at, last_used_at
- 密码字段显示为占位符"•••••••••"

Story 9.2: ProxyUsageLog Admin界面
- 列表显示：proxy_name, ai_provider, endpoint, response_time_ms_formatted, success_icon, timestamp_formatted
- 筛选器：proxy, ai_provider, success, timestamp
- 搜索：endpoint, error_message
- 只读模式：禁止添加、修改、删除（仅超级用户可删除）
- 批量操作：导出为CSV

Story 9.9: 测试连接功能
- Admin Action: test_connection
- 测试代理连接到 https://httpbin.org/ip
- 记录 ProxyUsageLog
- 显示成功/失败消息

@Author: Epic 9 Team
@Created: 2026-01-30
"""

import csv
import time

import httpx
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html

from .models import ProxyConfig, ProxyUsageLog


@admin.register(ProxyConfig)
class ProxyConfigAdmin(admin.ModelAdmin):
    """
    ProxyConfig Django Admin配置

    功能：
    - 列表显示7个关键字段
    - 支持按protocol, is_active, is_healthy筛选
    - 支持按name搜索
    - password_encrypted只读且显示为占位符
    - 按priority降序、name升序排列
    - 测试连接功能（Story 9.9）
    """

    # Admin Actions（批量操作）
    actions = ["test_connection"]

    # 列表页显示字段
    list_display = [
        "name",
        "protocol",
        "get_host_port",
        "is_active",
        "is_healthy",
        "priority",
        "last_used_at",
    ]

    # 列表筛选器
    list_filter = [
        "protocol",
        "is_active",
        "is_healthy",
    ]

    # 搜索字段
    search_fields = [
        "name",
    ]

    # 只读字段（防止手动修改）
    readonly_fields = [
        "password_encrypted_display",
        "get_proxy_url_display",
        "created_at",
        "updated_at",
        "last_used_at",
    ]

    # 字段集（编辑页布局）
    fieldsets = (
        ("基本配置", {"fields": ("name", "protocol", "host", "port")}),
        (
            "认证信息",
            {
                "fields": ("username", "password"),
                "description": "密码保存后会自动加密存储，明文密码不会被保存",
            },
        ),
        ("状态", {"fields": ("is_active", "is_healthy", "priority")}),
        (
            "只读信息",
            {
                "fields": (
                    "password_encrypted_display",
                    "get_proxy_url_display",
                    "last_used_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    # 排序
    ordering = ["priority", "name"]

    def get_host_port(self, obj):
        """返回代理地址（host:port格式）"""
        return f"{obj.host}:{obj.port}"

    get_host_port.short_description = "代理地址"
    get_host_port.admin_order_field = "host"

    def password_encrypted_display(self, obj):
        """
        显示加密密码（占位符格式）

        Returns:
            "•••••••••" 如果有加密密码
            "(空)" 如果没有加密密码
        """
        if obj.password_encrypted:
            return "•••••••••"
        return "(空)"

    password_encrypted_display.short_description = "加密密码"

    def get_proxy_url_display(self, obj):
        """
        显示代理URL（用于复制）

        Returns:
            代理URL字符串（已解密密码）
        """
        try:
            return obj.get_proxy_url()
        except Exception as e:
            return f"(错误: {e!s})"

    get_proxy_url_display.short_description = "代理URL"

    @admin.action(description="测试连接")
    def test_connection(self, request, queryset):
        """
        测试代理连接 - Story 9.9

        测试流程：
        1. 检查代理是否启用（is_active）
        2. 通过代理访问 https://httpbin.org/ip
        3. 记录测试结果到 ProxyUsageLog
        4. 显示成功/失败消息

        Args:
            request: Django HttpRequest
            queryset: 选中的ProxyConfig对象集合

        Returns:
            None（使用messages框架显示消息）
        """
        success_count = 0
        failure_count = 0

        for proxy in queryset:
            # AC[场景4]: 代理未启用时立即返回错误
            if not proxy.is_active:
                messages.error(request, f"✗ {proxy.name}：代理未启用，无法测试")
                failure_count += 1
                continue

            # 测试连接
            start_time = time.time()
            try:
                # 获取代理URL
                proxy_url = proxy.get_proxy_url()

                # 发送测试请求（AC[场景2]）
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(
                        "https://httpbin.org/ip",
                        proxies={"all://": proxy_url},
                    )
                    response.raise_for_status()

                # 计算响应时间
                response_time_ms = int((time.time() - start_time) * 1000)

                # 解析响应
                result = response.json()
                origin_ip = result.get("origin", "")

                # AC[场景5]: 显示响应时间
                messages.success(
                    request,
                    f"✓ {proxy.name}：连接成功！代理IP: {origin_ip}，响应时间: {response_time_ms}ms",
                )

                # 更新代理健康状态
                proxy.is_healthy = True
                proxy.save(update_fields=["is_healthy"])

                # AC[场景8]: 记录ProxyUsageLog
                ProxyUsageLog.objects.create(
                    proxy=proxy,
                    ai_provider="system",
                    endpoint="https://httpbin.org/ip",
                    response_time_ms=response_time_ms,
                    success=True,
                )

                success_count += 1

            except httpx.TimeoutException:
                # AC[场景3]: 连接超时
                messages.error(request, f"✗ {proxy.name}：连接失败：Connection timeout")
                failure_count += 1

                # 更新代理健康状态
                proxy.is_healthy = False
                proxy.save(update_fields=["is_healthy"])

                # 记录失败的日志
                ProxyUsageLog.objects.create(
                    proxy=proxy,
                    ai_provider="system",
                    endpoint="https://httpbin.org/ip",
                    response_time_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message="Connection timeout",
                )

            except httpx.HTTPStatusError as e:
                # HTTP错误
                messages.error(
                    request, f"✗ {proxy.name}：连接失败：HTTP error {e.response.status_code}"
                )
                failure_count += 1

                # 更新代理健康状态
                proxy.is_healthy = False
                proxy.save(update_fields=["is_healthy"])

                # 记录失败的日志
                ProxyUsageLog.objects.create(
                    proxy=proxy,
                    ai_provider="system",
                    endpoint="https://httpbin.org/ip",
                    response_time_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=f"HTTP error {e.response.status_code}",
                )

            except Exception as e:
                # 其他错误
                messages.error(request, f"✗ {proxy.name}：连接失败：{e!s}")
                failure_count += 1

                # 更新代理健康状态
                proxy.is_healthy = False
                proxy.save(update_fields=["is_healthy"])

                # 记录失败的日志
                ProxyUsageLog.objects.create(
                    proxy=proxy,
                    ai_provider="system",
                    endpoint="https://httpbin.org/ip",
                    response_time_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=str(e),
                )

        # AC[场景6]: 显示汇总结果
        if queryset.count() > 1:
            messages.info(request, f"测试完成：成功 {success_count} 个，失败 {failure_count} 个")


@admin.register(ProxyUsageLog)
class ProxyUsageLogAdmin(admin.ModelAdmin):
    """
    ProxyUsageLog Django Admin配置

    功能：
    - 列表显示6个字段（包含自定义格式化显示）
    - 支持按proxy, ai_provider, success, timestamp筛选
    - 支持按endpoint, error_message搜索
    - 只读模式（禁止添加、修改、删除）
    - 批量操作：导出为CSV（仅超级用户可删除）
    """

    # 列表页显示字段（使用自定义方法格式化）
    list_display = [
        "proxy_name",
        "ai_provider",
        "endpoint",
        "response_time_ms_formatted",
        "success_icon",
        "timestamp_formatted",
    ]

    # 列表筛选器
    list_filter = [
        "proxy",
        "ai_provider",
        "success",
        "timestamp",
    ]

    # 搜索字段
    search_fields = [
        "endpoint",
        "error_message",
    ]

    # 只读字段（所有字段都只读）
    readonly_fields = [
        "proxy",
        "ai_provider",
        "endpoint",
        "response_time_ms",
        "success",
        "error_message",
        "timestamp",
    ]

    # 每页显示数量（默认50条）
    list_per_page = 50

    # 排序
    ordering = ["-timestamp"]

    # 批量操作
    actions = ["export_as_csv"]

    def has_add_permission(self, request):
        """禁止添加日志记录"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改日志记录"""
        return False

    def has_delete_permission(self, request, obj=None):
        """仅超级用户可删除日志记录"""
        return request.user.is_superuser

    def proxy_name(self, obj):
        """显示代理名称（通过外键关联）"""
        return obj.proxy.name

    proxy_name.short_description = "代理名称"
    proxy_name.admin_order_field = "proxy"

    def response_time_ms_formatted(self, obj):
        """格式化显示响应时间"""
        return f"{obj.response_time_ms} ms"

    response_time_ms_formatted.short_description = "响应时间"
    response_time_ms_formatted.admin_order_field = "response_time_ms"

    def success_icon(self, obj):
        """显示成功/失败图标"""
        if obj.success:
            return format_html('<span style="color:green">✅</span>')
        return format_html('<span style="color:red">❌</span>')

    success_icon.short_description = "状态"
    success_icon.admin_order_field = "success"

    def timestamp_formatted(self, obj):
        """格式化显示时间戳"""
        if obj.timestamp:
            return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return "-"

    timestamp_formatted.short_description = "时间"
    timestamp_formatted.admin_order_field = "timestamp"

    def export_as_csv(self, request, queryset):
        """
        批量导出日志为CSV

        Args:
            request: Django HTTP请求对象
            queryset: 选中的日志记录

        Returns:
            CSV文件响应
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="proxy_logs.csv"'

        writer = csv.writer(response)
        # 写入表头
        writer.writerow(
            [
                "代理",
                "AI提供商",
                "端点",
                "响应时间(ms)",
                "成功",
                "错误信息",
                "时间",
            ]
        )

        # 写入数据行
        for log in queryset:
            writer.writerow(
                [
                    log.proxy.name,
                    log.ai_provider,
                    log.endpoint,
                    log.response_time_ms,
                    "成功" if log.success else "失败",
                    log.error_message or "",
                    log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                ]
            )

        return response

    export_as_csv.short_description = "导出选中的日志为CSV"
