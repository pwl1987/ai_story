"""
Story 9.2: ProxyUsageLog模型测试套件

测试ProxyUsageLog模型的所有功能：
- Phase 1: 模型层单元测试（字段、索引、时间戳）
- Phase 2: Admin集成测试（权限、显示、批量操作）
- Phase 3: 端到端测试（完整流程）

@Author: Epic 9 Team
@Created: 2026-01-30
@Story: 9.2 - ProxyUsageLog模型 + Admin界面
"""

import random
from unittest.mock import MagicMock

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.proxy.models import ProxyConfig, ProxyProtocol, ProxyUsageLog


class ProxyUsageLogModelTest(TestCase):
    """Phase 1: 模型层单元测试"""

    def test_log_creation_with_all_fields(self):
        """AC[场景1]: 日志创建时所有字段正确保存"""
        # 创建代理
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 创建日志
        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )

        # 验证所有字段
        assert log.proxy == proxy
        assert log.ai_provider == "OpenAIClient"
        assert log.endpoint == "/v1/chat/completions"
        assert log.response_time_ms == 150
        assert log.success is True
        assert log.error_message is None

    def test_log_creation_with_error(self):
        """AC[场景7]: 失败日志记录错误信息"""
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            response_time_ms=30000,
            success=False,
            error_message="Connection timeout after 30s",
        )

        assert log.success is False
        assert log.response_time_ms == 30000
        assert "Connection timeout" in log.error_message

    def test_timestamp_auto_set(self):
        """AC[场景2]: timestamp字段自动设置为当前时间"""
        from django.utils.timezone import now

        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        before_creation = now()
        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/completions",
            response_time_ms=100,
            success=True,
        )
        after_creation = now()

        # 验证timestamp已自动设置且在合理范围内
        assert log.timestamp is not None
        assert before_creation <= log.timestamp <= after_creation

    def test_str_representation(self):
        """测试__str__方法"""
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )

        # 验证字符串表示
        str_repr = str(log)
        assert "测试代理" in str_repr
        assert "OpenAIClient" in str_repr

    def test_foreign_key_cascade_delete(self):
        """测试外键级联删除"""
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建多条日志
        ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )
        ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            response_time_ms=200,
            success=True,
        )

        # 验证日志数量
        assert ProxyUsageLog.objects.count() == 2

        # 删除代理
        proxy.delete()

        # 验证日志被级联删除
        assert ProxyUsageLog.objects.count() == 0

    def test_default_success_value(self):
        """测试success字段默认值为True"""
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
        )

        # 验证默认值
        assert log.success is True

    def test_related_name_usage_logs(self):
        """测试related_name='usage_logs'"""
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 通过related_name创建日志
        log1 = proxy.usage_logs.create(
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )
        log2 = proxy.usage_logs.create(
            ai_provider="ClaudeClient", endpoint="/v1/messages", response_time_ms=200, success=True
        )

        # 验证可以通过related_name查询
        assert proxy.usage_logs.count() == 2
        assert log1 in proxy.usage_logs.all()
        assert log2 in proxy.usage_logs.all()


class ProxyUsageLogIndexTest(TestCase):
    """Phase 1: 索引性能测试 - AC[场景6]"""

    def test_index_proxy_timestamp(self):
        """AC[场景6]: 验证proxy, -timestamp联合索引"""
        # 创建代理
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建100条日志
        for i in range(100):
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider=random.choice(["OpenAIClient", "ClaudeClient"]),
                endpoint=f"/endpoint/{i}",
                response_time_ms=random.randint(50, 500),
                success=random.choice([True, False]),
            )

        # 执行查询并验证使用索引
        with CaptureQueriesContext(connection) as context:
            list(ProxyUsageLog.objects.filter(proxy=proxy).order_by("-timestamp"))

        # 验证查询数量（应该只有1条查询）
        assert len(context.captured_queries) == 1

        # 验证SQL包含索引提示（SQLite不显示索引名称，但查询应该有效）
        query = context.captured_queries[0]["sql"]
        assert "proxy_usage_log" in query.lower()

    def test_index_ai_provider_success(self):
        """验证ai_provider, success, -timestamp联合索引"""
        # 创建代理
        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建100条日志
        for i in range(100):
            ProxyUsageLog.objects.create(
                proxy=proxy,
                ai_provider=random.choice(["OpenAIClient", "ClaudeClient"]),
                endpoint=f"/endpoint/{i}",
                response_time_ms=random.randint(50, 500),
                success=random.choice([True, False]),
            )

        # 执行查询并验证使用索引
        with CaptureQueriesContext(connection) as context:
            list(
                ProxyUsageLog.objects.filter(ai_provider="OpenAIClient", success=False).order_by(
                    "-timestamp"
                )
            )

        # 验证查询数量
        assert len(context.captured_queries) == 1

        # 验证SQL包含相关字段
        query = context.captured_queries[0]["sql"]
        assert "ai_provider" in query.lower()
        assert "success" in query.lower()


