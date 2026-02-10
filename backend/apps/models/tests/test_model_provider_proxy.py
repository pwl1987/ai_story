"""
Epic 9 Story 9.13: ModelProvider 代理集成测试

测试 ModelProvider 与 ProxyConfig 的集成功能
"""

import pytest

from apps.models.models import ModelProvider
from apps.proxy.models import ProxyConfig, ProxyProtocol


@pytest.mark.django_db
class TestModelProviderProxyIntegration:
    """ModelProvider 代理集成单元测试"""

    def test_proxy_fields_exist(self):
        """测试代理字段是否存在"""
        # 检查 ModelProvider 是否有代理相关字段
        provider = ModelProvider()
        assert hasattr(provider, "proxy_config")
        assert hasattr(provider, "use_proxy")

    def test_default_proxy_disabled(self):
        """测试默认不启用代理"""
        provider = ModelProvider(
            name="测试模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
        )
        assert provider.use_proxy is False
        assert provider.proxy_config is None

    def test_get_proxy_url_without_proxy(self):
        """测试未启用代理时返回 None"""
        provider = ModelProvider(
            name="测试模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
            use_proxy=False,
        )
        assert provider.get_proxy_url() is None

    def test_get_proxy_url_with_inactive_proxy(self):
        """测试代理未激活时返回 None"""
        # 创建未激活的代理
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="127.0.0.1",
            port=8080,
            is_active=False,
        )

        # 创建启用代理但代理未激活的模型
        provider = ModelProvider(
            name="测试模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
            use_proxy=True,
            proxy_config=proxy,
        )
        assert provider.get_proxy_url() is None

    def test_get_proxy_url_with_active_proxy(self):
        """测试代理激活时返回 URL"""
        # 创建激活的代理
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="127.0.0.1",
            port=8080,
            is_active=True,
        )

        # 创建启用代理且代理激活的模型
        provider = ModelProvider(
            name="测试模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
            use_proxy=True,
            proxy_config=proxy,
        )
        proxy_url = provider.get_proxy_url()
        assert proxy_url is not None
        assert "127.0.0.1:8080" in proxy_url

    def test_proxy_set_null_on_delete(self):
        """测试代理删除时模型不受影响（SET_NULL）"""
        # 创建代理
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="127.0.0.1",
            port=8080,
            is_active=True,
        )

        # 创建使用代理的模型
        provider = ModelProvider.objects.create(
            name="测试模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
            use_proxy=True,
            proxy_config=proxy,
        )

        # 删除代理
        proxy.delete()

        # 重新加载模型
        provider.refresh_from_db()

        # 验证 proxy_config 设为 NULL，但模型仍存在
        assert provider.proxy_config is None
        assert provider.name == "测试模型"

    def test_backward_compatibility(self):
        """测试向后兼容性：现有模型不受影响"""
        # 创建没有代理的现有模型
        provider = ModelProvider.objects.create(
            name="现有模型",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test_key",
            model_name="gpt-4",
        )

        # 验证字段默认值正确
        assert provider.use_proxy is False
        assert provider.proxy_config is None
        assert provider.get_proxy_url() is None


@pytest.mark.django_db
class TestModelProviderAdminProxyValidation:
    """ModelProvider Admin 表单验证测试"""

    def test_form_validation_proxy_required_when_enabled(self):
        """测试启用代理时必须选择代理配置"""
        from apps.models.admin import ModelProviderAdminForm

        # 创建表单数据（启用代理但未选择代理）
        form_data = {
            "name": "测试模型",
            "provider_type": "llm",
            "api_url": "https://api.openai.com/v1",
            "api_key": "test_key",
            "model_name": "gpt-4",
            "use_proxy": True,
            "proxy_config": None,
        }

        form = ModelProviderAdminForm(data=form_data)
        assert not form.is_valid()
        assert "proxy_config" in form.errors or "use_proxy" in form.errors

    def test_form_validation_allow_disabled_without_proxy(self):
        """测试禁用代理时可以不选择代理"""
        from apps.models.admin import ModelProviderAdminForm

        # 创建表单数据（禁用代理且未选择代理）
        form_data = {
            "name": "测试模型",
            "provider_type": "llm",
            "api_url": "https://api.openai.com/v1",
            "api_key": "test_key",
            "model_name": "gpt-4",
            "use_proxy": False,
            "proxy_config": "",
            "is_active": True,
            "timeout": 60,
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "priority": 0,
            "rate_limit_rpm": 60,
            "rate_limit_rpd": 1000,
        }

        form = ModelProviderAdminForm(data=form_data)
        # 表单应该有效（禁用代理时不需要选择代理）
        assert form.is_valid()

    def test_form_validation_allow_enabled_with_proxy(self):
        """测试启用代理且选择了代理"""
        from apps.models.admin import ModelProviderAdminForm

        # 创建激活的代理
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="127.0.0.1",
            port=8080,
            is_active=True,
        )

        # 创建表单数据（启用代理且选择了代理）
        form_data = {
            "name": "测试模型",
            "provider_type": "llm",
            "api_url": "https://api.openai.com/v1",
            "api_key": "test_key",
            "model_name": "gpt-4",
            "use_proxy": True,
            "proxy_config": proxy.id,
            "is_active": True,
            "timeout": 60,
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "priority": 0,
            "rate_limit_rpm": 60,
            "rate_limit_rpd": 1000,
        }

        form = ModelProviderAdminForm(data=form_data)
        assert form.is_valid()
