"""
项目工作流服务测试
测试ProjectWorkflowService的业务逻辑
遵循SOLID原则和TDD红绿重构循环
"""

import pytest

from apps.projects.models import ProjectStage
from apps.projects.services import ProjectWorkflowService
from apps.projects.tests.factories import ProjectFactory, ProjectStageFactory


@pytest.mark.django_db
class TestProjectWorkflowService:
    """测试ProjectWorkflowService业务逻辑"""

    def test_get_stage_index_valid_stages(self):
        """测试获取阶段索引 - 有效阶段"""
        # Given & When & Then
        assert ProjectWorkflowService.get_stage_index("rewrite") == 0
        assert ProjectWorkflowService.get_stage_index("storyboard") == 1
        assert ProjectWorkflowService.get_stage_index("image_generation") == 2
        assert ProjectWorkflowService.get_stage_index("camera_movement") == 3
        assert ProjectWorkflowService.get_stage_index("video_generation") == 4

    def test_get_stage_index_invalid_stage(self):
        """测试获取阶段索引 - 无效阶段"""
        # Given & When & Then
        assert ProjectWorkflowService.get_stage_index("invalid_stage") == -1
        assert ProjectWorkflowService.get_stage_index("") == -1
        assert ProjectWorkflowService.get_stage_index(None) == -1  # 边界值: None输入

    def test_get_next_stage_middle(self):
        """测试获取下一阶段 - 中间阶段"""
        # Given & When & Then
        assert ProjectWorkflowService.get_next_stage("rewrite") == "storyboard"
        assert ProjectWorkflowService.get_next_stage("storyboard") == "image_generation"
        assert ProjectWorkflowService.get_next_stage("image_generation") == "camera_movement"

    def test_get_next_stage_last_stage(self):
        """测试获取下一阶段 - 最后阶段返回None"""
        # Given & When & Then
        assert ProjectWorkflowService.get_next_stage("video_generation") is None

    def test_get_next_stage_invalid_stage(self):
        """测试获取下一阶段 - 无效阶段返回None"""
        # Given & When & Then
        assert ProjectWorkflowService.get_next_stage("invalid") is None

    def test_get_previous_stage_first_stage(self):
        """测试获取上一阶段 - 第一个阶段返回None"""
        # Given & When & Then
        assert ProjectWorkflowService.get_previous_stage("rewrite") is None

    def test_get_previous_stage_middle_stage(self):
        """测试获取上一阶段 - 中间阶段"""
        # Given & When & Then
        assert ProjectWorkflowService.get_previous_stage("storyboard") == "rewrite"
        assert ProjectWorkflowService.get_previous_stage("image_generation") == "storyboard"

    def test_start_stage_success(self):
        """测试开始阶段 - 成功场景"""
        # Given
        project = ProjectFactory(status="draft")
        ProjectStageFactory(project=project, stage_type="rewrite", status="pending")

        # When
        result = ProjectWorkflowService.start_stage(project.id, "rewrite", {"test": "data"})

        # Then
        assert result.status == "processing"
        assert result.started_at is not None
        assert result.input_data == {"test": "data"}

        # 验证项目状态已更新
        project.refresh_from_db()
        assert project.status == "processing"

    def test_start_stage_stage_not_found(self):
        """测试开始阶段 - 阶段不存在"""
        # Given
        project = ProjectFactory()

        # When & Then
        with pytest.raises(ValueError, match="阶段 rewrite 不存在"):
            ProjectWorkflowService.start_stage(project.id, "rewrite")

    def test_start_stage_already_processing(self):
        """测试开始阶段 - 阶段正在处理中"""
        # Given
        project = ProjectFactory()
        ProjectStageFactory(project=project, stage_type="rewrite", status="processing")

        # When & Then
        with pytest.raises(ValueError, match="正在处理中"):
            ProjectWorkflowService.start_stage(project.id, "rewrite")

    def test_start_stage_prerequisites_not_met(self):
        """测试开始阶段 - 前置阶段未完成"""
        # Given
        project = ProjectFactory()
        # 创建rewrite阶段（未完成）和storyboard阶段
        ProjectStageFactory(
            project=project,
            stage_type="rewrite",
            status="pending",  # 未完成
        )
        ProjectStageFactory(project=project, stage_type="storyboard", status="pending")

        # When & Then - 前置阶段未完成
        with pytest.raises(ValueError, match=r"前置阶段.*未完成"):
            ProjectWorkflowService.start_stage(project.id, "storyboard")

    def test_complete_stage_success(self):
        """测试完成阶段 - 成功场景"""
        # Given
        project = ProjectFactory(status="processing")
        ProjectStageFactory(project=project, stage_type="rewrite", status="processing")
        output_data = {"result": "success"}

        # When
        result = ProjectWorkflowService.complete_stage(project.id, "rewrite", output_data)

        # Then
        assert result["completed"] is True
        assert result["stage"].status == "completed"
        assert result["stage"].output_data == output_data
        assert result["stage"].completed_at is not None
        assert result["stage"].error_message == ""

    def test_complete_stage_auto_next(self):
        """测试完成阶段 - 自动开始下一阶段"""
        # Given
        project = ProjectFactory(status="processing")
        ProjectStageFactory(project=project, stage_type="rewrite", status="processing")
        ProjectStageFactory(project=project, stage_type="storyboard", status="pending")
        output_data = {"result": "success"}

        # When
        result = ProjectWorkflowService.complete_stage(
            project.id, "rewrite", output_data, auto_next=True
        )

        # Then
        assert result["completed"] is True
        assert result["next_stage"] is not None
        assert result["next_stage"].stage_type == "storyboard"
        assert result["next_stage"].status == "processing"

    def test_complete_stage_project_completed(self):
        """测试完成阶段 - 所有阶段完成"""
        # Given
        project = ProjectFactory(status="processing")
        # 创建所有阶段并标记最后一个为processing
        for stage_type in ProjectWorkflowService.STAGE_ORDER:
            ProjectStageFactory(project=project, stage_type=stage_type, status="completed")
        # 将最后一个设为processing
        last_stage = ProjectStage.objects.filter(
            project=project, stage_type="video_generation"
        ).first()
        last_stage.status = "processing"
        last_stage.save()

        # When
        result = ProjectWorkflowService.complete_stage(
            project.id, "video_generation", {"final": "result"}
        )

        # Then
        assert result["completed"] is True
        assert result.get("project_completed") is True

        # 验证项目状态
        project.refresh_from_db()
        assert project.status == "completed"
        assert project.completed_at is not None

    def test_fail_stage_with_retry(self):
        """测试阶段失败 - 有重试次数"""
        # Given
        project = ProjectFactory(status="processing")
        stage = ProjectStageFactory(
            project=project, stage_type="rewrite", status="processing", retry_count=0, max_retries=3
        )
        error_message = "测试错误"

        # When
        result = ProjectWorkflowService.fail_stage(
            project.id, "rewrite", error_message, auto_retry=True
        )

        # Then
        assert result["failed"] is True
        assert result["will_retry"] is True
        assert result["retry_count"] == 1

        # 验证阶段状态
        stage.refresh_from_db()
        assert stage.status == "processing"
        assert stage.error_message == error_message

    def test_fail_stage_max_retries_reached(self):
        """测试阶段失败 - 达到最大重试次数"""
        # Given
        project = ProjectFactory(status="processing")
        stage = ProjectStageFactory(
            project=project, stage_type="rewrite", status="processing", retry_count=3, max_retries=3
        )

        # When
        result = ProjectWorkflowService.fail_stage(
            project.id, "rewrite", "最终失败", auto_retry=True
        )

        # Then
        assert result["failed"] is True
        assert result["will_retry"] is False
        assert result["max_retries_reached"] is True

        # 验证阶段和项目状态
        stage.refresh_from_db()
        assert stage.status == "failed"

        project.refresh_from_db()
        assert project.status == "failed"

    def test_fail_stage_no_auto_retry(self):
        """测试阶段失败 - 不自动重试"""
        # Given
        project = ProjectFactory(status="processing")
        stage = ProjectStageFactory(
            project=project, stage_type="rewrite", status="processing", retry_count=0, max_retries=3
        )

        # When
        result = ProjectWorkflowService.fail_stage(project.id, "rewrite", "错误", auto_retry=False)

        # Then
        assert result["failed"] is True
        assert result["will_retry"] is False

        # 验证阶段状态
        stage.refresh_from_db()
        assert stage.status == "failed"

    def test_rollback_to_stage_middle(self):
        """测试回滚到指定阶段 - 中间阶段"""
        # Given
        project = ProjectFactory(status="processing")
        # 创建多个阶段
        for i, stage_type in enumerate(ProjectWorkflowService.STAGE_ORDER):
            ProjectStageFactory(
                project=project, stage_type=stage_type, status="completed" if i < 3 else "pending"
            )

        # When - 回滚到storyboard
        result = ProjectWorkflowService.rollback_to_stage(project.id, "storyboard")

        # Then
        assert result["rolled_back_to"] == "storyboard"
        # 回滚到storyboard会重置storyboard及之后的所有阶段
        # storyboard(1), image_generation(2), camera_movement(3), video_generation(4)
        assert result["reset_stages_count"] == 4

        # 验证阶段状态
        for stage_type in ["storyboard", "image_generation", "camera_movement", "video_generation"]:
            stage = ProjectStage.objects.get(project=project, stage_type=stage_type)
            assert stage.status == "pending"
            assert stage.output_data == {}
            assert stage.retry_count == 0

        # rewrite应保持completed
        rewrite_stage = ProjectStage.objects.get(project=project, stage_type="rewrite")
        assert rewrite_stage.status == "completed"

    def test_rollback_to_stage_invalid_stage(self):
        """测试回滚到指定阶段 - 无效阶段"""
        # Given
        project = ProjectFactory()

        # When & Then
        with pytest.raises(ValueError, match="无效的阶段类型"):
            ProjectWorkflowService.rollback_to_stage(project.id, "invalid")

    def test_get_workflow_progress(self):
        """测试获取工作流进度"""
        # Given
        project = ProjectFactory()
        # 创建阶段，部分完成
        ProjectStageFactory(project=project, stage_type="rewrite", status="completed")
        ProjectStageFactory(project=project, stage_type="storyboard", status="processing")
        ProjectStageFactory(project=project, stage_type="image_generation", status="pending")

        # When
        progress = ProjectWorkflowService.get_workflow_progress(project.id)

        # Then
        assert progress["total_stages"] == 5
        assert progress["completed_stages"] == 1
        assert progress["processing_stages"] == 1
        assert progress["failed_stages"] == 0
        assert progress["progress_percentage"] == 20.0  # 1/5
        assert progress["current_stage"]["stage_type"] == "storyboard"
        assert len(progress["stages"]) == 3

    def test_get_workflow_progress_all_completed(self):
        """测试获取工作流进度 - 全部完成"""
        # Given
        project = ProjectFactory()
        for stage_type in ProjectWorkflowService.STAGE_ORDER:
            ProjectStageFactory(project=project, stage_type=stage_type, status="completed")

        # When
        progress = ProjectWorkflowService.get_workflow_progress(project.id)

        # Then
        assert progress["total_stages"] == 5
        assert progress["completed_stages"] == 5
        assert progress["progress_percentage"] == 100.0
        assert progress["current_stage"] is None

    def test_get_workflow_progress_empty(self):
        """测试获取工作流进度 - 无阶段"""
        # Given
        project = ProjectFactory()

        # When
        progress = ProjectWorkflowService.get_workflow_progress(project.id)

        # Then
        assert progress["total_stages"] == 5
        assert progress["completed_stages"] == 0
        assert progress["progress_percentage"] == 0.0
        assert progress["current_stage"] is None

    def test_check_prerequisites_first_stage(self):
        """测试前置阶段检查 - 第一个阶段无需检查"""
        # Given
        project = ProjectFactory()
        ProjectStageFactory(project=project, stage_type="rewrite", status="pending")

        # When & Then - 不应抛出异常
        ProjectWorkflowService._check_prerequisites(project.id, "rewrite")

    def test_check_prerequisites_all_completed(self):
        """测试前置阶段检查 - 所有前置阶段已完成"""
        # Given
        project = ProjectFactory()
        ProjectStageFactory(project=project, stage_type="rewrite", status="completed")
        ProjectStageFactory(project=project, stage_type="storyboard", status="pending")

        # When & Then - 不应抛出异常
        ProjectWorkflowService._check_prerequisites(project.id, "storyboard")

    def test_check_prerequisites_not_completed(self):
        """测试前置阶段检查 - 前置阶段未完成"""
        # Given
        project = ProjectFactory()
        ProjectStageFactory(project=project, stage_type="rewrite", status="pending")
        ProjectStageFactory(project=project, stage_type="storyboard", status="pending")

        # When & Then
        with pytest.raises(ValueError, match=r"前置阶段.*未完成"):
            ProjectWorkflowService._check_prerequisites(project.id, "storyboard")

    def test_check_prerequisites_stage_not_exist(self):
        """测试前置阶段检查 - 前置阶段不存在"""
        # Given
        project = ProjectFactory()
        ProjectStageFactory(project=project, stage_type="storyboard", status="pending")
        # rewrite阶段不存在

        # When & Then
        with pytest.raises(ValueError, match=r"前置阶段.*不存在"):
            ProjectWorkflowService._check_prerequisites(project.id, "storyboard")

    def test_stage_order_constants(self):
        """测试阶段顺序常量"""
        # Given & When & Then
        assert len(ProjectWorkflowService.STAGE_ORDER) == 5
        assert "rewrite" in ProjectWorkflowService.STAGE_ORDER
        assert "storyboard" in ProjectWorkflowService.STAGE_ORDER
        assert "image_generation" in ProjectWorkflowService.STAGE_ORDER
        assert "camera_movement" in ProjectWorkflowService.STAGE_ORDER
        assert "video_generation" in ProjectWorkflowService.STAGE_ORDER
