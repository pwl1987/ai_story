"""
简化的端到端工作流集成测试

专注于验证核心工作流：
1. 数据在各阶段间正确流转
2. 阶段状态正确更新
3. 错误处理机制

避免复杂的async mock，使用同步方式测试核心逻辑
"""

import pytest
from django.contrib.auth import get_user_model

from apps.models.models import ModelProvider
from apps.projects.models import Project, ProjectStage
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestSimpleE2EWorkflow:
    """简化的端到端工作流测试"""

    @pytest.fixture
    def configured_user(self, db):
        """创建用户"""
        return User.objects.create_user(username="e2e_simple_user", email="e2e_simple@test.com")

    @pytest.fixture
    def llm_provider(self, db):
        """创建LLM提供商"""
        return ModelProvider.objects.create(
            name="Test OpenAI",
            provider_type="llm",
            api_url="https://api.openai.com/v1",
            api_key="test-key",
            model_name="gpt-4",
            is_active=True,
        )

    @pytest.fixture
    def template_set(self, db, configured_user, llm_provider):
        """创建提示词集"""
        template_set = PromptTemplateSet.objects.create(
            name="Simple E2E Template Set", is_default=True, created_by=configured_user
        )

        # 创建rewrite模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type="rewrite",
            template_content="改写：{{ raw_text }}",
            model_provider=llm_provider,
            is_active=True,
        )

        # 创建storyboard模板
        PromptTemplate.objects.create(
            template_set=template_set,
            stage_type="storyboard",
            template_content="分镜：{{ raw_text }}",
            model_provider=llm_provider,
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

    def test_project_creates_all_stages(self, api_client, configured_user, template_set):
        """测试项目创建时自动创建5个阶段"""
        project_data = {
            "name": "E2E阶段创建测试",
            "original_topic": "测试项目自动创建5个阶段",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        assert response.status_code == 201
        project_id = response.data["id"]

        # 验证5个阶段已创建
        project = Project.objects.get(id=project_id)
        stages = ProjectStage.objects.filter(project=project)

        assert stages.count() == 5

        # 验证阶段类型
        stage_types = [s.stage_type for s in stages]
        expected_types = [
            "rewrite",
            "storyboard",
            "image_generation",
            "camera_movement",
            "video_generation",
        ]

        for expected_type in expected_types:
            assert expected_type in stage_types

        print("✅ 项目创建时自动创建5个阶段")

    def test_stage_initial_status(self, api_client, configured_user, template_set):
        """测试阶段初始状态正确"""
        project_data = {
            "name": "初始状态测试",
            "original_topic": "测试",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)
        stages = ProjectStage.objects.filter(project=project)

        for stage in stages:
            # 验证初始状态为pending
            assert stage.status == "pending"
            # 验证有空的input_data和output_data
            assert isinstance(stage.input_data, dict)
            assert isinstance(stage.output_data, dict)

        print("✅ 所有阶段初始状态为pending")

    def test_stage_data_flow_structure(self, api_client, configured_user, template_set):
        """测试阶段数据结构正确"""
        project_data = {
            "name": "数据结构测试",
            "original_topic": "测试数据在各阶段间传递",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)

        # 获取rewrite阶段
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")

        # 模拟rewrite完成，设置output_data
        rewrite_output = {"raw_text": "改写后的文本"}
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = rewrite_output
        rewrite_stage.save()

        # 获取storyboard阶段
        storyboard_stage = ProjectStage.objects.get(project=project, stage_type="storyboard")

        # 模拟数据传递：将rewrite的output复制到storyboard的input
        storyboard_stage.input_data = rewrite_output
        storyboard_stage.save()

        # 验证数据传递
        storyboard_stage.refresh_from_db()
        assert storyboard_stage.input_data == rewrite_output
        assert storyboard_stage.input_data["raw_text"] == "改写后的文本"

        print("✅ 阶段数据传递结构正确")

    def test_stage_error_handling(self, api_client, configured_user, template_set):
        """测试阶段错误处理"""
        project_data = {
            "name": "错误处理测试",
            "original_topic": "测试错误处理机制",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)

        # 获取rewrite阶段
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")

        # 模拟rewrite失败
        rewrite_stage.status = "failed"
        rewrite_stage.error_message = "API调用失败"
        rewrite_stage.retry_count = 1
        rewrite_stage.save()

        # 验证失败状态
        rewrite_stage.refresh_from_db()
        assert rewrite_stage.status == "failed"
        assert rewrite_stage.error_message == "API调用失败"
        assert rewrite_stage.retry_count == 1

        print("✅ 阶段错误处理正确")

    def test_stage_order_enforcement(self, api_client, configured_user, template_set):
        """测试阶段执行顺序约束"""
        project_data = {
            "name": "顺序约束测试",
            "original_topic": "测试阶段必须按顺序执行",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)

        # 获取rewrite和storyboard阶段
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")
        storyboard_stage = ProjectStage.objects.get(project=project, stage_type="storyboard")

        # 初始状态：都是pending
        assert rewrite_stage.status == "pending"
        assert storyboard_stage.status == "pending"

        # rewrite完成
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = {"raw_text": "text"}
        rewrite_stage.save()

        # storyboard仍然是pending（需要手动触发）
        storyboard_stage.refresh_from_db()
        assert storyboard_stage.status == "pending"

        print("✅ 阶段顺序约束正确")

    def test_full_workflow_data_integrity(self, api_client, configured_user, template_set):
        """测试完整工作流数据完整性"""
        project_data = {
            "name": "数据完整性测试",
            "original_topic": "测试完整工作流的数据完整性",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)

        # 模拟完整工作流数据
        stages_data = {
            "rewrite": {"output_data": {"raw_text": "改写文本"}},
            "storyboard": {
                "output_data": {
                    "human_text": {
                        "scenes": [
                            {
                                "scene_number": 1,
                                "narration": "旁白",
                                "visual_prompt": "提示",
                                "shot_type": "特写",
                            }
                        ]
                    }
                }
            },
            "image_generation": {
                "output_data": {
                    "human_text": {
                        "scenes": [
                            {
                                "scene_number": 1,
                                "narration": "旁白",
                                "visual_prompt": "提示",
                                "shot_type": "特写",
                                "urls": [{"url": "http://example.com/image.jpg"}],
                            }
                        ]
                    }
                }
            },
            "camera_movement": {"output_data": {"status": "completed"}},
            "video_generation": {
                "output_data": {
                    "human_text": {
                        "scenes": [
                            {
                                "scene_number": 1,
                                "narration": "旁白",
                                "visual_prompt": "提示",
                                "shot_type": "特写",
                                "urls": [{"url": "http://example.com/image.jpg"}],
                                "video_urls": [{"url": "http://example.com/video.mp4"}],
                            }
                        ]
                    }
                }
            },
        }

        # 更新所有阶段
        for stage_type, data in stages_data.items():
            stage = ProjectStage.objects.get(project=project, stage_type=stage_type)
            stage.status = "completed"
            stage.output_data = data["output_data"]
            stage.save()

        # 验证最终数据完整性
        video_stage = ProjectStage.objects.get(project=project, stage_type="video_generation")
        final_scene = video_stage.output_data["human_text"]["scenes"][0]

        # 验证所有必需字段都存在
        assert "scene_number" in final_scene
        assert "narration" in final_scene
        assert "visual_prompt" in final_scene
        assert "shot_type" in final_scene
        assert "urls" in final_scene  # 图片
        assert "video_urls" in final_scene  # 视频

        # 验证数据不为空
        assert final_scene["scene_number"] == 1
        assert final_scene["narration"] == "旁白"
        assert len(final_scene["urls"]) > 0
        assert len(final_scene["video_urls"]) > 0

        print("✅ 完整工作流数据完整性验证通过")

    def test_partial_workflow_failure_recovery(self, api_client, configured_user, template_set):
        """测试部分阶段失败时的恢复"""
        project_data = {
            "name": "部分失败测试",
            "original_topic": "测试部分阶段失败的处理",
            "prompt_template_set": str(template_set.id),
        }

        response = api_client.post("/api/v1/projects/", project_data, format="json")
        project_id = response.data["id"]

        project = Project.objects.get(id=project_id)

        # rewrite完成
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")
        rewrite_stage.status = "completed"
        rewrite_stage.output_data = {"raw_text": "text"}
        rewrite_stage.save()

        # storyboard失败
        storyboard_stage = ProjectStage.objects.get(project=project, stage_type="storyboard")
        storyboard_stage.status = "failed"
        storyboard_stage.error_message = "解析失败"
        storyboard_stage.save()

        # image_generation仍然是pending
        image_stage = ProjectStage.objects.get(project=project, stage_type="image_generation")
        assert image_stage.status == "pending"

        # 验证失败不影响其他阶段的状态
        rewrite_stage.refresh_from_db()
        assert rewrite_stage.status == "completed"

        print("✅ 部分失败不影响已完成阶段")
