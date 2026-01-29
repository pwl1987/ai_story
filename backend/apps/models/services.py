"""
模型管理服务层
职责: 处理模型提供商相关业务逻辑
遵循单一职责原则(SRP)和依赖倒置原则(DIP)
"""

from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Avg, Q, Sum

from .models import ModelProvider, ModelUsageLog


class ModelProviderService:
    """
    模型提供商服务
    职责: 处理模型提供商的业务逻辑
    """

    @staticmethod
    def get_active_providers(provider_type: Optional[str] = None) -> List[ModelProvider]:
        """
        获取激活的模型提供商

        Args:
            provider_type: 提供商类型 (llm, text2image, image2video)

        Returns:
            激活的模型提供商列表
        """
        queryset = ModelProvider.objects.filter(is_active=True)

        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)

        return queryset.order_by("-priority", "-created_at")

    @staticmethod
    def get_provider_by_type_and_priority(
        provider_type: str, min_priority: int = 0
    ) -> Optional[ModelProvider]:
        """
        根据类型和优先级获取模型提供商

        Args:
            provider_type: 提供商类型
            min_priority: 最小优先级

        Returns:
            符合条件的最高优先级提供商
        """
        return (
            ModelProvider.objects.filter(
                provider_type=provider_type, is_active=True, priority__gte=min_priority
            )
            .order_by("-priority")
            .first()
        )

    @staticmethod
    def search_providers(
        keyword: str, provider_type: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[ModelProvider]:
        """
        搜索模型提供商

        Args:
            keyword: 搜索关键词
            provider_type: 提供商类型
            is_active: 是否激活

        Returns:
            符合条件的提供商列表
        """
        queryset = ModelProvider.objects.all()

        # 关键词搜索
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(model_name__icontains=keyword)
                | Q(api_url__icontains=keyword)
            )

        # 类型过滤
        if provider_type:
            queryset = queryset.filter(provider_type=provider_type)

        # 激活状态过滤
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        return queryset.order_by("-priority", "-created_at")

    @staticmethod
    @transaction.atomic
    def create_provider(data: Dict[str, Any]) -> ModelProvider:
        """
        创建模型提供商

        Args:
            data: 提供商数据

        Returns:
            创建的模型提供商实例
        """
        provider = ModelProvider.objects.create(**data)
        return provider

    @staticmethod
    @transaction.atomic
    def update_provider(provider_id: str, data: Dict[str, Any]) -> ModelProvider:
        """
        更新模型提供商

        Args:
            provider_id: 提供商ID
            data: 更新数据

        Returns:
            更新后的模型提供商实例
        """
        provider = ModelProvider.objects.get(id=provider_id)

        for key, value in data.items():
            setattr(provider, key, value)

        provider.save()
        return provider

    @staticmethod
    @transaction.atomic
    def delete_provider(provider_id: str) -> bool:
        """
        删除模型提供商

        Args:
            provider_id: 提供商ID

        Returns:
            是否删除成功
        """
        try:
            provider = ModelProvider.objects.get(id=provider_id)
            provider.delete()
            return True
        except ModelProvider.DoesNotExist:
            return False

    @staticmethod
    @transaction.atomic
    def toggle_provider_status(provider_id: str) -> ModelProvider:
        """
        切换模型提供商激活状态

        Args:
            provider_id: 提供商ID

        Returns:
            更新后的模型提供商实例
        """
        provider = ModelProvider.objects.get(id=provider_id)
        provider.is_active = not provider.is_active
        provider.save()
        return provider

    @staticmethod
    def get_provider_statistics(provider_id: str) -> Dict[str, Any]:
        """
        获取模型提供商统计信息

        Args:
            provider_id: 提供商ID

        Returns:
            统计信息字典
        """
        provider = ModelProvider.objects.get(id=provider_id)

        # 总调用次数
        total_count = provider.usage_logs.count()

        # 成功/失败次数
        success_count = provider.usage_logs.filter(status="success").count()
        failed_count = provider.usage_logs.filter(status="failed").count()

        # 成功率
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        # 平均延迟
        avg_latency = provider.usage_logs.aggregate(avg=Avg("latency_ms"))["avg"] or 0

        # 总Token使用量
        total_tokens = provider.usage_logs.aggregate(total=Sum("tokens_used"))["total"] or 0

        # 最近7天使用情况
        from datetime import timedelta

        from django.utils import timezone

        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_count = provider.usage_logs.filter(created_at__gte=seven_days_ago).count()

        return {
            "total_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "total_tokens_used": total_tokens,
            "recent_7days_count": recent_count,
        }

    @staticmethod
    async def test_provider_connection(
        provider_id: str, test_prompt: str = "Hello, this is a test."
    ) -> Dict[str, Any]:
        """
        测试模型提供商连接

        Args:
            provider_id: 提供商ID
            test_prompt: 测试提示词

        Returns:
            测试结果
        """
        import time

        # 使用 sync_to_async 包装同步查询
        provider = await sync_to_async(ModelProvider.objects.get)(id=provider_id)

        if not provider.is_active:
            return {"success": False, "error": "模型提供商未激活"}

        start_time = time.time()

        try:
            # 根据提供商类型选择测试方法
            if provider.provider_type == "llm":
                result = ModelProviderService._test_llm_provider(provider, test_prompt)
            elif provider.provider_type == "text2image":
                result = await ModelProviderService._test_text2image_provider(provider, test_prompt)
            elif provider.provider_type == "image2video":
                result = await ModelProviderService._test_image2video_provider(provider)
            else:
                return {"success": False, "error": f"不支持的提供商类型: {provider.provider_type}"}

            # 计算延迟
            latency_ms = int((time.time() - start_time) * 1000)

            # 记录使用日志
            await sync_to_async(ModelUsageLog.objects.create)(
                model_provider=provider,
                request_data={"test_prompt": test_prompt},
                response_data=result.get("data", {}),
                tokens_used=result.get("tokens_used", 0),
                latency_ms=latency_ms,
                status="success" if result.get("success") else "failed",
                error_message=result.get("error", "暂无错误") or "暂无错误",
                stage_type="test",
            )

            return {
                "success": result.get("success", False),
                "latency_ms": latency_ms,
                "response": result.get("text", ""),
                "data": result.get("data", {}),
                "error": result.get("error"),
            }

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            # 记录失败日志
            await sync_to_async(ModelUsageLog.objects.create)(
                model_provider=provider,
                request_data={"test_prompt": test_prompt},
                response_data={},
                latency_ms=latency_ms,
                status="failed",
                error_message=str(e),
                stage_type="test",
            )

            return {"success": False, "latency_ms": latency_ms, "error": str(e)}

    @staticmethod
    def _test_llm_provider(provider: ModelProvider, prompt: str) -> Dict[str, Any]:
        """测试LLM提供商"""
        from core.ai_client.openai_client import OpenAIClient

        client = OpenAIClient(
            api_url=provider.api_url,
            api_key=provider.api_key,
            model_name=provider.model_name,
            max_tokens=min(provider.max_tokens, 100),  # 测试时限制token数
            temperature=provider.temperature,
            timeout=provider.timeout,
        )
        full_text = ""
        is_success = False
        for chunk in client.generate_stream(prompt):
            if chunk.get("type") == "done":
                full_text = chunk.get("full_text")
                is_success = True
            elif chunk.get("type") == "error":
                full_text = chunk.get("error")
                is_success = False
        return {
            "success": is_success,
            "text": full_text,
            "data": {"prompt": prompt, "provider": provider.name},
            "tokens_used": 0,
        }

    @staticmethod
    async def _test_text2image_provider(provider: ModelProvider, prompt: str) -> Dict[str, Any]:
        """测试文生图提供商"""
        # 这里返回模拟结果,实际实现需要调用对应的AI客户端
        return {
            "success": True,
            "text": "Text2Image test successful",
            "data": {"prompt": prompt, "provider": provider.name},
            "tokens_used": 0,
        }

    @staticmethod
    async def _test_image2video_provider(provider: ModelProvider) -> Dict[str, Any]:
        """测试图生视频提供商"""
        # 这里返回模拟结果,实际实现需要调用对应的AI客户端
        return {
            "success": True,
            "text": "Image2Video test successful",
            "data": {"provider": provider.name},
            "tokens_used": 0,
        }