class ProxyUsageLogAdminTest(TestCase):
    """Phase 2: Django Admin集成测试"""

    def setUp(self):
        """设置测试数据"""
        self.superuser = User.objects.create_superuser(
            username="admin", password="pass", email="admin@test.com"
        )
        self.normal_user = User.objects.create_user(
            username="normal", password="pass", email="normal@test.com"
        )

    def test_admin_list_display(self):
        """AC[场景3]: 测试Admin list_display配置"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证list_display包含必需字段
        expected_fields = [
            "proxy_name",
            "ai_provider",
            "endpoint",
            "response_time_ms_formatted",
            "success_icon",
            "timestamp_formatted",
        ]
        for field in expected_fields:
            assert field in admin_instance.list_display

    def test_admin_list_filter(self):
        """测试Admin list_filter配置"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证list_filter包含必需筛选器
        expected_filters = ["proxy", "ai_provider", "success", "timestamp"]
        for filter_name in expected_filters:
            assert filter_name in admin_instance.list_filter

    def test_admin_search_fields(self):
        """测试Admin search_fields配置"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证可以按endpoint和error_message搜索
        assert "endpoint" in admin_instance.search_fields
        assert "error_message" in admin_instance.search_fields

    def test_admin_readonly_fields(self):
        """测试Admin readonly_fields配置"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证所有字段都是只读
        readonly = admin_instance.readonly_fields
        assert "proxy" in readonly
        assert "ai_provider" in readonly
        assert "endpoint" in readonly
        assert "response_time_ms" in readonly
        assert "success" in readonly
        assert "error_message" in readonly
        assert "timestamp" in readonly

    def test_admin_permissions_no_add(self):
        """AC[场景5]: 测试has_add_permission返回False"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证禁止添加
        assert admin_instance.has_add_permission(MagicMock()) is False

    def test_admin_permissions_no_change(self):
        """AC[场景5]: 测试has_change_permission返回False"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证禁止修改
        assert admin_instance.has_change_permission(MagicMock()) is False

    def test_admin_permissions_delete_only_superuser(self):
        """AC[场景5]: 测试has_delete_permission仅超级用户可删除"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 创建Mock请求对象（普通用户）
        normal_request = MagicMock()
        normal_request.user.is_superuser = False

        # 创建Mock请求对象（超级用户）
        super_request = MagicMock()
        super_request.user.is_superuser = True

        # 验证普通用户不能删除
        assert admin_instance.has_delete_permission(normal_request) is False

        # 验证超级用户可以删除
        assert admin_instance.has_delete_permission(super_request) is True

    def test_admin_custom_methods(self):
        """AC[场景3]: 测试Admin自定义方法"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 测试proxy_name方法
        assert admin_instance.proxy_name(log) == "测试代理"

        # 测试response_time_ms_formatted方法
        assert admin_instance.response_time_ms_formatted(log) == "150 ms"

        # 测试success_icon方法（成功）
        success_html = admin_instance.success_icon(log)
        assert "✅" in success_html
        assert "green" in success_html

        # 测试timestamp_formatted方法
        timestamp_str = admin_instance.timestamp_formatted(log)
        assert "-" in timestamp_str  # 包含日期分隔符
        assert ":" in timestamp_str  # 包含时间分隔符

    def test_admin_success_icon_failure(self):
        """测试失败状态的图标"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=30000,
            success=False,
            error_message="Connection timeout",
        )

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 测试失败图标
        failure_html = admin_instance.success_icon(log)
        assert "❌" in failure_html
        assert "red" in failure_html

    def test_admin_actions_export_csv(self):
        """AC[场景8]: 测试export_as_csv批量操作"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        proxy = ProxyConfig.objects.create(
            name="测试代理", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        log1 = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )
        log2 = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            response_time_ms=200,
            success=False,
            error_message="Timeout",
        )

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 创建Mock请求
        request = MagicMock()

        # 创建queryset
        queryset = ProxyUsageLog.objects.filter(id__in=[log1.id, log2.id])

        # 执行导出
        response = admin_instance.export_as_csv(request, queryset)

        # 验证响应
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"
        assert "proxy_logs.csv" in response["Content-Disposition"]

        # 验证CSV内容
        content = response.content.decode("utf-8")
        assert "代理" in content  # CSV表头
        assert "测试代理" in content  # 数据
        assert "OpenAIClient" in content
        assert "ClaudeClient" in content

    def test_admin_actions_list(self):
        """验证批量操作列表"""
        from apps.proxy.admin import ProxyUsageLogAdmin

        admin_site = AdminSite()
        admin_instance = ProxyUsageLogAdmin(ProxyUsageLog, admin_site)

        # 验证export_as_csv在actions列表中
        assert "export_as_csv" in admin_instance.actions


