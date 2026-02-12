# Story 12-1.1: 创建工作流数据模型

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P0
> **预估工作量:** 1天
> **依赖:** 无

---

## 📋 需求描述

**用户故事：** 作为开发者，我需要定义章节工作流的数据模型，以便系统能够追踪工作流的状态和进度。

**功能说明：**
- 创建 `ChapterWorkflow` 模型，存储章节工作流的核心信息
- 创建 `WorkflowEvent` 模型，记录工作流的关键事件
- 定义工作流状态枚举
- 添加 Django Admin 配置

**边界条件：**
- 不涉及工作流的执行逻辑
- 不涉及 API 接口
- 只定义数据结构

**验收标准：**
- [ ] ChapterWorkflow 模型包含所有必需字段
- [ ] WorkflowEvent 模型能记录事件历史
- [ ] Admin 界面可以查看和编辑工作流
- [ ] 数据库迁移成功执行
- [ ] 单元测试通过

---

## 🔧 技术实现细节

### 数据模型

```python
# apps/artworks/models.py

class ChapterWorkflow(models.Model):
    """章节工作流记录"""

    class Status(models.TextChoices):
        PENDING = 'pending'
        RUNNING = 'running'
        PAUSED = 'paused'
        COMPLETED = 'completed'
        FAILED = 'failed'

    workflow_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_('工作流ID')
    )
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.CASCADE,
        related_name='workflows',
        verbose_name=_('章节')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('状态')
    )
    current_scene = models.ForeignKey(
        'ScriptScene',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_in_workflows',
        verbose_name=_('当前场景')
    )
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('进度百分比')
    )
    total_scenes = models.IntegerField(
        default=0,
        verbose_name=_('总场景数')
    )
    completed_scenes = models.IntegerField(
        default=0,
        verbose_name=_('已完成场景数')
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('开始时间')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('完成时间')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('错误信息')
    )
    celery_task_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('Celery任务ID')
    )

    class Meta:
        verbose_name = _('章节工作流')
        verbose_name_plural = _('章节工作流')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id']),
            models.Index(fields=['chapter', '-created_at']),
        ]

    def __str__(self):
        return f'{self.chapter.title} - {self.get_status_display()}'

    @property
    def is_active(self):
        return self.status in [self.Status.RUNNING, self.Status.PAUSED]

    def calculate_progress(self):
        """重新计算进度百分比"""
        if self.total_scenes == 0:
            return 0
        return int((self.completed_scenes / self.total_scenes) * 100)


class WorkflowEvent(models.Model):
    """工作流事件记录"""

    class EventType(models.TextChoices):
        WORKFLOW_STARTED = 'workflow_started'
        WORKFLOW_COMPLETED = 'workflow_completed'
        WORKFLOW_FAILED = 'workflow_failed'
        WORKFLOW_PAUSED = 'workflow_paused'
        WORKFLOW_RESUMED = 'workflow_resumed'
        SCENE_STARTED = 'scene_started'
        SCENE_COMPLETED = 'scene_completed'
        SCENE_FAILED = 'scene_failed'

    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_('事件ID')
    )
    workflow = models.ForeignKey(
        ChapterWorkflow,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('工作流')
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        verbose_name=_('事件类型')
    )
    scene = models.ForeignKey(
        'ScriptScene',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_events',
        verbose_name=_('关联场景')
    )
    message = models.TextField(
        blank=True,
        verbose_name=_('事件消息')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('元数据')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('时间戳')
    )

    class Meta:
        verbose_name = _('工作流事件')
        verbose_name_plural = _('工作流事件')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['workflow', '-timestamp']),
        ]

    def __str__(self):
        return f'{self.get_event_type_display()} - {self.timestamp}'
```

### Django Admin 配置

```python
# apps/artworks/admin.py

@admin.register(ChapterWorkflow)
class ChapterWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'workflow_id', 'chapter', 'status',
        'progress_percentage', 'started_at', 'completed_at'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['workflow_id', 'chapter__title']
    readonly_fields = ['workflow_id', 'created_at']

    fieldsets = (
        (_('基本信息'), {
            'fields': ('workflow_id', 'chapter', 'status')
        }),
        (_('进度信息'), {
            'fields': (
                'current_scene', 'progress_percentage',
                'total_scenes', 'completed_scenes'
            )
        }),
        (_('时间信息'), {
            'fields': ('started_at', 'completed_at')
        }),
        (_('错误信息'), {
            'fields': ('error_message',)
        }),
    )


@admin.register(WorkflowEvent)
class WorkflowEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_id', 'workflow', 'event_type',
        'scene', 'timestamp'
    ]
    list_filter = ['event_type', 'timestamp']
    search_fields = ['event_id', 'workflow__workflow_id']
    readonly_fields = ['event_id', 'timestamp']
```

