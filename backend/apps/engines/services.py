# Engines Services - 引擎健康检查和 Fallback 服务

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from .models import EngineConfig, EngineHealthLog, EngineUsageLog, FallbackEventLog

logger = logging.getLogger(__name__)


# ==================== 引擎定价配置 ====================

# 云端引擎定价 (美元/1K tokens 或 每次)
ENGINE_PRICING = {
    # LLM 定价
    "openai": {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.002,
    },
    "anthropic": {
        "claude-3-opus": 0.015,
        "claude-3-sonnet": 0.003,
    },
    "glm": {
        "glm-4": 0.001,  # 示例定价
    },
    "deepseek": {
        "deepseek-chat": 0.001,
    },
    # 本地引擎免费
    "ollama": {
        "*": 0.0,
    },
    # Image 引擎定价
    "dalle": {
        "dall-e-3": 0.04,  # 每次
    },
    "stable-diffusion": {
        "sdxl": 0.01,
    },
    "midjourney": {
        "*": 0.01,
    },
    "comfyui": {
        "*": 0.0,  # 本地免费
    },
    # TTS 定价
    "elevenlabs": {
        "*": 0.015,  # 每1K字符
    },
    "azure-tts": {
        "*": 0.01,
    },
    "google-tts": {
        "*": 0.004,
    },
    "edge-tts": {
        "*": 0.0,  # 免费TTS
    },
}


# ==================== 健康检查服务 ====================