class ProxyUsageLogE2ETest(TestCase):
    """Phase 3: 端到端集成测试"""

    def test_complete_log_workflow(self):
        """AC[场景1]: 完整的日志记录流程"""
        # 1. 创建代理
        proxy = ProxyConfig.objects.create(
            name="E2E测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="e2e.example.com",
            port=8888,
            username="e2euser",
            password="e2epass",
        )

        # 2. 创建成功日志
        success_log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=120,
            success=True,
        )

        # 3. 创建失败日志
        failure_log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            response_time_ms=5000,
            success=False,
            error_message="Rate limit exceeded",
        )

        # 4. 验证可以通过代理查询日志
        logs = proxy.usage_logs.all()
        assert logs.count() == 2
        assert success_log in logs
        assert failure_log in logs

        # 5. 验证排序（按timestamp降序）
        ordered_logs = list(ProxyUsageLog.objects.filter(proxy=proxy))
        assert ordered_logs[0] == failure_log  # 最新的在前

    def test_filter_by_ai_provider_and_success(self):
        """AC[场景4]: 测试按AI提供商和成功状态筛选"""
        proxy = ProxyConfig.objects.create(
            name="筛选测试", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建多条日志
        ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=150,
            success=True,
        )
        ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/completions",
            response_time_ms=200,
            success=False,
        )
        ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="ClaudeClient",
            endpoint="/v1/messages",
            response_time_ms=100,
            success=True,
        )

        # 筛选OpenAI成功日志
        openai_success = ProxyUsageLog.objects.filter(ai_provider="OpenAIClient", success=True)
        assert openai_success.count() == 1
        assert openai_success.first().endpoint == "/v1/chat/completions"

        # 筛选失败日志
        failed_logs = ProxyUsageLog.objects.filter(success=False)
        assert failed_logs.count() == 1
        assert failed_logs.first().ai_provider == "OpenAIClient"

    def test_bulk_create_logs(self):
        """测试批量创建日志（性能测试）"""
        proxy = ProxyConfig.objects.create(
            name="批量测试", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 批量创建1000条日志
        logs = [
            ProxyUsageLog(
                proxy=proxy,
                ai_provider=random.choice(["OpenAIClient", "ClaudeClient", "GeminiClient"]),
                endpoint=f"/endpoint/{i}",
                response_time_ms=random.randint(50, 500),
                success=random.choice([True, False]),
            )
            for i in range(1000)
        ]

        # bulk_create
        ProxyUsageLog.objects.bulk_create(logs, batch_size=100)

        # 验证创建成功
        assert ProxyUsageLog.objects.count() == 1000

        # 验证可以通过外键查询
        assert proxy.usage_logs.count() == 1000

    def test_ordering_by_timestamp(self):
        """测试默认排序（timestamp降序）"""
        proxy = ProxyConfig.objects.create(
            name="排序测试", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建多条日志（自动按时间顺序）
        log1 = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/1",
            response_time_ms=100,
            success=True,
        )
        log2 = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/2",
            response_time_ms=150,
            success=True,
        )
        log3 = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/3",
            response_time_ms=200,
            success=True,
        )

        # 查询所有日志（应按timestamp降序）
        logs = list(ProxyUsageLog.objects.all())

        # 验证排序（最新的在前）
        assert logs[0] == log3
        assert logs[1] == log2
        assert logs[2] == log1

    def test_long_error_message(self):
        """测试长错误消息（TextField）"""
        proxy = ProxyConfig.objects.create(
            name="错误测试", protocol=ProxyProtocol.HTTP, host="proxy.example.com", port=8080
        )

        # 创建超长错误消息（模拟异常堆栈）
        long_error = "\n".join([f"Error line {i}" for i in range(100)])

        log = ProxyUsageLog.objects.create(
            proxy=proxy,
            ai_provider="OpenAIClient",
            endpoint="/v1/chat/completions",
            response_time_ms=5000,
            success=False,
            error_message=long_error,
        )

        # 验证长错误消息正确保存
        assert log.error_message == long_error
        assert len(log.error_message) > 1000
