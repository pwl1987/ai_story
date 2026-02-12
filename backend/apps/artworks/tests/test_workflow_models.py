"""
工作流模型单元测试 (Story 12-1.1)

测试范围:
- ChapterWorkflow 模型功能和状态转换
- WorkflowEvent 模型和事件记录
- 工作流生命周期管理
- 进度计算和统计
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.artworks.models import Artwork, Chapter, ChapterWorkflow, ScriptScene, WorkflowEvent


class ChapterWorkflowModelTest(TestCase):
    """ChapterWorkflow 模型测试"""

    def setUp(self):
        """创建测试数据"""
        # 创建测试章节
        self.artwork = Artwork.objects.create(title="测试作品", artwork_type="novel")
        self.chapter = Chapter.objects.create(
            artwork=self.artwork, chapter_number=1, title="第一章", original_text="测试内容"
        )

        # 创建测试场景
        self.scene1 = ScriptScene.objects.create(
            chapter=self.chapter, scene_number=1, scene_name="场景1", description="第一个场景"
        )
        self.scene2 = ScriptScene.objects.create(
            chapter=self.chapter, scene_number=2, scene_name="场景2", description="第二个场景"
        )
        self.scene3 = ScriptScene.objects.create(
            chapter=self.chapter, scene_number=3, scene_name="场景3", description="第三个场景"
        )

    def test_create_workflow(self):
        """测试创建工作流"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)

        self.assertIsNotNone(workflow.workflow_id)
        self.assertEqual(workflow.chapter, self.chapter)
        self.assertEqual(workflow.status, ChapterWorkflow.Status.PENDING)
        self.assertEqual(workflow.total_scenes, 0)
        self.assertEqual(workflow.completed_scenes, 0)
        self.assertEqual(workflow.progress_percentage, 0)

    def test_workflow_start(self):
        """测试启动工作流"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)

        workflow.start()

        workflow.refresh_from_db()

        self.assertEqual(workflow.status, ChapterWorkflow.Status.RUNNING)
        self.assertIsNotNone(workflow.started_at)
        self.assertTrue(workflow.is_active)

        # 检查是否创建了启动事件
        event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_STARTED
        ).first()
        self.assertIsNotNone(event)

    def test_workflow_pause(self):
        """测试暂停工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.RUNNING
        )

        workflow.pause()

        workflow.refresh_from_db()

        self.assertEqual(workflow.status, ChapterWorkflow.Status.PAUSED)
        self.assertTrue(workflow.is_active)

        # 检查是否创建了暂停事件
        event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_PAUSED
        ).first()
        self.assertIsNotNone(event)

    def test_workflow_pause_validation(self):
        """测试只有运行中的工作流可以暂停"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.PENDING
        )

        with self.assertRaises(ValueError) as cm:
            workflow.pause()

        self.assertIn("只有运行中的工作流可以暂停", str(cm.exception))

    def test_workflow_resume(self):
        """测试恢复工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.PAUSED
        )

        workflow.resume()

        workflow.refresh_from_db()

        self.assertEqual(workflow.status, ChapterWorkflow.Status.RUNNING)
        self.assertTrue(workflow.is_active)

        # 检查是否创建了恢复事件
        event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_RESUMED
        ).first()
        self.assertIsNotNone(event)

    def test_workflow_complete(self):
        """测试完成工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.RUNNING
        )

        workflow.complete()

        workflow.refresh_from_db()

        self.assertEqual(workflow.status, ChapterWorkflow.Status.COMPLETED)
        self.assertIsNotNone(workflow.completed_at)
        self.assertEqual(workflow.progress_percentage, 100)
        self.assertFalse(workflow.is_active)

        # 检查是否创建了完成事件
        event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_COMPLETED
        ).first()
        self.assertIsNotNone(event)

    def test_workflow_fail(self):
        """测试工作流失败"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.RUNNING
        )

        error_msg = "测试错误"
        workflow.fail(error_msg)

        workflow.refresh_from_db()

        self.assertEqual(workflow.status, ChapterWorkflow.Status.FAILED)
        self.assertEqual(workflow.error_message, error_msg)
        self.assertIsNotNone(workflow.completed_at)
        self.assertFalse(workflow.is_active)

        # 检查是否创建了失败事件
        event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_FAILED
        ).first()
        self.assertIsNotNone(event)

    def test_update_progress(self):
        """测试更新进度"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, total_scenes=3, status=ChapterWorkflow.Status.RUNNING
        )

        # 完成第一个场景
        workflow.completed_scenes = 1
        workflow.update_progress(current_scene=self.scene1)

        workflow.refresh_from_db()

        self.assertEqual(workflow.current_scene, self.scene1)
        self.assertEqual(workflow.progress_percentage, 33)  # 1/3 = 33%

    def test_elapsed_seconds(self):
        """测试计算已用时长"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.RUNNING
        )

        # 未启动的工作流
        self.assertEqual(workflow.elapsed_seconds, 0)

        # 启动工作流
        workflow.started_at = timezone.now()
        workflow.save()

        # 手动设置 completed_at 模拟完成
        workflow.completed_at = workflow.started_at + timedelta(hours=2, minutes=30)
        workflow.save()

        self.assertEqual(workflow.elapsed_seconds, 9000)  # 2h30m = 9000s