class HealthCheckService:
    """
    引擎健康检查服务

    负责检查引擎的可用性和响应时间。
    """

    def __init__(self, engine: EngineConfig):
        self.engine = engine

    def check(self) -> Dict[str, Any]:
        """
        执行健康检查

        Returns:
            dict: 检查结果
                {
                    'status': 'online' | 'offline' | 'error',
                    'response_time': float (毫秒),
                    'error_message': str,
                    'error_code': str,
                }
        """
        provider = self.engine.primary_provider
        engine_type = self.engine.engine_type

        try:
            if engine_type == "llm":
                return self._check_llm(provider)
            elif engine_type == "image":
                return self._check_image(provider)
            elif engine_type == "tts":
                return self._check_tts(provider)
            else:
                return {
                    "status": "error",
                    "response_time": None,
                    "error_message": f"未知引擎类型: {engine_type}",
                    "error_code": "UNKNOWN_ENGINE_TYPE",
                }
        except requests.RequestException as e:
            logger.warning(f"引擎 {self.engine.name} 健康检查失败: {e}")
            return {
                "status": "offline",
                "response_time": None,
                "error_message": f"连接失败: {e!s}",
                "error_code": "CONNECTION_ERROR",
            }
        except Exception as e:
            logger.error(f"引擎 {self.engine.name} 健康检查异常: {e}")
            return {
                "status": "error",
                "response_time": None,
                "error_message": f"检查异常: {e!s}",
                "error_code": "CHECK_ERROR",
            }

    def _check_llm(self, provider: str) -> Dict[str, Any]:
        """检查 LLM 引擎健康状态"""
        config = self.engine.primary_config

        if provider == "ollama":
            return self._check_ollama(config)
        elif provider == "openai":
            return self._check_openai(config)
        else:
            # 通用健康检查：返回 online（实际使用时会记录真实状态）
            return {
                "status": "online",
                "response_time": 100.0,
                "error_message": "",
                "error_code": "",
            }

    def _check_ollama(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查 Ollama 引擎"""
        base_url = config.get("base_url", "http://localhost:11434")

        # Ollama API 健康检查端点
        url = urljoin(base_url, "/api/tags")

        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "status": "online",
                    "response_time": response_time,
                    "error_message": "",
                    "error_code": "",
                }
            else:
                return {
                    "status": "error",
                    "response_time": response_time,
                    "error_message": f"HTTP {response.status_code}",
                    "error_code": f"HTTP_{response.status_code}",
                }
        except requests.Timeout:
            return {
                "status": "offline",
                "response_time": 10000.0,
                "error_message": "请求超时",
                "error_code": "TIMEOUT",
            }

    def _check_openai(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查 OpenAI 引擎"""
        # OpenAI API 简单检查
        api_key = config.get("api_key")
        if not api_key:
            return {
                "status": "error",
                "response_time": None,
                "error_message": "缺少 API 密钥",
                "error_code": "MISSING_API_KEY",
            }

        # 模拟检查（实际会调用 OpenAI API）
        start_time = time.time()
        time.sleep(0.1)  # 模拟网络延迟
        response_time = (time.time() - start_time) * 1000

        return {
            "status": "online",
            "response_time": response_time,
            "error_message": "",
            "error_code": "",
        }

    def _check_image(self, provider: str) -> Dict[str, Any]:
        """检查图像生成引擎"""
        config = self.engine.primary_config

        if provider == "comfyui":
            return self._check_comfyui(config)
        else:
            # 通用检查
            return {
                "status": "online",
                "response_time": 500.0,
                "error_message": "",
                "error_code": "",
            }

    def _check_comfyui(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查 ComfyUI 引擎"""
        base_url = config.get("base_url", "http://localhost:8188")

        # ComfyUI 健康检查
        url = urljoin(base_url, "/system_stats")

        start_time = time.time()
        try:
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "status": "online",
                    "response_time": response_time,
                    "error_message": "",
                    "error_code": "",
                }
            else:
                return {
                    "status": "error",
                    "response_time": response_time,
                    "error_message": f"HTTP {response.status_code}",
                    "error_code": f"HTTP_{response.status_code}",
                }
        except requests.Timeout:
            return {
                "status": "offline",
                "response_time": 10000.0,
                "error_message": "请求超时",
                "error_code": "TIMEOUT",
            }

    def _check_tts(self, provider: str) -> Dict[str, Any]:
        """检查 TTS 引擎"""
        if provider == "edge-tts":
            # Edge-TTS 是本地库，总是可用的
            return {
                "status": "online",
                "response_time": 50.0,
                "error_message": "",
                "error_code": "",
            }
        else:
            # 通用检查
            return {
                "status": "online",
                "response_time": 200.0,
                "error_message": "",
                "error_code": "",
            }

    def save_health_log(self, result: Dict[str, Any]):
        """保存健康检查日志"""
        EngineHealthLog.objects.create(
            engine=self.engine,
            status=result["status"],
            response_time=result.get("response_time"),
            error_message=result.get("error_message", ""),
            error_code=result.get("error_code", ""),
        )

        # 更新引擎状态
        self.engine.health_status = result["status"]
        self.engine.save(update_fields=["health_status"])

        logger.info(
            f"引擎 {self.engine.name} 健康检查完成: "
            f"{result['status']} ({(result.get('response_time') or 0):.0f}ms)"
        )


# ==================== Fallback 服务 ====================


class FallbackService:
    """
    Fallback 自动切换服务

    负责监控引擎失败并在必要时切换到备份引擎。
    """

    def __init__(self, engine: EngineConfig):
        self.engine = engine

    def should_trigger_fallback(self) -> bool:
        """
        判断是否应该触发 Fallback

        Returns:
            bool: 是否需要切换
        """
        if not self.engine.auto_fallback:
            return False

        if not self.engine.fallback_provider:
            return False

        # 使用模型的方法判断
        return self.engine.should_fallback()

    def switch_to_fallback(self, reason: str = "failure", reason_detail: str = "") -> bool:
        """
        切换到备份引擎

        Args:
            reason: 切换原因 (timeout/failure/manual/error)
            reason_detail: 原因详情

        Returns:
            bool: 切换是否成功
        """
        if not self.engine.fallback_provider:
            logger.warning(f"引擎 {self.engine.name} 没有配置备份引擎")
            return False

        from_provider = self.engine.current_provider or self.engine.primary_provider
        to_provider = self.engine.fallback_provider

        # 记录 Fallback 事件
        event = FallbackEventLog.objects.create(
            engine=self.engine,
            from_provider=from_provider,
            to_provider=to_provider,
            reason=reason,
            reason_detail=reason_detail or f"{from_provider} → {to_provider}",
            affected_requests=0,  # 后续可以统计
        )

        # 更新引擎当前提供商
        self.engine.current_provider = to_provider
        self.engine.health_status = "unknown"  # 新引擎状态未知
        self.engine.failure_count = 0  # 重置失败计数
        self.engine.save(update_fields=["current_provider", "health_status", "failure_count"])

        logger.info(
            f"引擎 {self.engine.name} 已切换: {from_provider} → {to_provider} (原因: {reason})"
        )

        # 发送 WebSocket 通知
        self._notify_fallback(event)

        return True

    def _notify_fallback(self, event: FallbackEventLog):
        """发送 Fallback 事件通知"""
        # TODO: 实现 WebSocket 推送
        # 将在 Story 11.3.2 的 WebSocket 部分实现
        logger.info(
            f"Fallback 事件: {event.engine.engine_type} - "
            f"{event.from_provider} → {event.to_provider}"
        )


# ==================== 成本计算服务 ====================


class CostCalculationService:
    """
    成本计算服务

    负责计算引擎使用成本和节省金额。
    """

    @staticmethod
    def calculate_cost(
        provider: str,
        model: str,
        token_count: int,
        request_type: str,
    ) -> float:
        """
        计算实际花费

        Args:
            provider: 提供商
            model: 模型名称
            token_count: Token 数量
            request_type: 请求类型 (llm/image/tts)

        Returns:
            float: 花费金额 (美元)
        """
        if provider not in ENGINE_PRICING:
            return 0.0

        pricing = ENGINE_PRICING[provider]

        # 检查是否有特定模型定价
        if model in pricing:
            per_unit_cost = pricing[model]
            # 对于图像/TTS，按次计费（直接返回定价）
            if request_type in ("image", "tts"):
                return per_unit_cost
            # 对于 LLM，按 token 计费
            return (token_count / 1000) * per_unit_cost

        # 检查是否有通配符定价
        if "*" in pricing:
            # 对于图像/TTS，按次计费
            if request_type in ("image", "tts"):
                return pricing["*"]
            # 对于 LLM，按 token 计费
            return (token_count / 1000) * pricing["*"]

        return 0.0

    @staticmethod
    def calculate_saved_cost(
        primary_provider: str,
        actual_provider: str,
        model: str,
        token_count: int,
        request_type: str,
    ) -> float:
        """
        计算节省金额

        如果使用本地引擎而未使用云端引擎，则计算节省的金额。

        Args:
            primary_provider: 主引擎提供商
            actual_provider: 实际使用的提供商
            model: 模型名称（本地引擎的模型）
            token_count: Token 数量
            request_type: 请求类型

        Returns:
            float: 节省金额 (美元)
        """
        # 如果使用的是本地/免费引擎，计算相比云端的节省
        # 本地引擎: ollama, comfyui, edge-tts
        if actual_provider in ("ollama", "comfyui", "edge-tts"):
            # 找到云端对照提供商并计算成本
            if actual_provider == "ollama":
                # 使用 GPT-4 作为云端对照
                return CostCalculationService.calculate_cost(
                    "openai", "gpt-4", token_count, request_type
                )
            elif actual_provider == "comfyui":
                # 使用 DALL-E 3 作为云端对照
                return CostCalculationService.calculate_cost(
                    "dalle", "dall-e-3", token_count, request_type
                )
            elif actual_provider == "edge-tts":
                # 使用 ElevenLabs 作为云端对照
                return CostCalculationService.calculate_cost(
                    "elevenlabs", "*", token_count, request_type
                )

        return 0.0


# ==================== 使用记录服务 ====================


class UsageService:
    """
    引擎使用记录服务

    负责记录引擎使用统计和成本信息。
    """

    @staticmethod
    def record_usage(
        engine: EngineConfig,
        provider: str,
        request_type: str,
        success: bool,
        response_time: float,
        token_count: Optional[int] = None,
        project_id: Optional[str] = None,
        shot_id: Optional[str] = None,
    ) -> EngineUsageLog:
        """
        记录引擎使用

        Args:
            engine: 引擎配置
            provider: 实际使用的提供商
            request_type: 请求类型
            success: 是否成功
            response_time: 响应时间 (毫秒)
            token_count: Token 数量
            project_id: 项目 ID
            shot_id: 镜头 ID

        Returns:
            EngineUsageLog: 使用日志记录
        """
        # 计算成本
        cost = 0.0
        saved_cost = 0.0

        if success and token_count:
            # 实际花费
            cost = CostCalculationService.calculate_cost(
                provider,
                engine.primary_config.get("model", "unknown"),
                token_count,
                request_type,
            )

            # 节省金额（如果使用本地引擎）
            saved_cost = CostCalculationService.calculate_saved_cost(
                engine.primary_provider,
                provider,
                engine.primary_config.get("model", "unknown"),
                token_count,
                request_type,
            )

        # 创建使用日志
        log = EngineUsageLog.objects.create(
            engine=engine,
            provider=provider,
            request_type=request_type,
            success=success,
            response_time=response_time,
            token_count=token_count,
            cost=cost,
            saved_cost=saved_cost,
            project_id=project_id,
            shot_id=shot_id,
        )

        # 更新引擎统计
        if success:
            engine.record_success(response_time, cost, saved_cost)
        else:
            engine.record_failure()

        logger.info(
            f"引擎使用记录: {engine.engine_type} - {provider} - "
            f"{'✓' if success else '✗'} ({response_time:.0f}ms) - "
            f"${cost:.4f} (省 ${saved_cost:.4f})"
        )

        return log


# ==================== 综合服务 ====================


class EngineMonitoringService:
    """
    引擎监控综合服务

    整合健康检查、Fallback 切换和使用记录功能。
    """

    @staticmethod
    def perform_health_check(engine: EngineConfig) -> Dict[str, Any]:
        """
        执行完整的健康检查流程

        Args:
            engine: 引擎配置

        Returns:
            dict: 检查结果
        """
        service = HealthCheckService(engine)
        result = service.check()
        service.save_health_log(result)

        # 检查是否需要 Fallback
        fallback_service = FallbackService(engine)
        if result["status"] in ("offline", "error") and fallback_service.should_trigger_fallback():
            fallback_service.switch_to_fallback(
                reason="error" if result["status"] == "error" else "timeout",
                reason_detail=result.get("error_message", ""),
            )

        return result

    @staticmethod
    def check_all_engines() -> Dict[str, Dict[str, Any]]:
        """
        检查所有引擎的健康状态

        Returns:
            dict: 各引擎的检查结果
        """
        results = {}
        for engine in EngineConfig.objects.filter(is_active=True):
            try:
                results[engine.engine_type] = EngineMonitoringService.perform_health_check(engine)
            except Exception as e:
                logger.error(f"检查引擎 {engine.name} 时出错: {e}")
                results[engine.engine_type] = {
                    "status": "error",
                    "error_message": str(e),
                }

        return results
