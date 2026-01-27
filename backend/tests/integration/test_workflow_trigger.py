"""
工作流触发集成测试
测试Celery异步任务的触发和执行
"""

import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.projects.models import Project, ProjectStage

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestWorkflowTrigger:
    """工作流触发集成测试"""

    @pytest.fixture
    def api_client(self, db):
        """API客户端"""
        return APIClient()

    @pytest.fixture
    def test_user(self, db):
        """测试用户"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        return user

    @pytest.fixture
    def project_with_stages(self, db, test_user):
        """带阶段的项目"""
        project = Project.objects.create(
            name='测试项目',
            description='测试描述',
            original_topic='AI视频生成',
            user=test_user,
            status='draft'
        )
        # 创建阶段
        for stage_type in ['rewrite', 'storyboard', 'image_generation',
                          'camera_movement', 'video_generation']:
            ProjectStage.objects.create(
                project=project,
                stage_type=stage_type,
                status='pending'
            )
        return project

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_execute_llm_stage_triggers_celery_task(self, mock_delay, api_client,
                                                     test_user, project_with_stages):
        """测试执行LLM阶段触发Celery任务"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务返回值
        mock_task = MagicMock()
        mock_task.id = 'test-task-id-123'
        mock_delay.return_value = mock_task

        # 准备请求数据
        request_data = {
            'stage_name': 'rewrite',
            'input_data': {
                'raw_text': 'AI视频生成测试',
                'human_text': ''
            }
        }

        # 发送POST请求执行阶段
        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        # 验证响应（202 = 异步任务已接受）
        assert response.status_code == 202
        assert 'task_id' in response.data
        assert 'channel' in response.data
        assert response.data['task_id'] == 'test-task-id-123'

        # 验证Celery任务被调用
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args
        assert call_args[1]['project_id'] == str(project_with_stages.id)
        assert call_args[1]['stage_name'] == 'rewrite'
        assert call_args[1]['user_id'] == test_user.id

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_execute_stage_updates_project_status(self, mock_delay, api_client,
                                                  test_user, project_with_stages):
        """测试执行阶段时更新项目状态为processing"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务
        mock_task = MagicMock()
        mock_task.id = 'test-task-id'
        mock_delay.return_value = mock_task

        # 项目初始状态为draft
        assert project_with_stages.status == 'draft'

        # 执行阶段
        request_data = {
            'stage_name': 'storyboard',
            'input_data': {'raw_text': '测试'}
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        assert response.status_code == 202

        # 验证项目状态更新为processing
        project_with_stages.refresh_from_db()
        assert project_with_stages.status == 'processing'

    @patch('apps.projects.tasks.execute_text2image_stage.delay')
    def test_execute_image_generation_stage(self, mock_delay, api_client,
                                            test_user, project_with_stages):
        """测试执行文生图阶段"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务
        mock_task = MagicMock()
        mock_task.id = 'image-task-id'
        mock_delay.return_value = mock_task

        request_data = {
            'stage_name': 'image_generation',
            'input_data': {
                'storyboard_ids': ['sb-1', 'sb-2']
            }
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        assert response.status_code == 202
        assert response.data['task_id'] == 'image-task-id'

        # 验证任务被调用
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args
        assert call_args[1]['project_id'] == str(project_with_stages.id)
        assert call_args[1]['storyboard_ids'] == ['sb-1', 'sb-2']

    @patch('apps.projects.tasks.execute_image2video_stage.delay')
    def test_execute_video_generation_stage(self, mock_delay, api_client,
                                             test_user, project_with_stages):
        """测试执行图生视频阶段"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务
        mock_task = MagicMock()
        mock_task.id = 'video-task-id'
        mock_delay.return_value = mock_task

        request_data = {
            'stage_name': 'video_generation',
            'input_data': {
                'storyboard_ids': ['sb-1', 'sb-2']
            }
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        assert response.status_code == 202
        assert response.data['task_id'] == 'video-task-id'

        # 验证任务被调用
        mock_delay.assert_called_once()

    def test_execute_invalid_stage_type(self, api_client, test_user, project_with_stages):
        """测试执行无效的阶段类型"""
        api_client.force_authenticate(user=test_user)

        request_data = {
            'stage_name': 'invalid_stage',
            'input_data': {}
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        # 应该返回400错误
        assert response.status_code == 400

    def test_execute_stage_unauthenticated(self, api_client, project_with_stages):
        """测试未认证用户无法执行阶段"""
        request_data = {
            'stage_name': 'rewrite',
            'input_data': {}
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        # 应该返回401或403
        assert response.status_code in [401, 403]

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_execute_stage_channel_format(self, mock_delay, api_client,
                                          test_user, project_with_stages):
        """测试Redis频道名称格式正确"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务
        mock_task = MagicMock()
        mock_task.id = 'test-task'
        mock_delay.return_value = mock_task

        request_data = {
            'stage_name': 'camera_movement',
            'input_data': {}
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        assert response.status_code == 202

        # 验证频道名称格式
        expected_channel = f'ai_story:project:{project_with_stages.id}:stage:camera_movement'
        assert response.data['channel'] == expected_channel

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_execute_nonexistent_project(self, mock_delay, api_client, test_user):
        """测试执行不存在的项目"""
        api_client.force_authenticate(user=test_user)

        fake_project_id = '00000000-0000-0000-0000-000000000000'

        request_data = {
            'stage_name': 'rewrite',
            'input_data': {}
        }

        response = api_client.post(
            f'/api/v1/projects/{fake_project_id}/execute_stage/',
            request_data,
            format='json'
        )

        # 应该返回404
        assert response.status_code == 404

    @patch('apps.projects.tasks.execute_llm_stage.delay')
    def test_execute_stage_project_already_processing(self, mock_delay, api_client,
                                                      test_user, project_with_stages):
        """测试项目已在处理中时不重复更新状态"""
        api_client.force_authenticate(user=test_user)

        # Mock Celery任务
        mock_task = MagicMock()
        mock_task.id = 'test-task'
        mock_delay.return_value = mock_task

        # 设置项目状态为processing
        project_with_stages.status = 'processing'
        project_with_stages.save()

        request_data = {
            'stage_name': 'rewrite',
            'input_data': {}
        }

        response = api_client.post(
            f'/api/v1/projects/{project_with_stages.id}/execute_stage/',
            request_data,
            format='json'
        )

        assert response.status_code == 202
        # 状态应保持processing
        project_with_stages.refresh_from_db()
        assert project_with_stages.status == 'processing'