class WorkflowEventModelTest(TestCase):
    """WorkflowEvent 模型测试"""

    def setUp(self):
        """创建测试数据"""
        self.artwork = Artwork.objects.create(title="测试作品", artwork_type="novel")
        self.chapter = Chapter.objects.create(
            artwork=self.artwork, chapter_number=1, title="第一章", original_text="测试内容"
        )
        self.workflow = ChapterWorkflow.objects.create(chapter=self.chapter)
        self.scene = ScriptScene.objects.create(
            chapter=self.chapter, scene_number=1, scene_name="场景1", description="第一个场景"
        )

    def test_create_event(self):
        """测试创建事件"""
        event = WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            message="场景开始处理",
            severity="info",
        )

        self.assertEqual(event.workflow, self.workflow)
        self.assertEqual(event.event_type, WorkflowEvent.EventType.SCENE_STARTED)
        self.assertEqual(event.message, "场景开始处理")
        self.assertEqual(event.severity, "info")

    def test_log_scene_started(self):
        """测试记录场景开始"""
        event = WorkflowEvent.log_scene_started(self.workflow, self.scene)

        self.assertEqual(event.event_type, WorkflowEvent.EventType.SCENE_STARTED)
        self.assertEqual(event.scene, self.scene)
        self.assertIn("场景1", event.message)

    def test_log_scene_completed(self):
        """测试记录场景完成"""
        event = WorkflowEvent.log_scene_completed(self.workflow, self.scene)

        self.assertEqual(event.event_type, WorkflowEvent.EventType.SCENE_COMPLETED)
        self.assertEqual(event.scene, self.scene)
        self.assertIn("场景1", event.message)

    def test_log_scene_failed(self):
        """测试记录场景失败"""
        error_msg = "生成失败"
        event = WorkflowEvent.log_scene_failed(self.workflow, self.scene, error_msg)

        self.assertEqual(event.event_type, WorkflowEvent.EventType.SCENE_FAILED)
        self.assertEqual(event.scene, self.scene)
        self.assertIn("场景1", event.message)
        self.assertEqual(event.metadata.get("error"), error_msg)
        self.assertEqual(event.severity, "error")

    def test_event_with_metadata(self):
        """测试带元数据的事件"""
        metadata = {"scene_id": 123, "retry_count": 2}
        event = WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.TASK_RETRY,
            message="任务重试",
            metadata=metadata,
            severity="warning",
        )

        self.assertEqual(event.metadata, metadata)
        self.assertEqual(event.severity, "warning")

    def test_event_ordering(self):
        """测试事件按时间倒序排列"""
        # 创建多个事件
        WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.WORKFLOW_STARTED,
            message="启动",
            severity="info",
        )
        WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            message="场景1开始",
            severity="info",
        )
        WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.SCENE_COMPLETED,
            message="场景1完成",
            severity="info",
        )

        # 查询事件
        events = WorkflowEvent.objects.filter(workflow=self.workflow)

        # 验证顺序（最新的在前）
        self.assertEqual(events[0].event_type, WorkflowEvent.EventType.SCENE_COMPLETED)
        self.assertEqual(events[1].event_type, WorkflowEvent.EventType.SCENE_STARTED)
        self.assertEqual(events[2].event_type, WorkflowEvent.EventType.WORKFLOW_STARTED)


