"""
执行器工厂
职责: 根据ModelProvider配置动态创建AI客户端实例
遵循工厂模式: 封装复杂的对象创建逻辑
"""

import logging
import os
from typing import Optional

from .base import BaseAIClient
from .registry import get_executor_class

logger = logging.getLogger(__name__)


def create_ai_client(provider) -> BaseAIClient:
    """
    根据ModelProvider实例创建AI客户端

    支持通过环境变量 ENABLE_MOCK_AI=true 启用Mock客户端用于离线测试

    Args:
        provider: ModelProvider实例（来自apps.models.models）

    Returns:
        BaseAIClient: 客户端实例

    Raises:
        ValueError: 配置无效
        ImportError: 执行器类无法导入
        Exception: 客户端创建失败
    """
    # 验证provider对象
    if not provider:
        raise ValueError("ModelProvider实例不能为空")

    # 检查是否启用Mock AI模式（用于离线测试）
    enable_mock = os.environ.get("ENABLE_MOCK_AI", "").lower() == "true"
    use_enhanced = os.environ.get("USE_ENHANCED_MOCK", "").lower() == "true"

    if enable_mock:
        logger.info(
            f"检测到ENABLE_MOCK_AI=true，使用{'Enhanced' if use_enhanced else '标准'}Mock客户端"
        )
        return _create_mock_client(provider, use_enhanced=use_enhanced)

    # 获取执行器类路径
    executor_class_path = provider.executor_class

    # 如果未配置执行器，使用默认执行器
    if not executor_class_path:
        executor_class_path = provider.get_default_executor()
        logger.warning(
            f"ModelProvider '{provider.name}' 未配置executor_class，"
            f"使用默认执行器: {executor_class_path}"
        )

    if not executor_class_path:
        raise ValueError(f"ModelProvider '{provider.name}' 未配置执行器，且无法获取默认执行器")

    try:
        # 动态导入执行器类
        executor_class = get_executor_class(executor_class_path)

        # 准备配置参数
        config = {
            "timeout": provider.timeout,
            "max_tokens": provider.max_tokens,
            "temperature": provider.temperature,
            "top_p": provider.top_p,
            **provider.extra_config,  # 合并额外配置
        }

        # Epic 9 Story 9.13: 代理集成
        # 检查是否启用代理并获取代理 URL
        proxy_url = None
        if hasattr(provider, "get_proxy_url"):
            proxy_url = provider.get_proxy_url()
            if proxy_url:
                config["proxy_url"] = proxy_url
                logger.info(f"模型 '{provider.name}' 启用代理: {proxy_url}")
            else:
                logger.debug(f"模型 '{provider.name}' 配置了代理但未启用或代理不可用")

        # 创建客户端实例
        client = executor_class(
            api_url=provider.api_url,
            api_key=provider.api_key,
            model_name=provider.model_name,
            **config,
        )

        logger.info(
            f"成功创建AI客户端: provider='{provider.name}', "
            f"executor='{executor_class_path}', "
            f"proxy={'enabled' if proxy_url else 'disabled'}"
        )

        return client

    except ImportError as e:
        logger.error(f"无法导入执行器类 '{executor_class_path}': {e!s}")
        raise

    except Exception as e:
        logger.error(
            f"创建AI客户端失败: provider='{provider.name}', "
            f"executor='{executor_class_path}', error={e!s}",
            exc_info=True,
        )
        raise Exception(f"创建AI客户端失败: {e!s}")


def create_ai_client_safe(provider) -> Optional[BaseAIClient]:
    """
    安全版本的create_ai_client，捕获所有异常并返回None

    Args:
        provider: ModelProvider实例

    Returns:
        Optional[BaseAIClient]: 客户端实例，失败时返回None
    """
    try:
        return create_ai_client(provider)
    except Exception as e:
        logger.error(f"创建AI客户端失败（安全模式）: {e!s}")
        return None


