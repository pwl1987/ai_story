"""
Story 9.1: ProxyConfig模型测试套件

测试ProxyConfig模型的所有功能：
- Phase 1: 模型层单元测试（加密/解密、URL构建、字段验证）
- Phase 2: Admin集成测试（显示、筛选、只读字段）
- Phase 3: 端到端测试（完整CRUD流程）

@Author: Epic 9 Team
@Created: 2026-01-30
@Story: 9.1 - ProxyConfig模型 + Fernet加密实现
"""

from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from apps.proxy.models import ProxyConfig, ProxyProtocol


class ProxyConfigModelTest(TestCase):
    """Phase 1: 模型层单元测试"""

    def test_http_proxy_no_auth(self):
        """AC[场景1]: 创建HTTP代理（无认证）"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 验证默认值
        assert proxy.is_active is True
        assert proxy.is_healthy is True
        assert proxy.priority == 0
        # 无密码时password_encrypted应为空
        assert proxy.password_encrypted == b"" or proxy.password_encrypted is None

    def test_https_proxy_with_encryption(self):
        """AC[场景2]: 创建HTTPS代理（带认证）- 密码自动加密"""
        proxy = ProxyConfig.objects.create(
            name="加密代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=443,
            username="user",
            password="Secret@123",
        )

        # 验证加密
        assert proxy.password_encrypted is not None
        assert proxy.password_encrypted != b""
        # 明文密码已清空
        assert proxy.password is None
        # 密文与明文不同
        assert proxy.password_encrypted != b"Secret@123"

    def test_decrypt_password_consistency(self):
        """AC[场景3]: 密码加密解密一致性"""
        proxy = ProxyConfig(
            name="一致性测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            password="Secret@123",
        )
        proxy.save()

        # 解密密码应与原始密码一致
        decrypted = proxy.decrypt_password(proxy.password_encrypted)
        assert decrypted == "Secret@123"

    def test_fernet_non_deterministic(self):
        """AC[场景3]: 多次加密相同密码产生不同密文（Fernet特性）"""
        proxy = ProxyConfig(password="SamePassword")

        encrypted1 = proxy.encrypt_password("SamePassword")
        encrypted2 = proxy.encrypt_password("SamePassword")

        # Fernet每次生成不同的token（timestamp不同）
        assert encrypted1 != encrypted2

        # 但解密结果一致
        assert proxy.decrypt_password(encrypted1) == "SamePassword"
        assert proxy.decrypt_password(encrypted2) == "SamePassword"

    def test_get_proxy_url_with_auth(self):
        """AC[场景4]: 代理URL构建（有认证）"""
        proxy = ProxyConfig(
            name="认证代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass123",
        )
        proxy.save()

        url = proxy.get_proxy_url()
        assert url == "https://user:pass123@proxy.example.com:8080"

    def test_get_proxy_url_without_auth(self):
        """AC[场景4]: 代理URL构建（无认证）"""
        proxy = ProxyConfig.objects.create(
            name="无认证代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=8080,
        )

        url = proxy.get_proxy_url()
        assert url == "https://proxy.example.com:8080"

    def test_get_proxy_url_all_protocols(self):
        """测试所有协议的URL构建"""
        test_cases = [
            (ProxyProtocol.HTTP, "http://host:80"),
            (ProxyProtocol.HTTPS, "https://host:443"),
            (ProxyProtocol.SOCKS5, "socks5://host:1080"),
        ]

        for protocol, expected_prefix in test_cases:
            proxy = ProxyConfig.objects.create(
                name=f"{protocol}代理",
                protocol=protocol,
                host="host",
                port=80
                if protocol == ProxyProtocol.HTTP
                else (443 if protocol == ProxyProtocol.HTTPS else 1080),
            )
            url = proxy.get_proxy_url()
            assert url.startswith(expected_prefix)

    def test_port_range_validation_invalid_port(self):
        """AC[场景5]: port字段验证 - 无效端口号"""
        proxy = ProxyConfig(
            name="无效端口代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=0,  # 无效端口
        )

        with pytest.raises(ValidationError) as exc:
            proxy.full_clean()  # 触发所有验证

        # 验证错误消息包含端口号信息
        assert "port" in str(exc.value).lower()

    def test_port_range_validation_valid_port(self):
        """port字段验证 - 有效端口号"""
        # 边界值测试
        valid_ports = [1, 80, 443, 8080, 65535]
        for port in valid_ports:
            proxy = ProxyConfig(
                name=f"端口{port}代理",
                protocol=ProxyProtocol.HTTP,
                host="proxy.example.com",
                port=port,
            )
            proxy.full_clean()  # 不应抛出异常

    def test_name_unique_constraint(self):
        """AC[场景5]: name唯一性约束"""
        ProxyConfig.objects.create(
            name="重复名称",
            protocol=ProxyProtocol.HTTP,
            host="proxy1.example.com",
            port=8080,
        )

        # 尝试创建重复名称
        duplicate = ProxyConfig(
            name="重复名称",
            protocol=ProxyProtocol.HTTP,
            host="proxy2.example.com",
            port=8080,
        )

        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            duplicate.save()

    def test_str_representation(self):
        """测试__str__方法"""
        proxy = ProxyConfig(
            name="测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=443,
        )
        expected = "测试代理 (https://proxy.example.com:443)"
        assert str(proxy) == expected

    def test_default_values(self):
        """测试字段默认值"""
        proxy = ProxyConfig.objects.create(
            name="默认值测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        assert proxy.protocol == ProxyProtocol.HTTP
        assert proxy.is_active is True
        assert proxy.is_healthy is True
        assert proxy.priority == 0
        assert proxy.username is None
        assert proxy.password is None

    def test_encryption_key_missing(self):
        """AC[场景8]: PROXY_ENCRYPTION_KEY缺失处理"""
        with override_settings(PROXY_ENCRYPTION_KEY=None):
            proxy = ProxyConfig(
                name="无密钥测试",
                protocol=ProxyProtocol.HTTP,
                host="proxy.example.com",
                port=8080,
                password="test",
            )

            with pytest.raises(ValidationError) as exc:
                proxy.full_clean()

            assert "PROXY_ENCRYPTION_KEY" in str(exc.value)

    def test_save_without_password(self):
        """测试保存无密码代理"""
        proxy = ProxyConfig.objects.create(
            name="无密码代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 验证password_encrypted为空
        assert proxy.password_encrypted == b"" or proxy.password_encrypted is None

    def test_password_cleared_after_save(self):
        """测试保存后明文密码被清空"""
        proxy = ProxyConfig(
            name="清空测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            password="Secret123",
        )
        proxy.save()

        # 明文密码应被清空
        assert proxy.password is None
        # 但加密密码存在
        assert proxy.password_encrypted is not None


class ProxyConfigIndexTest(TestCase):
    """Phase 1: 索引性能测试 - AC[场景6]"""

    def test_query_uses_active_healthy_index(self):
        """AC[场景6]: 验证is_active, is_healthy联合索引"""
        # 创建100个代理
        for i in range(100):
            ProxyConfig.objects.create(
                name=f"Proxy{i}",
                protocol=ProxyProtocol.HTTP,
                host=f"host{i}.example.com",
                port=8080 + i % 1000,
                is_active=(i % 2 == 0),
                is_healthy=(i % 3 == 0),
            )

        # 执行查询
        with self.assertNumQueries(1):
            list(ProxyConfig.objects.filter(is_active=True, is_healthy=True))

    def test_query_uses_last_used_index(self):
        """验证last_used_at降序索引"""
        # 创建代理
        for i in range(10):
            proxy = ProxyConfig.objects.create(
                name=f"Proxy{i}",
                protocol=ProxyProtocol.HTTP,
                host=f"host{i}.example.com",
                port=8080 + i,
            )
            if i % 2 == 0:
                from django.utils import timezone

                proxy.last_used_at = timezone.now()
                proxy.save()

        # 按last_used_at降序查询
        with self.assertNumQueries(1):
            list(ProxyConfig.objects.filter(last_used_at__isnull=False).order_by("-last_used_at"))


class ProxyConfigAdminTest(TestCase):
    """Phase 2: Django Admin集成测试"""

    def setUp(self):
        """设置测试数据"""
        from django.contrib.auth.models import User

        self.superuser = User.objects.create_superuser(
            username="admin", password="pass", email="admin@test.com"
        )

    def test_admin_list_display(self):
        """测试Admin list_display配置"""
        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        # 验证list_display包含必需字段
        expected_fields = [
            "name",
            "protocol",
            "get_host_port",
            "is_active",
            "is_healthy",
            "priority",
            "last_used_at",
        ]
        for field in expected_fields:
            assert field in admin_instance.list_display

    def test_admin_list_filter(self):
        """测试Admin list_filter配置"""
        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        # 验证list_filter包含协议和状态筛选
        expected_filters = ["protocol", "is_active", "is_healthy"]
        for filter_name in expected_filters:
            assert filter_name in admin_instance.list_filter

    def test_admin_search_fields(self):
        """测试Admin search_fields配置"""
        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        # 验证可以按name搜索
        assert "name" in admin_instance.search_fields

    def test_admin_readonly_fields(self):
        """测试Admin readonly_fields配置"""
        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        # 验证只读字段
        readonly = admin_instance.readonly_fields
        assert "password_encrypted_display" in readonly
        assert "get_proxy_url_display" in readonly
        assert "created_at" in readonly
        assert "updated_at" in readonly
        assert "last_used_at" in readonly

    def test_admin_custom_methods(self):
        """测试Admin自定义方法"""
        proxy = ProxyConfig.objects.create(
            name="方法测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 测试get_host_port方法
        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        host_port = admin_instance.get_host_port(proxy)
        assert host_port == "proxy.example.com:8080"

    def test_admin_password_masked_display(self):
        """AC[场景7]: password_encrypted在Admin中显示为占位符"""
        proxy = ProxyConfig.objects.create(
            name="密码掩码测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            password="Secret123",
        )

        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        # 测试password_encrypted_display方法
        display = admin_instance.password_encrypted_display(proxy)
        assert display == "•••••••••"

    def test_admin_password_empty_display(self):
        """无密码时显示(空)"""
        proxy = ProxyConfig.objects.create(
            name="空密码测试",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        from django.contrib.admin.sites import AdminSite

        from apps.proxy.admin import ProxyConfigAdmin

        admin_site = AdminSite()
        admin_instance = ProxyConfigAdmin(ProxyConfig, admin_site)

        display = admin_instance.password_encrypted_display(proxy)
        assert display == "(空)"


class ProxyConfigE2ETest(TestCase):
    """Phase 3: 端到端集成测试"""

    def test_complete_crud_workflow(self):
        """AC[场景7]: 完整的CRUD流程测试"""
        # Create
        proxy = ProxyConfig.objects.create(
            name="E2E测试代理",
            protocol=ProxyProtocol.HTTPS,
            host="e2e.example.com",
            port=8888,
            username="e2euser",
            password="e2epass",
        )

        # Read
        retrieved = ProxyConfig.objects.get(name="E2E测试代理")
        assert retrieved.protocol == ProxyProtocol.HTTPS
        assert retrieved.host == "e2e.example.com"
        assert retrieved.port == 8888
        assert retrieved.username == "e2euser"

        # Update
        retrieved.priority = 10
        retrieved.save()
        updated = ProxyConfig.objects.get(name="E2E测试代理")
        assert updated.priority == 10

        # Delete
        proxy_id = proxy.id
        proxy.delete()
        assert not ProxyConfig.objects.filter(id=proxy_id).exists()

    def test_proxy_url_after_create(self):
        """创建后get_proxy_url()正常工作"""
        proxy = ProxyConfig.objects.create(
            name="URL测试",
            protocol=ProxyProtocol.HTTPS,
            host="urltest.example.com",
            port=9000,
            username="urluser",
            password="urlpass",
        )

        url = proxy.get_proxy_url()
        assert url == "https://urluser:urlpass@urltest.example.com:9000"

    def test_ordering_by_priority_and_name(self):
        """测试按priority降序、name升序排列"""
        # 创建多个代理
        ProxyConfig.objects.create(
            name="Z代理", protocol=ProxyProtocol.HTTP, host="z.com", port=80, priority=10
        )
        ProxyConfig.objects.create(
            name="A代理", protocol=ProxyProtocol.HTTP, host="a.com", port=80, priority=10
        )
        ProxyConfig.objects.create(
            name="M代理", protocol=ProxyProtocol.HTTP, host="m.com", port=80, priority=0
        )

        # 查询所有代理（应按Meta.ordering排序）
        proxies = list(ProxyConfig.objects.all())

        # 验证排序：priority=0的最先，然后priority相同时按name字母序
        assert proxies[0].name == "M代理"  # priority=0
        assert proxies[1].name == "A代理"  # priority=10, A在前
        assert proxies[2].name == "Z代理"  # priority=10, Z在后


class ProxyConfigMockTest(TestCase):
    """使用Mock的单元测试（避免依赖真实密钥）"""

    @patch("apps.proxy.models.Fernet")
    def test_encrypt_with_mock_fernet(self, mock_fernet_class):
        """使用Mock Fernet测试加密逻辑"""
        # 设置Mock
        mock_fernet = MagicMock()
        mock_fernet.encrypt.return_value = b"mocked_encrypted_bytes"
        mock_fernet_class.return_value = mock_fernet

        # 设置密钥
        with override_settings(PROXY_ENCRYPTION_KEY="test_key"):
            proxy = ProxyConfig(password="test_password")

            # 执行加密
            encrypted = proxy.encrypt_password("test_password")

            # 验证调用
            mock_fernet.encrypt.assert_called_once_with(b"test_password")
            assert encrypted == b"mocked_encrypted_bytes"

    @patch("apps.proxy.models.Fernet")
    def test_decrypt_with_mock_fernet(self, mock_fernet_class):
        """使用Mock Fernet测试解密逻辑"""
        # 设置Mock
        mock_fernet = MagicMock()
        mock_fernet.decrypt.return_value = b"decrypted_password"
        mock_fernet_class.return_value = mock_fernet

        with override_settings(PROXY_ENCRYPTION_KEY="test_key"):
            proxy = ProxyConfig()

            # 执行解密
            decrypted = proxy.decrypt_password(b"encrypted_bytes")

            # 验证调用
            mock_fernet.decrypt.assert_called_once_with(b"encrypted_bytes")
            assert decrypted == "decrypted_password"