### 测试用例

```python
# apps/artworks/tests/test_workflow_models.py

class TestChapterWorkflowModel(TestCase):
    def test_create_workflow(self):
        """测试创建工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            status=ChapterWorkflow.Status.PENDING
        )
        self.assertEqual(workflow.status, 'pending')
        self.assertIsNotNone(workflow.workflow_id)

    def test_workflow_status_transitions(self):
        """测试状态转换"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)

        # pending -> running
        workflow.status = ChapterWorkflow.Status.RUNNING
        workflow.save()
        self.assertTrue(workflow.is_active)

        # running -> completed
        workflow.status = ChapterWorkflow.Status.COMPLETED
        workflow.save()
        self.assertFalse(workflow.is_active)

    def test_progress_calculation(self):
        """测试进度计算"""
        workflow = ChapterWorkflow.objects.create(
            chapter=self.chapter,
            total_scenes=10,
            completed_scenes=5
        )
        workflow.calculate_progress()
        workflow.save()
        self.assertEqual(workflow.progress_percentage, 50)


class TestWorkflowEventModel(TestCase):
    def test_create_event(self):
        """测试创建事件"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)
        event = WorkflowEvent.objects.create(
            workflow=workflow,
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            scene=self.scene
        )
        self.assertEqual(event.event_type, 'scene_started')
        self.assertIsNotNone(event.event_id)

    def test_event_metadata(self):
        """测试事件元数据"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)
        event = WorkflowEvent.objects.create(
            workflow=workflow,
            event_type=WorkflowEvent.EventType.SCENE_FAILED,
            metadata={'error': 'AI generation timeout'}
        )
        self.assertEqual(event.metadata['error'], 'AI generation timeout')
```

---

## 📊 依赖关系

**前置 Story:** 无
**阻塞 Story:** 12-1.2, 12-1.3, 12-1.4

---

## 🎯 成功标准

- [x] 数据模型创建成功
- [x] 数据库迁移执行成功
- [x] Admin 界面可正常使用
- [x] 所有单元测试通过
- [x] 代码符合规范

## ✅ 实现完成 (2026-02-12)

### 已完成文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `apps/artworks/models.py` | ✅ | 新增 ChapterWorkflow 和 WorkflowEvent 模型，包含所有必需字段和方法 |
| `apps/artworks/admin.py` | ✅ | 新增 ChapterWorkflowAdmin 和 WorkflowEventAdmin 配置 |
| `apps/artworks/tests/test_workflow_models.py` | ✅ | 创建 18 个测试用例，全部通过 |

### 测试结果

```
18 passed, 1 warning in 0.45s
Coverage: 79% (new lines: 505, missed: 108)
```

### 迁移记录

- 迁移文件: `0005_chapterworkflow_workflowevent_and_more.py`
- 创建模型: ChapterWorkflow, WorkflowEvent
- 创建索引: workflow_id, chapter+created_at, status, event_type, severity

### 功能亮点

1. **状态管理**: 工作流支持 5 种状态 (pending/running/paused/completed/failed)
2. **事件追踪**: 记录工作流生命周期和场景处理事件
3. **Admin 保护**: WorkflowEvent 设置为只读，只能由系统创建
4. **业务方法**: start/pause/resume/complete/fail 方法封装状态转换逻辑
5. **进度计算**: 自动计算进度百分比和已用时长

---

## 🔧 代码评审修复 (2026-02-12)

### 已修复问题

#### P0 严重问题

| 问题ID | 描述 | 状态 |
|--------|------|------|
| CRIT-001 | WorkflowEvent 继承 TimeStampedModel，统一时间字段 | ✅ 已修复 |
| CRIT-002 | 删除冗余 event_id 字段，使用默认 id 主键 | ✅ 已修复 |

#### P1 警告问题

| 问题ID | 描述 | 状态 |
|--------|------|------|
| WARN-001 | 业务方法添加返回类型注解 `-> 'ChapterWorkflow'` | ✅ 已修复 |

### 修复详情

**CRIT-001 修复**: WorkflowEvent 继承 TimeStampedModel
- 删除了自定义 `event_id` 字段（使用 Django 默认 id）
- 删除了自定义 `timestamp` 字段（使用基类的 `created_at`, `updated_at`）
- 更新了 `ordering` 使用基类的 `created_at`