class ModelUsageLogService:
    """
    模型使用日志服务
    职责: 处理使用日志相关业务逻辑
    """

    @staticmethod
    def get_logs_by_provider(provider_id: str, limit: int = 100) -> List[ModelUsageLog]:
        """
        获取指定提供商的使用日志

        Args:
            provider_id: 提供商ID
            limit: 返回条数限制

        Returns:
            使用日志列表
        """
        return ModelUsageLog.objects.filter(model_provider_id=provider_id).order_by("-created_at")[
            :limit
        ]

    @staticmethod
    def get_logs_by_project(
        project_id: str, stage_type: Optional[str] = None
    ) -> List[ModelUsageLog]:
        """
        获取指定项目的使用日志

        Args:
            project_id: 项目ID
            stage_type: 阶段类型

        Returns:
            使用日志列表
        """
        queryset = ModelUsageLog.objects.filter(project_id=project_id)

        if stage_type:
            queryset = queryset.filter(stage_type=stage_type)

        return queryset.order_by("-created_at")

    @staticmethod
    def get_failed_logs(limit: int = 100) -> List[ModelUsageLog]:
        """
        获取失败的使用日志

        Args:
            limit: 返回条数限制

        Returns:
            失败日志列表
        """
        return ModelUsageLog.objects.filter(status="failed").order_by("-created_at")[:limit]

    @staticmethod
    def create_usage_log(data: Dict[str, Any]) -> ModelUsageLog:
        """
        创建使用日志

        Args:
            data: 日志数据

        Returns:
            创建的日志实例
        """
        return ModelUsageLog.objects.create(**data)