class WorkflowIntegrationTest(TestCase):
    """工作流集成测试"""

    def setUp(self):
        """创建测试数据"""
        self.artwork = Artwork.objects.create(title="测试作品", artwork_type="novel")
        self.chapter = Chapter.objects.create(
            artwork=self.artwork, chapter_number=1, title="第一章", original_text="测试内容"
        )
        self.scenes = [
            ScriptScene.objects.create(
                chapter=self.chapter,
                scene_number=i,
                scene_name=f"场景{i}",
                description=f"第{i}个场景",
            )
            for i in range(1, 4)
        ]

    def test_full_workflow_lifecycle(self):
        """测试完整工作流生命周期"""
        # 创建工作流
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter, total_scenes=3)

        # 启动
        workflow.start()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.RUNNING)

        # 处理场景
        for i, scene in enumerate(self.scenes[:3], 1):
            WorkflowEvent.log_scene_started(workflow, scene)
            workflow.completed_scenes = i
            workflow.update_progress(current_scene=scene)
            WorkflowEvent.log_scene_completed(workflow, scene)

        # 完成
        workflow.complete()

        # 验证
        self.assertEqual(workflow.status, ChapterWorkflow.Status.COMPLETED)
        self.assertEqual(workflow.completed_scenes, 3)
        self.assertEqual(workflow.progress_percentage, 100)

        # 验证事件数量
        event_count = WorkflowEvent.objects.filter(workflow=workflow).count()
        # 1启动 + 3开始 + 3完成 + 1完成 = 8
        self.assertEqual(event_count, 8)

    def test_workflow_with_failure(self):
        """测试包含失败场景的工作流"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter, total_scenes=3)

        workflow.start()

        # 第一个场景成功
        WorkflowEvent.log_scene_started(workflow, self.scenes[0])
        workflow.completed_scenes = 1
        workflow.update_progress(current_scene=self.scenes[0])
        WorkflowEvent.log_scene_completed(workflow, self.scenes[0])

        # 第二个场景失败
        WorkflowEvent.log_scene_started(workflow, self.scenes[1])
        error_msg = "生成超时"
        WorkflowEvent.log_scene_failed(workflow, self.scenes[1], error_msg)

        # 工作流失败
        workflow.fail(error_msg)

        # 验证
        self.assertEqual(workflow.status, ChapterWorkflow.Status.FAILED)
        self.assertEqual(workflow.completed_scenes, 1)

        # 验证事件包含失败记录
        failed_events = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.SCENE_FAILED
        )
        self.assertEqual(failed_events.count(), 1)

    def test_pause_resume_workflow(self):
        """测试暂停和恢复工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, total_scenes=3, status=ChapterWorkflow.Status.RUNNING
        )

        # 暂停
        workflow.pause()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.PAUSED)

        # 恢复
        workflow.resume()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.RUNNING)

        # 验证事件
        pause_event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_PAUSED
        ).first()
        self.assertIsNotNone(pause_event)

        resume_event = WorkflowEvent.objects.filter(
            workflow=workflow, event_type=WorkflowEvent.EventType.WORKFLOW_RESUMED
        ).first()
        self.assertIsNotNone(resume_event)