def _create_mock_client(provider, use_enhanced=False) -> BaseAIClient:
    """
    创建Mock AI客户端用于离线测试

    根据provider类型自动选择合适的Mock客户端：
    - LLM类型 → MockLLMClient 或 EnhancedMockLLMClient
    - 文生图类型 → MockText2ImageClient 或 EnhancedMockText2ImageClient
    - 图生视频类型 → MockImage2VideoClient

    Args:
        provider: ModelProvider实例
        use_enhanced: 是否使用增强版Mock客户端（支持可配置延迟、错误模拟等）

    Returns:
        BaseAIClient: Mock客户端实例
    """
    from .mock_image2video_client import MockImage2VideoClient
    from .mock_llm_client import MockLLMClient
    from .mock_text2image_client import MockText2ImageClient

    # 获取provider的类型/类别
    getattr(provider, "provider_type", "").lower()
    getattr(provider, "name", "").lower()

    # 根据provider类型选择合适的Mock客户端
    # 检查executor_class来判断客户端类型
    executor_class = getattr(provider, "executor_class", "")

    # Enhanced Mock配置（从环境变量读取）
    enhanced_delay = float(os.environ.get("MOCK_DELAY", "0.5"))
    enhanced_error = os.environ.get("MOCK_ERROR", "")

    # 创建Mock客户端
    if (
        "llm" in executor_class.lower()
        or "openai" in executor_class.lower()
        or "ollama" in executor_class.lower()
    ):
        if use_enhanced:
            logger.info(
                f"创建EnhancedMockLLMClient for provider '{provider.name}' (delay={enhanced_delay}s)"
            )
            from .enhanced_mock_llm_client import EnhancedMockLLMClient

            return EnhancedMockLLMClient(
                api_url="mock://llm",
                api_key="mock_key",
                model_name=provider.model_name or "enhanced-mock-llm",
                stage_type="",  # 自动检测
                simulate_delay=enhanced_delay,
                simulate_error=enhanced_error if enhanced_error else None,
                enable_logging=True,
            )
        else:
            logger.info(f"创建标准MockLLMClient for provider '{provider.name}'")
            return MockLLMClient(
                api_url="mock://llm",
                api_key="mock_key",
                model_name=provider.model_name or "mock-llm",
            )
    elif "text2image" in executor_class.lower() or "stable" in executor_class.lower():
        if use_enhanced:
            logger.info(
                f"创建EnhancedMockText2ImageClient for provider '{provider.name}' (delay={enhanced_delay}s)"
            )
            from .enhanced_mock_text2image_client import EnhancedMockText2ImageClient

            return EnhancedMockText2ImageClient(
                api_url="mock://text2image",
                api_key="mock_key",
                model_name=provider.model_name or "enhanced-mock-text2image",
                simulate_delay=enhanced_delay,
                simulate_error=enhanced_error if enhanced_error else None,
                enable_logging=True,
            )
        else:
            logger.info(f"创建标准MockText2ImageClient for provider '{provider.name}'")
            return MockText2ImageClient(
                api_url="mock://text2image",
                api_key="mock_key",
                model_name=provider.model_name or "mock-text2image",
            )
    elif "image2video" in executor_class.lower() or "runway" in executor_class.lower():
        logger.info(f"创建MockImage2VideoClient for provider '{provider.name}'")
        # Image2Video暂无Enhanced版本
        return MockImage2VideoClient(
            api_url="mock://image2video",
            api_key="mock_key",
            model_name=provider.model_name or "mock-image2video",
        )
    else:
        # 默认使用MockLLMClient
        logger.warning(
            f"无法识别provider类型 '{executor_class}'，"
            f"使用默认{'Enhanced' if use_enhanced else '标准'}MockLLMClient"
        )
        if use_enhanced:
            from .enhanced_mock_llm_client import EnhancedMockLLMClient

            return EnhancedMockLLMClient(
                api_url="mock://llm",
                api_key="mock_key",
                model_name=provider.model_name or "enhanced-mock-llm",
                simulate_delay=enhanced_delay,
                enable_logging=True,
            )
        else:
            return MockLLMClient(
                api_url="mock://llm",
                api_key="mock_key",
                model_name=provider.model_name or "mock-llm",
            )