**CRIT-002 修复**: 业务方法添加返回值
- 所有状态转换方法添加了返回类型注解 `-> 'ChapterWorkflow'`
- 支持链式调用（如 `workflow.start().complete()`）

**测试验证**:
- 18 个测试用例全部通过 ✅
- 测试覆盖率保持 79% ✅

### 修复后评分

| 维度 | 修复前 | 修复后 |
|--------|--------|--------|
| 架构合规性 | 6/10 | 9/10 |
| 需求完整性 | 10/10 | 10/10 |
| 代码安全性 | 8/10 | 9/10 |
| 可测试性 | 9/10 | 9/10 |
| 命名规范性 | 9/10 | 9/10 |

**综合评分**: **42/50 (84%)** → **46/50 (92%)** - 已通过评审门槛

---

## 🔧 代码评审修复 (2026-02-12 - 第二轮)

### 已修复问题

#### P1 警告问题

| 问题ID | 描述 | 状态 |
|--------|------|------|
| WARN-002 | 添加迁移冲突检查 | ✅ 已修复 |
| WARN-003 | 考虑软删除机制 | ✅ 已修复 |

### 修复详情

**WARN-002 修复**: 迁移冲突检查
- 创建了空迁移文件验证无冲突
- 验证了 `makemigrations` 正常工作
- 迁移 `0006_chapterworkflow_deleted_at_and_more.py` 成功应用

**WARN-003 修复**: 软删除机制实现
- 添加了 `is_deleted` 和 `deleted_at` 字段到 ChapterWorkflow 和 WorkflowEvent
- 实现了 `soft_delete()`, `recover()`, `hard_delete()` 方法
- 更新了 `is_active` 属性排除已删除记录
- 更新了 Admin 配置：
  - 添加了 `is_deleted_badge` 显示删除状态
  - 添加了批量操作：软删除、恢复、永久删除
  - 添加了软删除字段到 fieldsets
- 添加了 `is_deleted` 索引优化查询性能

**测试验证**:
- 27 个测试用例全部通过（18个原始 + 9个软删除）✅
- 测试执行时间: 0.50s
- 测试覆盖率: 预计 >85%

### 实现文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `apps/artworks/models.py` | ✅ | 添加软删除字段和方法到两个模型 |
| `apps/artworks/admin.py` | ✅ | 修复重复注册，添加软删除支持 |
| `apps/artworks/tests/test_workflow_models.py` | ✅ | 添加9个软删除测试用例 |
| `apps/artworks/migrations/0006_chapterworkflow_deleted_at_and_more.py` | ✅ | 软删除字段迁移 |

### 最终评分

| 维度 | 第一轮修复 | 第二轮修复 | 最终 |
|--------|------------|------------|------|
| 架构合规性 | 9/10 | 10/10 | 10/10 |
| 需求完整性 | 10/10 | 10/10 | 10/10 |
| 代码安全性 | 9/10 | 10/10 | 10/10 |
| 可测试性 | 9/10 | 10/10 | 10/10 |
| 命名规范性 | 9/10 | 9/10 | 9/10 |

**综合评分**: **46/50 (92%)** → **49/50 (98%)** - 优秀级别 ✅

---

## ✅ Story 12-1.1 完成总结

### 全部完成功能

1. **数据模型** (100%)
   - ✅ ChapterWorkflow 模型：状态管理、进度追踪、错误处理
   - ✅ WorkflowEvent 模型：事件记录、元数据支持
   - ✅ 软删除支持：is_deleted/deleted_at 字段和管理方法

2. **Django Admin** (100%)
   - ✅ ChapterWorkflowAdmin：列表展示、过滤、批量操作
   - ✅ WorkflowEventAdmin：只读事件查看
   - ✅ 软删除操作：软删除、恢复、永久删除

3. **单元测试** (100%)
   - ✅ 27 个测试用例全部通过
   - ✅ 测试覆盖：模型创建、状态转换、进度计算、软删除

4. **数据库迁移** (100%)
   - ✅ 迁移文件生成和应用成功
   - ✅ 索引优化：workflow_id, chapter+created_at, is_deleted

### 验收标准完成

| 验收标准 | 状态 |
|----------|------|
| ChapterWorkflow 模型包含所有必需字段 | ✅ |
| WorkflowEvent 模型能记录事件历史 | ✅ |
| Admin 界面可以查看和编辑工作流 | ✅ |
| 数据库迁移成功执行 | ✅ |
| 单元测试通过 | ✅ |
| 代码评审修复全部完成 | ✅ |
| 软删除机制实现 | ✅ |
