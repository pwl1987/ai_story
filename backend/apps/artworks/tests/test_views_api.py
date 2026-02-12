"""
API 视图测试 (Story 10.3/10.4)

测试覆盖:
- ComfyUIViewSet API
- ScriptParserViewSet API
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestComfyUIViewSet:
    """ComfyUI API ViewSet 测试"""

    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        client = APIClient()
        # 创建测试用户并认证
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_authenticate(user=user)
        return client

    def test_health_check(self, api_client):
        """测试健康检查端点"""
        with patch('apps.artworks.services.comfyui_service.get_comfyui_service') as mock_get:
            mock_service = MagicMock()
            mock_service.health_check.return_value = {
                "healthy": True,
                "latency_ms": 100,
                "server_address": "localhost:8188"
            }
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/comfyui/health/"
            response = api_client.get(url)

            assert response.status_code == 200
            assert response.data["healthy"] is True

    def test_get_models(self, api_client):
        """测试获取模型列表"""
        with patch('apps.artworks.services.comfyui_service.get_comfyui_service') as mock_get:
            mock_service = MagicMock()
            mock_service.get_available_models.return_value = [
                "sdxl_base", "sd1.5_base"
            ]
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/comfyui/models/"
            response = api_client.get(url)

            assert response.status_code == 200
            assert "models" in response.data

    def test_generate_image_success(self, api_client):
        """测试图像生成成功"""
        with patch('apps.artworks.services.comfyui_service.get_comfyui_service') as mock_get:
            mock_service = MagicMock()
            mock_service.generate_image.return_value = {
                "success": True,
                "data": [{"url": "http://example.com/test.png"}]
            }
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/comfyui/generate_image/"
            data = {"workflow_json": '{"1": {"class_type": "KSampler"}}'}
            response = api_client.post(url, data, format="json")

            assert response.status_code == 200
            assert response.data["success"] is True

    def test_generate_image_missing_workflow(self, api_client):
        """测试缺少工作流参数"""
        url = "/api/v1/artworks/comfyui/generate_image/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestScriptParserViewSet:
    """脚本解析 API ViewSet 测试"""

    @pytest.fixture
    def api_client(self):
        """创建 API 客户端"""
        client = APIClient()
        user = User.objects.create_user(username="testuser", password="testpass")
        client.force_authenticate(user=user)
        return client

    def test_health_check(self, api_client):
        """测试健康检查"""
        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            # Mock the LLM client to return a successful response
            mock_llm_response = MagicMock()
            mock_llm_response.success = True

            mock_llm_client = MagicMock()
            mock_llm_client.model_name = "llama2"
            mock_llm_client.generate = AsyncMock(return_value=mock_llm_response)

            mock_service = MagicMock()
            mock_service.llm_client = mock_llm_client
            mock_service.temperature = 0.7
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/parser/health/"
            response = api_client.get(url)

            assert response.status_code == 200
            assert response.data["healthy"] is True

    def test_parse_script_success(self, api_client, sample_script_text):
        """测试解析脚本成功"""
        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            mock_service.parse_script.return_value = {
                "success": True,
                "chapters": [],
                "characters": [],
                "scenes": [],
                "items": [],
                "summary": "测试概要"
            }
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/parser/parse/"
            data = {"script_text": sample_script_text}
            response = api_client.post(url, data, format="json")

            assert response.status_code == 200
            assert response.data["success"] is True

    def test_parse_script_missing_text(self, api_client):
        """测试缺少脚本文本"""
        url = "/api/v1/artworks/parser/parse/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == 400

    def test_extract_characters(self, api_client, sample_script_text):
        """测试提取角色"""
        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            mock_service._extract_characters.return_value = [
                {"name": "张三", "display_name": "张三"}
            ]
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/parser/characters/"
            data = {"script_text": sample_script_text}
            response = api_client.post(url, data, format="json")

            assert response.status_code == 200
            assert len(response.data["characters"]) > 0

    def test_recommend_poses(self, api_client):
        """测试造型推荐"""
        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            mock_service.analyze_character_poses.return_value = {
                "success": True,
                "recommendations": [
                    {"pose_type": "casual", "confidence": 0.8}
                ]
            }
            mock_get.return_value = mock_service

            url = "/api/v1/artworks/parser/recommend_poses/"
            data = {"character_description": "一个活泼的女孩"}
            response = api_client.post(url, data, format="json")

            assert response.status_code == 200
            assert response.data["success"] is True


# ==================== 认证测试 ====================

@pytest.mark.django_db
class TestAPIAuthentication:
    """API 认证测试"""

    def test_unauthenticated_request(self):
        """测试未认证请求"""
        client = APIClient()  # 不认证
        url = "/api/v1/artworks/comfyui/health/"

        response = client.get(url)

        # 未认证应该返回 401 或 403
        assert response.status_code in [401, 403]
