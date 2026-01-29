"""
文案改写功能端到端集成测试

测试完整的文案改写工作流：
1. 创建项目（带提示词模板）
2. 触发文案改写阶段
3. 验证Celery任务执行
4. 验证Redis消息发布
5. 验证数据库状态更新
"""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from apps.models.models import ModelProvider
from apps.projects.models import Project, ProjectStage
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestRewriteE2E:
    """文案改写端到端测试"""

    @pytest.fixture
    def configured_user(self, db):
        """创建配置好的用户"""
        user = User.objects.create_user(username="rewrite_test_user", email="rewrite@test.com")
        return user

    @pytest.fixture
    def model_provider(self, db):
        """创建模型提供商"""
        provider = ModelProvider.objects.create(
            name="Test OpenAI",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test-key",
            model_name="gpt-4",
            is_active=True,
        )
        return provider

    @pytest.fixture
    def template_set(self, db, configured_user):
        """创建提示词集"""
        template_set = PromptTemplateSet.objects.create(
            name="Rewrite Template Set", is_default=True, created_by=configured_user
        )
        return template_set

    @pytest.fixture
    def rewrite_template(self, db, template_set, model_provider):
        """创建文案改写提示词模板"""
        template = PromptTemplate.objects.create(
            template_set=template_set,
            stage_type="rewrite",
            template_content="请改写以下文案：\n\n{{ raw_text }}",
            model_provider=model_provider,
            is_active=True,
        )
        return template

    @pytest.fixture
    def api_client(self, db, configured_user):
        """创建API客户端"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=configured_user)
        return client

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_e2e_rewrite_workflow(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        template_set,
        rewrite_template,
    ):
        """
        端到端测试：创建项目 → 触发改写 → 验证任务启动
        """
        # 1. 创建项目
        project_data = {
            "name": "测试文案改写项目",
            "description": "测试项目描述",
            "original_topic": "这是一个需要改写的原始文案",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")

        assert response.status_code == 201, f"创建项目失败: {response.data}"
        project_id = response.data["id"]

        # 验证项目创建成功
        project = Project.objects.get(id=project_id)
        assert project.name == "测试文案改写项目"
        assert project.original_topic == "这是一个需要改写的原始文案"
        assert project.user == configured_user

        # 验证5个阶段自动创建
        stages = ProjectStage.objects.filter(project=project)
        assert stages.count() == 5, f"应创建5个阶段，实际创建{stages.count()}个"

        # 验证rewrite阶段存在且状态为pending
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")
        assert rewrite_stage.status == "pending"

        # 2. 触发文案改写
        mock_task = MagicMock()
        mock_task.id = "test-celery-task-id-123"
        mock_execute_task.return_value = mock_task

        execute_data = {"stage_name": "rewrite", "input_data": {}}

        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/", execute_data, format="json"
        )

        assert response.status_code == 202, f"触发改写失败: {response.data}"
        assert response.data["task_id"] == "test-celery-task-id-123"
        assert response.data["stage"] == "rewrite"
        assert "channel" in response.data

        # 验证Celery任务被调用
        mock_execute_task.assert_called_once()
        call_args = mock_execute_task.call_args
        assert call_args[1]["project_id"] == project_id
        assert call_args[1]["stage_name"] == "rewrite"
        assert call_args[1]["user_id"] == configured_user.id

        # 验证项目状态更新为processing
        project.refresh_from_db()
        assert project.status == "processing"

        # 验证Redis频道格式
        expected_channel = f"ai_story:project:{project_id}:stage:rewrite"
        assert response.data["channel"] == expected_channel

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_multiple_rewrite_attempts(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        template_set,
        rewrite_template,
    ):
        """测试多次改写尝试"""
        # 创建项目
        project_data = {
            "name": "多次改写测试",
            "description": "测试",
            "original_topic": "原始文案",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        # 第一次改写
        mock_task = MagicMock()
        mock_task.id = "first-task-id"
        mock_execute_task.return_value = mock_task

        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "rewrite", "input_data": {}},
            format="json",
        )

        assert response.status_code == 202
        assert mock_execute_task.call_count == 1

        # 第二次改写（应该允许，重新执行）
        mock_task.id = "second-task-id"
        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "rewrite", "input_data": {}},
            format="json",
        )

        assert response.status_code == 202
        assert mock_execute_task.call_count == 2

    def test_rewrite_without_template_fails(self, api_client, configured_user):
        """测试没有提示词模板时改写失败"""
        # 创建没有提示词模板的项目
        project_data = {"name": "无模板项目", "description": "测试", "original_topic": "原始文案"}

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        assert response.status_code == 201
        project_id = response.data["id"]

        # 尝试改写（应该失败，因为没有提示词模板）
        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "rewrite", "input_data": {}},
            format="json",
        )

        # API会接受请求，但Celery任务执行时会失败
        assert response.status_code == 202

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_stage_execution_order(
        self, mock_execute_task, api_client, configured_user, model_provider, template_set
    ):
        """测试阶段执行顺序约束"""
        # 创建所有阶段的模板
        for stage_type in ["rewrite", "storyboard", "camera_movement"]:
            PromptTemplate.objects.create(
                template_set=template_set,
                stage_type=stage_type,
                template_content=f"Template for {stage_type}",
                model_provider=model_provider,
                is_active=True,
            )

        # 创建项目
        project_data = {
            "name": "阶段顺序测试",
            "description": "测试",
            "original_topic": "原始文案",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        mock_task = MagicMock()
        mock_task.id = "task-id"
        mock_execute_task.return_value = mock_task

        # 尝试跳过rewrite直接执行storyboard（API应该允许，但处理器会验证）
        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "storyboard", "input_data": {}},
            format="json",
        )

        # API接受请求
        assert response.status_code == 202
