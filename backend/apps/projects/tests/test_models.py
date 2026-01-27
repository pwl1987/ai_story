"""
项目管理域模型测试
测试Project、ProjectStage、ProjectModelConfig模型
遵循单一职责原则(SRP)
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.projects.tests.factories import (
    ProjectFactory,
    ProjectModelConfigFactory,
    ProjectStageFactory,
    UserFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestProjectModel:
    """测试Project模型"""

    def test_create_project_minimal(self):
        """测试创建最小项目"""
        user = UserFactory()
        project = Project.objects.create(
            name="测试项目",
            original_topic="人工智能",
            user=user
        )

        assert project.id is not None
        assert project.name == "测试项目"
        assert project.original_topic == "人工智能"
        assert project.status == 'draft'
        assert project.user == user
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_create_project_full(self):
        """测试创建完整项目"""
        user = UserFactory()
        project = ProjectFactory(
            name="完整项目",
            description="项目描述",
            original_topic="测试主题",
            status='processing',
            user=user
        )

        assert Project.objects.filter(id=project.id).exists()

    def test_project_status_choices(self):
        """测试项目状态选择"""
        user = UserFactory()
        project = ProjectFactory(user=user)

        # 测试所有有效状态
        valid_statuses = ['draft', 'processing', 'completed', 'failed', 'paused']
        for status in valid_statuses:
            project.status = status
            project.save()
            project.refresh_from_db()
            assert project.status == status

    def test_project_str_representation(self):
        """测试项目的字符串表示"""
        project = ProjectFactory(name="字符串测试项目")
        assert str(project) == "字符串测试项目"

    def test_project_ordering(self):
        """测试项目默认排序(按创建时间降序)"""
        user = UserFactory()
        project1 = ProjectFactory(user=user, name="项目1")
        project2 = ProjectFactory(user=user, name="项目2")
        project3 = ProjectFactory(user=user, name="项目3")

        projects = list(Project.objects.filter(user=user))
        assert projects[0] == project3
        assert projects[1] == project2
        assert projects[2] == project1

    def test_project_user_cascade_delete(self):
        """测试用户删除时项目级联删除"""
        user = UserFactory()
        project = ProjectFactory(user=user)

        user_id = user.id
        project_id = project.id

        user.delete()

        assert not User.objects.filter(id=user_id).exists()
        assert not Project.objects.filter(id=project_id).exists()


@pytest.mark.django_db
class TestProjectStageModel:
    """测试ProjectStage模型"""

    def test_create_stage_minimal(self):
        """测试创建最小阶段"""
        project = ProjectFactory()
        stage = ProjectStage.objects.create(
            project=project,
            stage_type='rewrite'
        )

        assert stage.id is not None
        assert stage.project == project
        assert stage.stage_type == 'rewrite'
        assert stage.status == 'pending'
        assert stage.retry_count == 0
        assert stage.max_retries == 3

    def test_stage_type_choices(self):
        """测试阶段类型选择"""
        project = ProjectFactory()
        stage_types = ['rewrite', 'storyboard', 'image_generation',
                      'camera_movement', 'video_generation']

        for stage_type in stage_types:
            stage = ProjectStageFactory(
                project=project,
                stage_type=stage_type
            )
            assert stage.stage_type == stage_type

    def test_stage_status_choices(self):
        """测试阶段状态选择"""
        project = ProjectFactory()
        stage = ProjectStageFactory(project=project)

        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        for status in valid_statuses:
            stage.status = status
            stage.save()
            stage.refresh_from_db()
            assert stage.status == status

    def test_stage_unique_constraint(self):
        """测试项目+阶段类型唯一约束"""
        project = ProjectFactory()

        # 创建第一个阶段
        ProjectStageFactory(project=project, stage_type='rewrite')

        # 尝试创建相同类型的阶段应该失败
        with pytest.raises(IntegrityError):
            ProjectStageFactory(project=project, stage_type='rewrite')

    def test_stage_json_fields(self):
        """测试阶段JSON字段"""
        project = ProjectFactory()
        input_data = {"prompt": "测试提示词"}
        output_data = {"result": "测试结果"}

        stage = ProjectStageFactory(
            project=project,
            input_data=input_data,
            output_data=output_data
        )

        assert stage.input_data == input_data
        assert stage.output_data == output_data

    def test_stage_retry_mechanism(self):
        """测试重试机制"""
        project = ProjectFactory()
        stage = ProjectStageFactory(
            project=project,
            retry_count=0,
            max_retries=3
        )

        assert stage.retry_count < stage.max_retries

        # 模拟重试
        stage.retry_count += 1
        stage.save()

        stage.refresh_from_db()
        assert stage.retry_count == 1

    def test_stage_timestamps(self):
        """测试阶段时间戳"""
        project = ProjectFactory()
        stage = ProjectStageFactory(project=project)

        # 初始状态下时间戳为空
        assert stage.started_at is None
        assert stage.completed_at is None

        # 设置时间戳
        from django.utils import timezone
        now = timezone.now()
        stage.started_at = now
        stage.completed_at = now
        stage.save()

        stage.refresh_from_db()
        assert stage.started_at is not None
        assert stage.completed_at is not None

    def test_stage_str_representation(self):
        """测试阶段字符串表示"""
        project = ProjectFactory(name="测试项目")
        stage = ProjectStageFactory(project=project, stage_type='rewrite')
        expected = f"{project.name} - 文案改写"
        assert str(stage) == expected


@pytest.mark.django_db
class TestProjectModelConfigModel:
    """测试ProjectModelConfig模型"""

    def test_create_config_minimal(self):
        """测试创建最小配置"""
        project = ProjectFactory()
        config = ProjectModelConfig.objects.create(
            project=project
        )

        assert config.id is not None
        assert config.project == project
        assert config.load_balance_strategy == 'weighted'

    def test_config_load_balance_strategies(self):
        """测试负载均衡策略选择"""
        strategies = ['round_robin', 'random', 'weighted', 'least_loaded']

        for strategy in strategies:
            project = ProjectFactory()
            config = ProjectModelConfigFactory(
                project=project,
                load_balance_strategy=strategy
            )
            assert config.load_balance_strategy == strategy

    def test_config_one_to_one_relationship(self):
        """测试项目与配置的一对一关系"""
        project = ProjectFactory()
        config1 = ProjectModelConfigFactory(project=project)

        # 尝试为同一项目创建第二个配置应该失败
        with pytest.raises(IntegrityError):
            ProjectModelConfigFactory(project=project)

    def test_config_str_representation(self):
        """测试配置字符串表示"""
        project = ProjectFactory(name="测试项目")
        config = ProjectModelConfigFactory(project=project)
        expected = f"{project.name} - 模型配置"
        assert str(config) == expected


@pytest.mark.django_db
class TestProjectStageRelationships:
    """测试Project与ProjectStage的关系"""

    def test_project_has_many_stages(self):
        """测试项目有多个阶段"""
        project = ProjectFactory()

        stage1 = ProjectStageFactory(project=project, stage_type='rewrite')
        stage2 = ProjectStageFactory(project=project, stage_type='storyboard')
        stage3 = ProjectStageFactory(project=project, stage_type='image_generation')

        assert project.stages.count() == 3
        assert stage1 in project.stages.all()
        assert stage2 in project.stages.all()
        assert stage3 in project.stages.all()

    def test_project_deletion_cascades_to_stages(self):
        """测试项目删除级联到阶段"""
        project = ProjectFactory()
        stage = ProjectStageFactory(project=project)

        project_id = project.id
        stage_id = stage.id

        project.delete()

        assert not Project.objects.filter(id=project_id).exists()
        assert not ProjectStage.objects.filter(id=stage_id).exists()


@pytest.mark.django_db
class TestProjectModelConfigRelationships:
    """测试Project与ProjectModelConfig的关系"""

    def test_project_has_one_config(self):
        """测试项目有一个配置"""
        project = ProjectFactory()
        config = ProjectModelConfigFactory(project=project)

        assert project.model_config == config
        assert config.project == project

    def test_project_deletion_cascades_to_config(self):
        """测试项目删除级联到配置"""
        project = ProjectFactory()
        config = ProjectModelConfigFactory(project=project)

        project_id = project.id
        config_id = config.id

        project.delete()

        assert not Project.objects.filter(id=project_id).exists()
        assert not ProjectModelConfig.objects.filter(id=config_id).exists()
