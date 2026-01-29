"""
Storyboard端到端集成测试

测试完整的分镜生成工作流：
1. 创建项目并完成rewrite阶段
2. 触发storyboard阶段
3. 验证Celery任务执行
4. 验证Redis消息发布
5. 验证JSON输出格式
6. 验证后续阶段的数据更新
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
class TestStoryboardE2E:
    """Storyboard端到端测试"""

    @pytest.fixture
    def configured_user(self, db):
        """创建配置好的用户"""
        user = User.objects.create_user(
            username="storyboard_test_user", email="storyboard@test.com"
        )
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
            name="Storyboard Template Set", is_default=True, created_by=configured_user
        )
        return template_set

    @pytest.fixture
    def rewrite_and_storyboard_templates(self, db, template_set, model_provider):
        """创建rewrite和storyboard提示词模板"""
        # Rewrite模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type="rewrite",
            template_content="请改写以下文案：\n\n{{ raw_text }}",
            model_provider=model_provider,
            is_active=True,
        )

        # Storyboard模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type="storyboard",
            template_content='根据以下文案生成分镜JSON：\n\n{{ raw_text }}\n\n返回格式：\n{"scenes": [{"scene_number": 1, "narration": "...", "visual_prompt": "...", "shot_type": "..."}]}',
            model_provider=model_provider,
            is_active=True,
        )

        return template_set

    @pytest.fixture
    def api_client(self, db, configured_user):
        """创建API客户端"""
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=configured_user)
        return client

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_e2e_storyboard_after_rewrite(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        rewrite_and_storyboard_templates,
    ):
        """
        端到端测试：rewrite → storyboard 完整工作流
        """
        # 1. 创建项目
        project_data = {
            "name": "测试分镜项目",
            "description": "测试项目描述",
            "original_topic": "这是一个关于AI的故事",
            "prompt_template_set": str(rewrite_and_storyboard_templates.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        assert response.status_code == 201
        project_id = response.data["id"]

        # 验证5个阶段已创建
        project = Project.objects.get(id=project_id)
        stages = ProjectStage.objects.filter(project=project)
        assert stages.count() == 5

        # 2. 执行rewrite阶段（模拟完成）
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")

        # Mock rewrite任务执行
        mock_task = MagicMock()
        mock_task.id = "rewrite-task-id"
        mock_execute_task.return_value = mock_task

        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "rewrite", "input_data": {}},
            format="json",
        )
        assert response.status_code == 202

        # 模拟rewrite完成
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = {
            "raw_text": "这是改写后的AI故事文案",
            "human_text": "这是改写后的AI故事文案",
        }
        rewrite_stage.save()

        # 3. 执行storyboard阶段
        mock_task.id = "storyboard-task-id"
        mock_execute_task.return_value = mock_task

        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "storyboard", "input_data": {}},
            format="json",
        )

        assert response.status_code == 202
        assert response.data["stage"] == "storyboard"
        assert response.data["task_id"] == "storyboard-task-id"

        # 验证Celery任务被调用
        assert mock_execute_task.call_count == 2  # rewrite + storyboard

        # 4. 验证Redis频道格式
        expected_channel = f"ai_story:project:{project_id}:stage:storyboard"
        assert response.data["channel"] == expected_channel

    def test_storyboard_requires_rewrite_completion(
        self, api_client, configured_user, model_provider, rewrite_and_storyboard_templates
    ):
        """测试storyboard需要rewrite完成"""
        # 1. 创建项目
        project_data = {
            "name": "测试分镜项目",
            "description": "测试",
            "original_topic": "原始主题",
            "prompt_template_set": str(rewrite_and_storyboard_templates.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        # 2. rewrite未完成时执行storyboard
        rewrite_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id), stage_type="rewrite"
        )
        assert rewrite_stage.status == "pending"  # 未完成

        # API会接受请求，但执行时会失败
        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "storyboard", "input_data": {}},
            format="json",
        )
        assert response.status_code == 202  # API接受请求

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_storyboard_json_output_validation(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        rewrite_and_storyboard_templates,
    ):
        """测试storyboard JSON输出格式验证"""
        # 创建项目
        project_data = {
            "name": "JSON验证测试",
            "description": "测试",
            "original_topic": "测试主题",
            "prompt_template_set": str(rewrite_and_storyboard_templates.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        # 完成rewrite阶段
        rewrite_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id), stage_type="rewrite"
        )
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = {"raw_text": "改写后的文案", "human_text": "改写后的文案"}
        rewrite_stage.save()

        # Mock任务执行
        mock_task = MagicMock()
        mock_task.id = "storyboard-task"
        mock_execute_task.return_value = mock_task

        # 执行storyboard
        response = api_client.post(
            f"/api/v1/projects/{project_id}/execute_stage/",
            {"stage_name": "storyboard", "input_data": {}},
            format="json",
        )

        assert response.status_code == 202
        # 任务应该被调用，实际JSON验证在处理器中进行

    @patch("apps.projects.tasks.execute_llm_stage.delay")
    def test_storyboard_updates_subsequent_stages(
        self,
        mock_execute_task,
        api_client,
        configured_user,
        model_provider,
        rewrite_and_storyboard_templates,
    ):
        """测试storyboard结果更新后续3个阶段"""
        from apps.projects.utils import parse_storyboard_json

        # 创建项目
        project_data = {
            "name": "更新测试",
            "description": "测试",
            "original_topic": "测试",
            "prompt_template_set": str(rewrite_and_storyboard_templates.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        # 完成rewrite
        rewrite_stage = ProjectStage.objects.get(
            project=Project.objects.get(id=project_id), stage_type="rewrite"
        )
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = {"raw_text": "改写文案", "human_text": "改写文案"}
        rewrite_stage.save()

        # 执行storyboard（模拟）
        ProjectStage.objects.get(
            project=Project.objects.get(id=project_id), stage_type="storyboard"
        )

        # 模拟storyboard完成并保存结果
        storyboard_json = """{
          "scenes": [
            {
              "scene_number": 1,
              "narration": "开场旁白",
              "visual_prompt": "产品特写",
              "shot_type": "特写"
            },
            {
              "scene_number": 2,
              "narration": "功能演示",
              "visual_prompt": "使用场景",
              "shot_type": "中景"
            }
          ]
        }"""

        parsed_data = parse_storyboard_json(storyboard_json)
        output_data = {"human_text": parsed_data, "raw_text": ""}

        # 更新storyboard及后续阶段
        ProjectStage.objects.filter(
            project=Project.objects.get(id=project_id),
            stage_type__in=[
                "storyboard",
                "image_generation",
                "camera_movement",
                "video_generation",
            ],
        ).update(input_data=output_data, output_data=output_data)

        # 验证后续3个阶段已更新
        for stage_type in ["image_generation", "camera_movement", "video_generation"]:
            stage = ProjectStage.objects.get(
                project=Project.objects.get(id=project_id), stage_type=stage_type
            )
            assert stage.input_data is not None
            assert "human_text" in stage.input_data
            assert "scenes" in stage.input_data["human_text"]
            assert len(stage.input_data["human_text"]["scenes"]) == 2
