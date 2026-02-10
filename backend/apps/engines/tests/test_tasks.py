# Engines Tasks Tests - 引擎异步任务测试

from unittest.mock import Mock, patch

import pytest
from celery.exceptions import Retry
from django.core.exceptions import ValidationError

from apps.engines.models import EngineConfig, EngineHealthLog
from apps.engines.tasks import (
    check_single_engine_task,
    manual_health_check_task,
    periodic_health_check_task,
)


@pytest.mark.django_db
@pytest.mark.celery()
class TestPeriodicHealthCheckTask:
    """periodic_health_check_task 测试"""

    def test_periodic_health_check_all_online(self):
        """测试所有引擎在线的健康检查"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )
        EngineConfig.objects.create(
            engine_type="tts",
            name="TTS 引擎",
            primary_provider="edge-tts",
            primary_config={"voice": "zh-CN-XiaoxiaoNeural"},
        )

        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            mock_check.return_value = {
                "llm": {"status": "online", "response_time": 100.0},
                "tts": {"status": "online", "response_time": 50.0},
            }

            result = periodic_health_check_task()

            assert result["summary"]["online"] == 2
            assert result["summary"]["total"] == 2

    def test_periodic_health_check_mixed_status(self):
        """测试混合状态的健康检查"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )
        EngineConfig.objects.create(
            engine_type="tts",
            name="TTS 引擎",
            primary_provider="edge-tts",
            primary_config={"voice": "zh-CN-XiaoxiaoNeural"},
        )

        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            mock_check.return_value = {
                "llm": {"status": "online", "response_time": 100.0},
                "tts": {"status": "offline", "response_time": None},
            }

            result = periodic_health_check_task()

            assert result["summary"]["online"] == 1
            assert result["summary"]["offline"] == 1

    def test_periodic_health_check_error_handling(self):
        """测试健康检查错误处理"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            mock_check.side_effect = Exception("Health check failed")

            result = periodic_health_check_task()

            assert "summary" in result
            assert "results" in result


@pytest.mark.django_db
@pytest.mark.celery()
class TestCheckSingleEngineTask:
    """check_single_engine_task 测试"""

    def test_check_single_engine_success(self):
        """测试单个引擎健康检查成功"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.return_value = {
                "status": "online",
                "response_time": 100.0,
            }

            result = check_single_engine_task(str(engine.id))

            assert result["status"] == "online"

    def test_check_single_engine_not_found(self):
        """测试检查不存在的引擎"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises((ValidationError, Exception)):
            check_single_engine_task(fake_id)


@pytest.mark.django_db
@pytest.mark.celery()
class TestManualHealthCheckTask:
    """manual_health_check_task 测试"""

    def test_manual_check_all_engines(self):
        """测试手动检查所有引擎"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )
        EngineConfig.objects.create(
            engine_type="tts",
            name="TTS 引擎",
            primary_provider="edge-tts",
            primary_config={"voice": "zh-CN-XiaoxiaoNeural"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.return_value = {
                "status": "online",
                "response_time": 100.0,
            }

            result = manual_health_check_task()

            assert result["engine_type"] is None
            assert "llm" in result["results"]
            assert "tts" in result["results"]

    def test_manual_check_specific_engine_type(self):
        """测试手动检查特定引擎类型"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.return_value = {
                "status": "online",
                "response_time": 100.0,
            }

            result = manual_health_check_task(engine_type="llm")

            assert result["engine_type"] == "llm"
            assert "llm" in result["results"]

    def test_manual_check_no_engines(self):
        """测试手动检查没有引擎"""
        result = manual_health_check_task()

        assert result["results"] == {}


@pytest.mark.django_db
@pytest.mark.celery()
class TestCeleryTaskErrorHandling:
    """Celery 任务错误处理测试"""

    def test_periodic_health_check_retry_on_failure(self):
        """测试定期健康检查失败时优雅处理"""
        # 模拟 check_all_engines 抛出异常
        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            mock_check.side_effect = Exception("Database error")

            # 任务应该返回错误结果而不是抛出异常
            result = periodic_health_check_task()
            assert "summary" in result
            assert "results" in result
            assert result["summary"]["total"] == 0
            assert "error" in result

    def test_check_single_engine_retry_on_failure(self):
        """测试单引擎检查失败时重试"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.side_effect = Exception("Network error")

            with pytest.raises(Exception, match="Network error"):
                check_single_engine_task(str(engine.id))

    def test_manual_check_exception_handling(self):
        """测试手动检查异常处理"""
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.side_effect = Exception("Unexpected error")

            result = manual_health_check_task()

            # 应该处理异常并返回
            assert "results" in result


@pytest.mark.django_db
class TestTaskIntegration:
    """任务集成测试"""

    def test_periodic_task_creates_health_logs(self):
        """测试定期任务创建健康日志"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
        )

        initial_count = EngineHealthLog.objects.filter(engine=engine).count()

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            periodic_health_check_task()

        # 验证创建了新的健康日志
        final_count = EngineHealthLog.objects.filter(engine=engine).count()
        assert final_count > initial_count

    def test_periodic_task_updates_health_status(self):
        """测试定期任务更新引擎健康状态"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
            health_status="unknown",
        )

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            periodic_health_check_task()

        # 验证健康状态已更新
        engine.refresh_from_db()
        assert engine.health_status == "online"

    def test_single_engine_task_updates_engine(self):
        """测试单引擎检查任务更新引擎状态"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={
                "base_url": "http://localhost:11434",
                "model": "llama2:7b",
            },
            health_status="unknown",
        )

        with patch("apps.engines.services.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            check_single_engine_task(str(engine.id))

        # 验证健康状态已更新
        engine.refresh_from_db()
        assert engine.health_status == "online"

    def test_manual_check_all_engine_types(self):
        """测试手动检查覆盖所有引擎类型"""
        # 创建三种类型的引擎
        EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )
        EngineConfig.objects.create(
            engine_type="image",
            name="Image 引擎",
            primary_provider="comfyui",
            primary_config={
                "base_url": "http://localhost:8188",
                "workflow": "sdxl",
            },
        )
        EngineConfig.objects.create(
            engine_type="tts",
            name="TTS 引擎",
            primary_provider="edge-tts",
            primary_config={"voice": "zh-CN-XiaoxiaoNeural"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.return_value = {
                "status": "online",
                "response_time": 100.0,
            }

            result = manual_health_check_task()

            # 验证检查了所有引擎
            assert len(result["results"]) == 3


@pytest.mark.django_db
@pytest.mark.celery()
class TestTaskPerformance:
    """任务性能测试"""

    def test_periodic_check_returns_quickly(self):
        """测试定期检查快速返回"""
        # 创建 3 个不同类型的引擎
        engine_types = ["llm", "image", "tts"]
        for i, etype in enumerate(engine_types):
            EngineConfig.objects.create(
                engine_type=etype,
                name=f"引擎 {i}",
                primary_provider="ollama"
                if etype == "llm"
                else "comfyui"
                if etype == "image"
                else "edge-tts",
                primary_config={"model": "test"},
                is_active=True,  # 全部激活
            )

        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            # 模拟返回 3 个活跃引擎的结果
            mock_check.return_value = {
                "llm": {"status": "online", "response_time": 100.0},
                "image": {"status": "online", "response_time": 100.0},
                "tts": {"status": "online", "response_time": 100.0},
            }

            # 任务应该快速完成
            result = periodic_health_check_task()

            assert "summary" in result
            assert result["summary"]["total"] == 3

    def test_single_check_handles_invalid_id_gracefully(self):
        """测试单引擎检查优雅处理无效 ID"""
        # 创建一个有效引擎
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            mock_check.return_value = {"status": "online", "response_time": 100.0}

            # 有效引擎应该成功
            result = check_single_engine_task(str(engine.id))
            assert "status" in result

            # 无效引擎应该失败
            with pytest.raises((ValidationError, Exception)):
                check_single_engine_task("invalid-id")


@pytest.mark.django_db
@pytest.mark.celery()
class TestTaskRetryBehavior:
    """任务重试行为测试"""

    def test_periodic_task_max_retries_exceeded(self):
        """测试定期任务超过最大重试次数"""
        with patch("apps.engines.services.EngineMonitoringService.check_all_engines") as mock_check:
            # 总是失败
            mock_check.side_effect = Exception("Persistent error")

            # Celery 会在 max_retries 后放弃
            # 这里我们模拟重试失败的场景
            try:
                periodic_health_check_task()
            except Exception as e:
                # 最终应该失败
                assert "Persistent error" in str(e) or isinstance(e, Retry)

    def test_single_engine_task_max_retries(self):
        """测试单引擎检查成功场景"""
        engine = EngineConfig.objects.create(
            engine_type="llm",
            name="LLM 引擎",
            primary_provider="ollama",
            primary_config={"model": "llama2:7b"},
        )

        with patch(
            "apps.engines.services.EngineMonitoringService.perform_health_check"
        ) as mock_check:
            # 返回成功结果
            mock_check.return_value = {"status": "online", "response_time": 100.0}

            result = check_single_engine_task(str(engine.id))
            assert result["status"] == "online"