class SoftDeleteTest(TestCase):
    """软删除功能测试"""

    def setUp(self):
        """创建测试数据"""
        self.artwork = Artwork.objects.create(title="测试作品", artwork_type="novel")
        self.chapter = Chapter.objects.create(
            artwork=self.artwork, chapter_number=1, title="第一章", original_text="测试内容"
        )
        self.workflow = ChapterWorkflow.objects.create(chapter=self.chapter)
        self.scene = ScriptScene.objects.create(
            chapter=self.chapter, scene_number=1, scene_name="场景1", description="第一个场景"
        )
        self.event = WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            message="场景开始",
            severity="info",
        )

    def test_workflow_soft_delete(self):
        """测试工作流软删除"""
        # 初始状态
        self.assertFalse(self.workflow.is_deleted)
        self.assertIsNone(self.workflow.deleted_at)
        self.assertTrue(self.workflow.is_active)

        # 执行软删除
        self.workflow.soft_delete()
        self.workflow.refresh_from_db()

        # 验证状态
        self.assertTrue(self.workflow.is_deleted)
        self.assertIsNotNone(self.workflow.deleted_at)
        self.assertFalse(self.workflow.is_active)  # is_active 应该返回 False

    def test_workflow_soft_delete_twice_raises_error(self):
        """测试重复软删除抛出错误"""
        self.workflow.soft_delete()

        with self.assertRaises(ValueError) as cm:
            self.workflow.soft_delete()

        self.assertIn("已被删除", str(cm.exception))

    def test_workflow_recover(self):
        """测试恢复已删除的工作流"""
        # 先删除
        self.workflow.soft_delete()
        self.workflow.refresh_from_db()
        self.assertTrue(self.workflow.is_deleted)

        # 恢复
        self.workflow.recover()
        self.workflow.refresh_from_db()

        # 验证恢复后的状态
        self.assertFalse(self.workflow.is_deleted)
        self.assertIsNone(self.workflow.deleted_at)

    def test_workflow_recover_non_deleted_raises_error(self):
        """测试恢复未删除的工作流抛出错误"""
        with self.assertRaises(ValueError) as cm:
            self.workflow.recover()

        self.assertIn("未被删除", str(cm.exception))

    def test_workflow_hard_delete(self):
        """测试永久删除工作流"""
        workflow_id = self.workflow.workflow_id

        # 硬删除（CASCADE 会同时删除关联的 events）
        with self.assertNumQueries(2):  # ChapterWorkflow + WorkflowEvent
            self.workflow.hard_delete()

        # 验证已被物理删除
        self.assertFalse(ChapterWorkflow.objects.filter(workflow_id=workflow_id).exists())

    def test_event_soft_delete(self):
        """测试事件软删除"""
        # 初始状态
        self.assertFalse(self.event.is_deleted)
        self.assertIsNone(self.event.deleted_at)

        # 执行软删除
        self.event.soft_delete()
        self.event.refresh_from_db()

        # 验证状态
        self.assertTrue(self.event.is_deleted)
        self.assertIsNotNone(self.event.deleted_at)

    def test_event_recover(self):
        """测试恢复已删除的事件"""
        # 先删除
        self.event.soft_delete()
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_deleted)

        # 恢复
        self.event.recover()
        self.event.refresh_from_db()

        # 验证恢复后的状态
        self.assertFalse(self.event.is_deleted)
        self.assertIsNone(self.event.deleted_at)

    def test_event_hard_delete(self):
        """测试永久删除事件"""
        event_id = self.event.id

        # 硬删除
        self.event.hard_delete()

        # 验证已被物理删除
        self.assertFalse(WorkflowEvent.objects.filter(id=event_id).exists())

    def test_is_active_excludes_deleted(self):
        """测试 is_active 属性排除已删除的工作流"""
        # 创建运行中的工作流
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter, status=ChapterWorkflow.Status.RUNNING
        )
        self.assertTrue(workflow.is_active)

        # 软删除后
        workflow.soft_delete()
        workflow.refresh_from_db()
        self.assertFalse(workflow.is_active)
