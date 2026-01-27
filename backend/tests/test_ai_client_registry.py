"""
AI客户端注册表测试
测试core.ai_client.registry的各种功能
"""

import pytest
from core.ai_client.registry import (
    get_executor_class,
    validate_executor,
    get_base_class_for_provider_type,
    validate_executor_for_provider
)
from core.ai_client.base import BaseAIClient, LLMClient, Text2ImageClient, Image2VideoClient


@pytest.mark.unit
class TestGetExecutorClass:
    """测试get_executor_class函数"""

    def test_get_valid_executor_class(self):
        """测试导入有效的执行器类"""
        # 测试Mock LLM客户端
        cls = get_executor_class('core.ai_client.mock_llm_client.MockLLMClient')
        assert cls is not None
        assert cls.__name__ == 'MockLLMClient'

    def test_get_mock_text2image_client(self):
        """测试导入Mock文生图客户端"""
        cls = get_executor_class('core.ai_client.mock_text2image_client.MockText2ImageClient')
        assert cls is not None
        assert cls.__name__ == 'MockText2ImageClient'

    def test_get_mock_image2video_client(self):
        """测试导入Mock图生视频客户端"""
        cls = get_executor_class('core.ai_client.mock_image2video_client.MockImage2VideoClient')
        assert cls is not None
        assert cls.__name__ == 'MockImage2VideoClient'

    def test_invalid_class_path_raises_error(self):
        """测试无效类路径抛出ImportError"""
        with pytest.raises(ImportError):
            get_executor_class('invalid.module.InvalidClass')

    def test_empty_class_path_raises_error(self):
        """测试空类路径抛出ValueError"""
        with pytest.raises(ValueError, match="执行器类路径不能为空"):
            get_executor_class('')

    def test_class_path_without_dot_raises_error(self):
        """测试不包含点的类路径抛出错误"""
        # rsplit会抛出ValueError
        with pytest.raises(ValueError):
            get_executor_class('InvalidClassName')


@pytest.mark.unit
class TestValidateExecutor:
    """测试validate_executor函数"""

    def test_validate_valid_llm_client(self):
        """测试验证有效的LLM客户端"""
        from core.ai_client.mock_llm_client import MockLLMClient
        assert validate_executor(MockLLMClient, LLMClient) is True

    def test_validate_text2image_client(self):
        """测试验证文生图客户端"""
        from core.ai_client.mock_text2image_client import MockText2ImageClient
        assert validate_executor(MockText2ImageClient, Text2ImageClient) is True

    def test_validate_image2video_client(self):
        """测试验证图生视频客户端"""
        from core.ai_client.mock_image2video_client import MockImage2VideoClient
        assert validate_executor(MockImage2VideoClient, Image2VideoClient) is True

    def test_validate_wrong_base_class_returns_false(self):
        """测试验证错误的基类返回False"""
        from core.ai_client.mock_llm_client import MockLLMClient
        # MockLLMClient不应该继承自Text2ImageClient
        assert validate_executor(MockLLMClient, Text2ImageClient) is False

    def test_validate_none_returns_false(self):
        """测试验证None返回False"""
        assert validate_executor(None, LLMClient) is False

    def test_validate_non_class_returns_false(self):
        """测试验证非类对象返回False"""
        assert validate_executor("not_a_class", LLMClient) is False

    def test_validate_instance_returns_false(self):
        """测试验证类实例返回False"""
        from core.ai_client.mock_llm_client import MockLLMClient
        instance = MockLLMClient(api_url="test", api_key="test", model_name="test")
        assert validate_executor(instance, LLMClient) is False


@pytest.mark.unit
class TestGetBaseClassForProviderType:
    """测试get_base_class_for_provider_type函数"""

    def test_get_llm_base_class(self):
        """测试获取LLM基类"""
        assert get_base_class_for_provider_type('llm') == LLMClient

    def test_get_text2image_base_class(self):
        """测试获取文生图基类"""
        assert get_base_class_for_provider_type('text2image') == Text2ImageClient

    def test_get_image2video_base_class(self):
        """测试获取图生视频基类"""
        assert get_base_class_for_provider_type('image2video') == Image2VideoClient

    def test_invalid_provider_type_raises_error(self):
        """测试无效provider_type抛出ValueError"""
        with pytest.raises(ValueError, match="无效的provider_type"):
            get_base_class_for_provider_type('invalid_type')

    def test_empty_provider_type_raises_error(self):
        """测试空provider_type抛出ValueError"""
        with pytest.raises(ValueError, match="无效的provider_type"):
            get_base_class_for_provider_type('')


@pytest.mark.unit
class TestValidateExecutorForProvider:
    """测试validate_executor_for_provider函数"""

    def test_validate_llm_executor_for_llm_provider(self):
        """测试验证LLM执行器用于LLM provider"""
        from core.ai_client.mock_llm_client import MockLLMClient
        assert validate_executor_for_provider(MockLLMClient, 'llm') is True

    def test_validate_text2image_executor_for_text2image_provider(self):
        """测试验证文生图执行器用于文生图provider"""
        from core.ai_client.mock_text2image_client import MockText2ImageClient
        assert validate_executor_for_provider(MockText2ImageClient, 'text2image') is True

    def test_validate_image2video_executor_for_image2video_provider(self):
        """测试验证图生视频执行器用于图生视频provider"""
        from core.ai_client.mock_image2video_client import MockImage2VideoClient
        assert validate_executor_for_provider(MockImage2VideoClient, 'image2video') is True

    def test_validate_wrong_executor_for_provider_returns_false(self):
        """测试验证错误的执行器返回False"""
        from core.ai_client.mock_llm_client import MockLLMClient
        # LLM客户端不应该用于text2image provider
        assert validate_executor_for_provider(MockLLMClient, 'text2image') is False

    def test_validate_none_executor_returns_false(self):
        """测试验证None执行器返回False"""
        assert validate_executor_for_provider(None, 'llm') is False

    def test_validate_with_invalid_provider_type_returns_false(self):
        """测试无效provider_type返回False"""
        from core.ai_client.mock_llm_client import MockLLMClient
        assert validate_executor_for_provider(MockLLMClient, 'invalid_type') is False

    def test_validate_with_empty_provider_type_returns_false(self):
        """测试空provider_type返回False"""
        from core.ai_client.mock_llm_client import MockLLMClient
        assert validate_executor_for_provider(MockLLMClient, '') is False
