"""
TODO功能单元测试
测试pause、resume、save_as_template、export action
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.content.models import CameraMovement, GeneratedVideo, Storyboard
from apps.projects.tests.factories import ProjectFactory, UserFactory
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


@pytest.mark.django_db
class TestPauseAction:
    """测试pause action"""

    @pytest.fixture
    def project(self):
        """创建测试项目"""
        user = UserFactory()
        project = ProjectFactory(user=user, status="processing", original_topic="测试主题")
        return project

    def test_pause_success(self, project):
        """测试暂停成功"""
        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用pause API
        response = client.post(f"/api/v1/projects/{project.id}/pause/")

        assert response.status_code == 200
        data = response.json()

        # 验证返回数据
        assert "message" in data
        assert "cancelled_tasks" in data
        assert "project" in data

        # 验证项目状态已更新
        project.refresh_from_db()
        assert project.status == "paused"

    def test_pause_failure_invalid_status(self, project):
        """测试暂停失败：状态不是processing"""
        # 修改项目状态为completed
        project.status = "completed"
        project.save()

        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用pause API
        response = client.post(f"/api/v1/projects/{project.id}/pause/")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


@pytest.mark.django_db
class TestResumeAction:
    """测试resume action"""

    @pytest.fixture
    def project(self):
        """创建暂停的项目"""
        user = UserFactory()
        project = ProjectFactory(user=user, status="paused", original_topic="测试主题")
        return project

    def test_resume_success(self, project):
        """测试恢复成功"""
        client = APIClient()
        client.force_authenticate(user=project.user)

        # Mock resume_project_pipeline服务
        from apps.projects import services

        original_resume = services.resume_project_pipeline
        services.resume_project_pipeline = lambda project_id: {
            "task_id": "test-task-id",
            "next_stage": "rewrite",
            "status": "resumed",
        }

        try:
            # 调用resume API
            response = client.post(f"/api/v1/projects/{project.id}/resume/")

            assert response.status_code == 200
            data = response.json()

            # 验证返回数据
            assert "message" in data
            assert "task_id" in data
            assert "next_stage" in data
        finally:
            services.resume_project_pipeline = original_resume

    def test_resume_failure_invalid_status(self, project):
        """测试恢复失败：状态不是paused"""
        # 修改项目状态为processing
        project.status = "processing"
        project.save()

        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用resume API
        response = client.post(f"/api/v1/projects/{project.id}/resume/")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data


@pytest.mark.django_db
class TestSaveAsTemplateAction:
    """测试save_as_template action"""

    @pytest.fixture
    def project(self):
        """创建带提示词集的测试项目"""
        user = UserFactory()
        template_set = PromptTemplateSet.objects.create(
            name="测试提示词集", created_by=user, is_active=True
        )

        # 创建提示词模板
        for stage_type in ["rewrite", "storyboard", "image_generation"]:
            PromptTemplate.objects.create(
                template_set=template_set,
                stage_type=stage_type,
                template_content=f"Test {stage_type} template",
                is_active=True,
            )

        project = ProjectFactory(
            user=user, prompt_template_set=template_set, original_topic="测试主题"
        )
        return project

    def test_save_as_template_success(self, project):
        """测试保存为模板成功"""
        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用save_as_template API（使用下划线）
        response = client.post(
            f"/api/v1/projects/{project.id}/save_as_template/",
            {"template_name": "我的测试模板", "include_model_config": False},
            format="json",
        )

        assert response.status_code == 200
        data = response.json()

        # 验证返回数据
        assert "message" in data
        assert "template_name" in data
        assert data["template_name"] == "我的测试模板"
        assert "template_set_id" in data
        assert "templates_count" in data
        assert data["templates_count"] == 3  # rewrite, storyboard, image_generation

    def test_save_as_template_with_model_config(self, project):
        """测试保存为模板包含模型配置"""
        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用save_as_template API
        response = client.post(
            f"/api/v1/projects/{project.id}/save_as_template/",
            {"template_name": "带模型配置的模板", "include_model_config": True},
            format="json",
        )

        assert response.status_code == 200
        data = response.json()

        # 验证返回数据
        assert "message" in data
        assert "template_name" in data


@pytest.mark.django_db
class TestExportAction:
    """测试export action"""

    @pytest.fixture
    def project(self):
        """创建已完成的项目"""
        user = UserFactory()
        template_set = PromptTemplateSet.objects.create(
            name="测试提示词集", created_by=user, is_active=True
        )

        project = ProjectFactory(
            user=user,
            prompt_template_set=template_set,
            status="completed",
            original_topic="测试主题",
        )

        # 创建分镜、运镜和生成的视频
        storyboard1 = Storyboard.objects.create(
            project=project, sequence_number=1, scene_description="场景1"
        )
        storyboard2 = Storyboard.objects.create(
            project=project, sequence_number=2, scene_description="场景2"
        )

        # 创建运镜参数
        camera_movement1 = CameraMovement.objects.create(
            storyboard=storyboard1,
            movement_type="static",
            movement_params={"start_scale": 1.0, "end_scale": 1.0},
        )
        camera_movement2 = CameraMovement.objects.create(
            storyboard=storyboard2,
            movement_type="zoom_in",
            movement_params={"start_scale": 1.0, "end_scale": 1.2},
        )

        # 创建已生成的图片（用于视频）
        from apps.content.models import GeneratedImage

        image1 = GeneratedImage.objects.create(
            storyboard=storyboard1, image_url="http://example.com/image1.jpg"
        )
        image2 = GeneratedImage.objects.create(
            storyboard=storyboard2, image_url="http://example.com/image2.jpg"
        )

        # 创建已完成的视频
        GeneratedVideo.objects.create(
            storyboard=storyboard1,
            camera_movement=camera_movement1,
            image=image1,
            status="completed",
            video_url="http://example.com/video1.mp4",
        )
        GeneratedVideo.objects.create(
            storyboard=storyboard2,
            camera_movement=camera_movement2,
            image=image2,
            status="completed",
            video_url="http://example.com/video2.mp4",
        )

        return project

    def test_export_success(self, project):
        """测试导出成功"""
        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用export API
        response = client.post(
            f"/api/v1/projects/{project.id}/export/",
            {"include_subtitles": True, "video_format": "mp4"},
            format="json",
        )

        assert response.status_code == 200
        data = response.json()

        # 验证返回数据
        assert "message" in data
        assert "export_id" in data
        assert "video_count" in data
        assert data["video_count"] == 2

    def test_export_failure_invalid_status(self, project):
        """测试导出失败：项目未完成"""
        # 修改项目状态为processing
        project.status = "processing"
        project.save()

        client = APIClient()
        client.force_authenticate(user=project.user)

        # 调用export API
        response = client.post(
            f"/api/v1/projects/{project.id}/export/",
            {"include_subtitles": True, "video_format": "mp4"},
            format="json",
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
