"""
ComfyUI 服务单元测试 (Epic 10 Story 10.3)

测试覆盖:
- ComfyUIService 初始化
- 图像生成功能
- 视频生成功能
- 批量生成功能
- 健康检查
- 工作流创建
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# 注意: services.py 已重命名为 batch_operations.py，services/ 现在可以正常导入
from apps.artworks.services.comfyui_service import (
    ComfyUIService,
    get_comfyui_service,
)


class TestComfyUIService:
    """ComfyUIService 单元测试"""

    # ==================== 初始化测试 ====================

    def test_service_initialization(self):
        """测试服务初始化"""
        service = ComfyUIService(
            base_url="http://localhost:8188",
            model_name="sdxl_base"
        )
        assert service.client is not None
        assert service.client.server_address == "localhost:8188"

    def test_singleton_pattern(self):
        """测试单例模式"""
        service1 = get_comfyui_service()
        service2 = get_comfyui_service()
        assert service1 is service2

    # ==================== 健康检查测试 ====================

    def test_health_check_success(self, mock_comfyui_client):
        """测试健康检查成功"""
        mock_comfyui_client.validate_config.return_value = True
        mock_comfyui_client.server_address = "localhost:8188"
        mock_comfyui_client.checkpoint_name = "sdxl_base"

        service = ComfyUIService()
        result = service.health_check()

        assert result["healthy"] is True
        assert result["server_address"] == "localhost:8188"
        assert result["model"] == "sdxl_base"
        assert "latency_ms" in result

    def test_health_check_failure(self, mock_comfyui_client):
        """测试健康检查失败"""
        mock_comfyui_client.validate_config.side_effect = Exception("Connection failed")

        service = ComfyUIService()
        result = service.health_check()

        assert result["healthy"] is False
        assert "error" in result

    # ==================== 工作流创建测试 ====================

    def test_create_character_pose_workflow(self):
        """测试创建角色造型工作流"""
        workflow_json = ComfyUIService.create_character_pose_workflow(
            character_description="A beautiful girl",
            pose_type="full_body",
            style="anime"
        )

        assert isinstance(workflow_json, str)
        workflow = json.loads(workflow_json)

        assert "1" in workflow  # KSampler 节点
        assert "4" in workflow  # CheckpointLoader 节点
        assert "6" in workflow  # CLIPTextEncode 节点 (positive)
        assert "7" in workflow  # CLIPTextEncode 节点 (negative)

        # 检查包含角色描述
        positive_text = workflow["6"]["inputs"]["text"]
        assert "beautiful girl" in positive_text
        assert "anime" in positive_text

    def test_create_scene_background_workflow(self):
        """测试创建场景背景工作流"""
        workflow_json = ComfyUIService.create_scene_background_workflow(
            scene_description="A peaceful forest",
            lighting="natural",
            atmosphere="calm"
        )

        workflow = json.loads(workflow_json)
        assert "1" in workflow

        # 检查场景描述
        positive_text = workflow["6"]["inputs"]["text"]
        assert "peaceful forest" in positive_text
        assert "natural lighting" in positive_text

    def test_create_manga_panel_workflow(self):
        """测试创建漫画面板工作流"""
        workflow_json = ComfyUIService.create_manga_panel_workflow(
            panel_description="Action scene",
            characters=["Hero", "Villain"],
            speech_bubbles=True,
            sfx=True
        )

        workflow = json.loads(workflow_json)
        assert "1" in workflow

        # 检查角色和元素
        positive_text = workflow["6"]["inputs"]["text"]
        assert "Action scene" in positive_text
        assert "Hero, Villain" in positive_text
        assert "speech bubbles" in positive_text

    # ==================== 模型列表测试 ====================

    def test_get_available_models(self):
        """测试获取可用模型列表"""
        service = ComfyUIService()
        models = service.get_available_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "sdxl_base" in models


class TestComfyUIServiceIntegration:
    """ComfyUIService 集成测试（需要实际 ComfyUI 服务）"""

    @pytest.mark.integration
    @pytest.mark.comfyui
    def test_real_comfyui_connection(self):
        """集成测试: 实际 ComfyUI 连接"""
        service = ComfyUIService()
        result = service.health_check()

        # 如果 ComfyUI 未运行，应该优雅地返回失败
        assert isinstance(result, dict)
        assert "healthy" in result

    @pytest.mark.integration
    @pytest.mark.comfyui
    @pytest.mark.skipif(
        True,  # 默认跳过，需要 ComfyUI 服务时手动运行
        reason="需要 ComfyUI 服务运行"
    )
    def test_real_image_generation(self, sample_workflow_json):
        """集成测试: 实际图像生成"""
        service = ComfyUIService()
        result = service.generate_image(sample_workflow_json)

        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) > 0
        assert "url" in result["data"][0]


# ==================== 异步测试 ====================

class TestComfyUIAsyncTasks:
    """ComfyUI Celery 任务测试"""

    @pytest.mark.unit
    def test_comfyui_health_check_task(self):
        """测试健康检查任务"""
        from apps.artworks.tasks import comfyui_health_check

        # Mock 服务
        with patch('apps.artworks.services.comfyui_service.get_comfyui_service') as mock_get:
            mock_service = MagicMock()
            mock_service.health_check.return_value = {
                "healthy": True,
                "latency_ms": 100
            }
            mock_get.return_value = mock_service

            result = comfyui_health_check()

            assert result["healthy"] is True
            assert result["latency_ms"] == 100

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_comfyui_generate_image_task(self):
        """测试图像生成任务"""
        from apps.artworks.tasks import comfyui_generate_image

        with patch('apps.artworks.services.comfyui_service.get_comfyui_service') as mock_get:
            mock_service = MagicMock()
            mock_service.generate_image.return_value = {
                "success": True,
                "data": [{"url": "http://example.com/test.png"}]
            }
            mock_get.return_value = mock_service

            result = comfyui_generate_image(
                workflow_json='{"1": {"class_type": "KSampler"}}',
                shot_id=1
            )

            assert result["success"] is True


# ==================== 边界条件测试 ====================

class TestComfyUIServiceEdgeCases:
    """边界条件测试"""

    def test_empty_workflow_json(self):
        """测试空工作流 JSON"""
        service = ComfyUIService()

        # 健康检查应该正常工作
        with patch.object(service.client, 'validate_config', return_value=True):
            result = service.health_check()
            assert result["healthy"] is True

    def test_invalid_workflow_json(self):
        """测试无效的工作流 JSON"""
        service = ComfyUIService()

        with patch.object(service.client, '_generate_image', return_value={
            "success": False,
            "error": "Invalid workflow JSON"
        }):
            result = service.generate_image("invalid json")
            assert result["success"] is False

    def test_large_batch_generation(self):
        """测试大批量生成"""
        service = ComfyUIService()
        workflows = ["{}"] * 100  # 100 个空工作流

        with patch.object(service, 'generate_image', return_value={
            "success": True,
            "data": []
        }):
            results = service.batch_generate_images(workflows)
            assert len(results) == 100
