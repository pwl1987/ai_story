"""
工作流控制 API 测试 (Story 12-4)

测试工作流控制 API 的各种场景:
- 启动工作流
- 暂停工作流
- 继续工作流
- 状态查询
- 权限控制
- 错误处理
"""

import uuid
import pytest
from unittest.mock import patch, Mock
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from apps.artworks.models import ChapterWorkflow, WorkflowEvent, ScriptScene, Chapter, Artwork


class TestWorkflowControlAPI(APITransactionTestCase):
    """
    工作流控制 API 测试套件 (Story 12-4)

    使用 APITransactionTestCase 确保 Celery 任务隔离。
    """

    def setUp(self):
        """测试数据初始化"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # 创建测试用户
        self.user = User.objects.create_user(
            username="test_user",
            password="test123"
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            password="test123"
        )

        # 创建作品和章节（Chapter 属于 Artwork 应用）
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="novel"
        )
        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            title="测试章节",
            chapter_number=1
        )

        # 创建3个场景
        for i in range(3):
            ScriptScene.objects.create(
                chapter=self.chapter,
                scene_name=f"场景{i+1}",
                scene_number=i+1
            )

        # 使用 APIClient 并认证
        self.client.force_authenticate(user=self.user)

    # ========== 启动工作流测试 ==========

    @patch("apps.artworks.tasks.start_chapter_workflow_task.delay")
    def test_start_workflow_creates_pending_entry(self, mock_delay):
        """测试启动工作流创建 PENDING 状态记录"""
        # Mock Celery 任务返回
        mock_task = Mock()
        mock_task.id = str(uuid.uuid4())
        mock_delay.return_value = mock_task

        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/start-workflow/")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("workflow_id", response.data)

        # 验证 Celery 任务被调用
        mock_delay.assert_called_once()

        # 验证数据库记录
        workflow = ChapterWorkflow.objects.get(workflow_id=response.data["workflow_id"])
        self.assertEqual(workflow.status, ChapterWorkflow.Status.PENDING.value)
        self.assertEqual(workflow.total_scenes, 3)
        self.assertIsNotNone(workflow.celery_task_id)

    @patch("apps.artworks.tasks.start_chapter_workflow_task.delay")
    def test_start_workflow_creates_start_event(self, mock_delay):
        """测试启动工作流记录事件"""
        # Mock Celery 任务返回
        mock_task = Mock()
        mock_task.id = str(uuid.uuid4())
        mock_delay.return_value = mock_task

        self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/start-workflow/")

        event = WorkflowEvent.objects.filter(
            event_type=WorkflowEvent.EventType.WORKFLOW_STARTED
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.message, "工作流已启动")

    @patch("apps.artworks.tasks.start_chapter_workflow_task.delay")
    def test_start_workflow_fails_with_running_workflow(self, mock_delay):
        """测试已有运行中工作流时启动失败"""
        # 创建一个运行中的工作流
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING.value
        )

        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/start-workflow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已有运行中的工作流", response.data["error"])

    @patch("apps.artworks.tasks.start_chapter_workflow_task.delay")
    def test_start_workflow_fails_with_no_scenes(self, mock_delay):
        """测试无场景章节启动失败"""
        # 创建空场景的章节
        empty_chapter = Chapter.objects.create(
            artwork=self.artwork,
            title="空章节",
            chapter_number=2
        )

        response = self.client.post(f"/api/v1/artworks/chapters/{empty_chapter.id}/start-workflow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("没有可处理的场景", response.data["error"])

    # ========== 暂停工作流测试 ==========

    def test_pause_workflow_transitions_to_paused(self):
        """测试暂停工作流状态转换"""
        # 创建运行中的工作流（不创建 celery_task_id，避免 UUID 验证错误）
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING.value
        )

        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/pause-workflow/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.PAUSED.value)

    def test_pause_workflow_fails_with_no_running_workflow(self):
        """测试无运行中工作流时暂停失败"""
        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/pause-workflow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("没有运行中的工作流", response.data["error"])

    # ========== 继续工作流测试 ==========

    @patch("apps.artworks.tasks.resume_chapter_workflow_task.delay")
    def test_resume_workflow_creates_new_task(self, mock_delay):
        """测试继续工作流创建新任务"""
        # Mock Celery 任务返回
        mock_task = Mock()
        mock_task.id = str(uuid.uuid4())
        mock_delay.return_value = mock_task

        # 创建暂停的工作流（不创建 celery_task_id，避免 UUID 验证错误）
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.PAUSED.value
        )

        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/resume-workflow/")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.RUNNING.value)
        self.assertIsNotNone(workflow.celery_task_id)

    @patch("apps.artworks.tasks.resume_chapter_workflow_task.delay")
    def test_resume_workflow_fails_with_no_paused_workflow(self, mock_delay):
        """测试无暂停工作流时继续失败"""
        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/resume-workflow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("没有暂停的工作流", response.data["error"])

    # ========== 状态查询测试 ==========

    def test_workflow_status_returns_latest(self):
        """测试状态查询返回最新工作流"""
        # 创建多个工作流
        old_workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.COMPLETED.value
        )
        new_workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING.value
        )

        response = self.client.get(f"/api/v1/artworks/chapters/{self.chapter.id}/workflow-status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["workflow_id"], str(new_workflow.workflow_id))

    def test_workflow_status_includes_display_fields(self):
        """测试状态响应包含显示字段"""
        # 创建工作流
        ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING.value
        )

        response = self.client.get(f"/api/v1/artworks/chapters/{self.chapter.id}/workflow-status/")

        self.assertIn("status_display", response.data)
        self.assertEqual(response.data["status_display"], "运行中")

    # ========== 权限控制测试 ==========

    @patch("apps.artworks.tasks.start_chapter_workflow_task.delay")
    def test_unauthenticated_user_cannot_access_api(self, mock_delay):
        """测试未认证用户无法访问 API"""
        self.client.force_authenticate(user=None)

        response = self.client.post(f"/api/v1/artworks/chapters/{self.chapter.id}/start-workflow/")

        # 未认证用户应返回 401 或 403
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
