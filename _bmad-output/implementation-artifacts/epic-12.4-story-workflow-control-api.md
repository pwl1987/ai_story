# Story 12-1.4: 实现工作流控制API

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P0
> **预估工作量:** 1天
> **依赖:** 12-1.1, 12-1.2, 12-1.3

---

## 📋 需求描述

**用户故事：** 作为前端用户，我需要通过API控制章节工作流的启动、暂停、继续和状态查询。

**功能说明：**
- 实现工作流启动API
- 实现工作流暂停API
- 实现工作流继续API
- 实现工作流状态查询API
- 实现权限控制（用户只能操作自己的项目）

**边界条件：**
- 不包含 UI 组件
- 不包含工作流编排逻辑
- 只提供 API 接口

**验收标准：**
- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] API文档完整
- [ ] 单元测试通过

---

## 🔧 技术实现细节

### API 端点

```
POST   /api/v1/artworks/chapters/{id}/start-workflow/
POST   /api/v1/artworks/chapters/{id}/pause-workflow/
POST   /api/v1/artworks/chapters/{id}/resume-workflow/
GET    /api/v1/artworks/chapters/{id}/workflow-status/
```

### ViewSet 实现

```python
# apps/artworks/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action

class ChapterViewSet(viewsets.ModelViewSet):
    """章节 ViewSet（扩展现有）"""

    @action(detail=True, methods=['post'])
    def start_workflow(self, request, pk=None):
        """启动章节工作流"""
        chapter = self.get_object()

        # 检查权限
        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 创建工作流记录
        workflow = ChapterWorkflow.objects.create(
            chapter=chapter,
            status=ChapterWorkflow.Status.PENDING,
            total_scenes=chapter.scenes.count()
        )

        # 启动 Celery 任务
        from apps.artworks.tasks import start_chapter_workflow_task
        task = start_chapter_workflow_task.delay(str(workflow.workflow_id))

        # 记录启动事件
        WorkflowEvent.objects.create(
            workflow=workflow,
            event_type=WorkflowEvent.EventType.WORKFLOW_STARTED,
            message='工作流已启动'
        )

        serializer = ChapterWorkflowSerializer(workflow)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def pause_workflow(self, request, pk=None):
        """暂停工作流"""
        chapter = self.get_object()

        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        workflow = chapter.workflows.filter(
            status=ChapterWorkflow.Status.RUNNING
        ).first()

        if not workflow:
            return Response(
                {'error': '没有运行中的工作流'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 转换状态
        workflow.status = ChapterWorkflow.Status.PAUSED
        workflow.save()

        # 取消 Celery 任务
        celery_app.control.revoke(
            task_id=workflow.celery_task_id,
            terminate=True
        )

        # 记录暂停事件
        WorkflowEvent.objects.create(
            workflow=workflow,
            event_type=WorkflowEvent.EventType.WORKFLOW_PAUSED,
            message='工作流已暂停'
        )

        serializer = ChapterWorkflowSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resume_workflow(self, request, pk=None):
        """继续工作流"""
        chapter = self.get_object()

        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        workflow = chapter.workflows.filter(
            status=ChapterWorkflow.Status.PAUSED
        ).first()

        if not workflow:
            return Response(
                {'error': '没有暂停的工作流'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 转换状态
        workflow.status = ChapterWorkflow.Status.RUNNING
        workflow.save()

        # 重新启动 Celery 任务
        from apps.artworks.tasks import resume_chapter_workflow_task
        task = resume_chapter_workflow_task.delay(str(workflow.workflow_id))

        # 记录继续事件
        WorkflowEvent.objects.create(
            workflow=workflow,
            event_type=WorkflowEvent.EventType.WORKFLOW_RESUMED,
            message='工作流已继续'
        )

        serializer = ChapterWorkflowSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def workflow_status(self, request, pk=None):
        """获取工作流状态"""
        chapter = self.get_object()

        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        workflow = chapter.workflows.order_by('-created_at').first()

        if not workflow:
            return Response(
                {'error': '没有工作流记录'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ChapterWorkflowSerializer(workflow)
        return Response(serializer.data)
```

### 序列化器

```python
# apps/artworks/serializers.py

class ChapterWorkflowSerializer(serializers.ModelSerializer):
    """工作流序列化器"""

    class Meta:
        model = ChapterWorkflow
        fields = [
            'workflow_id', 'chapter', 'status', 'current_scene',
            'progress_percentage', 'total_scenes', 'completed_scenes',
            'started_at', 'completed_at', 'error_message'
        ]
        read_only_fields = ['workflow_id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 添加状态描述
        data['status_display'] = instance.get_status_display()
        # 添加当前场景信息
        if instance.current_scene:
            data['current_scene_title'] = instance.current_scene.title
        return data
```

### API 测试

```python
# apps/artworks/tests/test_workflow_api.py

class TestWorkflowAPI(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.force_authenticate(user=self.user)
        self.chapter = Chapter.objects.create(
            project=Project.objects.create(user=self.user),
            title='测试章节'
        )

    def test_start_workflow(self):
        """测试启动工作流"""
        url = reverse('chapter-start-workflow', kwargs={'pk': self.chapter.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 202)
        self.assertIn('workflow_id', response.data)

    def test_pause_workflow(self):
        """测试暂停工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.RUNNING
        )

        url = reverse('chapter-pause-workflow', kwargs={'pk': self.chapter.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, ChapterWorkflow.Status.PAUSED)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        other_user = User.objects.create_user(username='other', password='test')

        url = reverse('chapter-start-workflow', kwargs={'pk': self.chapter.id})
        self.client.force_authenticate(user=other_user)
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
```

---

## 📊 依赖关系

**前置 Story:** 12-1.1, 12-1.2, 12-1.3
**阻塞 Story:** 12-3.1

---

## 🎯 成功标准

- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] API测试通过
- [ ] 文档完整
