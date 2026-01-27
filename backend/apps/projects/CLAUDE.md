# CLAUDE.md - 项目管理域 (projects)

[根目录](../../CLAUDE.md) > [backend](../) > [apps](../) > **projects**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

项目管理域是系统的**聚合根**，负责：
- 项目的生命周期管理（创建、启动、暂停、恢复、完成）
- 工作流阶段的状态追踪（5个阶段）
- Celery异步任务的编排和调度
- WebSocket实时通信
- 剪映草稿路径管理

---

## 入口与启动

### 主要入口文件

| 文件 | 职责 |
|------|------|
| [models.py](./models.py) | Project, ProjectStage, ProjectModelConfig 领域模型 |
| [views.py](./views.py) | ProjectViewSet（18个action，704行） |
| [tasks.py](./tasks.py) | Celery异步任务（execute_llm_stage等） |
| [consumers.py](./consumers.py) | WebSocket消费者（实时进度推送） |
| [services.py](./services.py) | 业务服务层 |
| [urls.py](./urls.py) | URL路由配置 |
| [serializers.py](./serializers.py) | DRF序列化器 |
| [sse_views.py](./sse_views.py) | SSE流式响应视图（备用） |
| [routing.py](./routing.py) | WebSocket路由配置 |

### 启动流程

```
用户创建项目 → ProjectViewSet.create()
    ↓
调用 Pipeline 工作流
    ↓
触发 Celery 异步任务 (tasks.py)
    ↓
通过 Redis Pub/Sub 推送进度
    ↓
前端 WebSocket 接收实时数据 (consumers.py)
```

---

## 对外接口

### REST API 端点

**基础路径:** `/api/v1/projects/`

| 端点 | 方法 | Action | 说明 |
|------|------|--------|------|
| `/` | GET | list | 项目列表 |
| `/` | POST | create | 创建项目 |
| `/{id}/` | GET | retrieve | 项目详情 |
| `/{id}/` | PUT/PATCH | update | 更新项目 |
| `/{id}/` | DELETE | destroy | 删除项目 |
| `/{id}/start/` | POST | start | 启动工作流 |
| `/{id}/pause/` | POST | pause | 暂停工作流 |
| `/{id}/resume/` | POST | resume | 恢复工作流 |
| `/{id}/retry/` | POST | retry | 重试失败阶段 |
| `/{id}/stages/` | GET | stages | 获取阶段列表 |
| `/{id}/stages/{stage_type}/` | GET | stage_detail | 阶段详情 |
| `/{id}/rollback/` | POST | rollback | 回滚到指定阶段 |

### WebSocket 端点

**路径:** `ws://localhost:8000/ws/projects/{project_id}/`

**消息格式:**
```json
{
  "type": "stage_update",
  "stage": "rewrite",
  "status": "processing",
  "progress": 50,
  "message": "正在生成文案..."
}
```

---

## 关键依赖与配置

### 依赖的内部模块

```python
# 领域模型依赖
from apps.prompts.models import PromptTemplateSet
from apps.models.models import ModelProvider
from apps.content.models import ContentRewrite, Storyboard

# 核心服务依赖
from core.pipeline.orchestrator import ProjectPipeline
from core.redis import RedisStreamPublisher

# Celery 配置
from config.celery import app
```

### Celery 队列配置

```python
# 任务队列定义
@app.task(
    bind=True,
    max_retries=0,
    soft_time_limit=600,  # 10分钟软超时
    time_limit=900  # 15分钟硬超时
)
def execute_llm_stage(self, project_id, stage_name, input_data, user_id):
    """执行LLM阶段任务"""
    pass
```

---

## 数据模型

### Project (项目聚合根)

```python
class Project(models.Model):
    """项目聚合根"""
    id = UUIDField(primary_key=True)
    name = CharField(max_length=255)
    description = TextField(blank=True)
    original_topic = TextField()  # 原始主题

    # 状态机: draft → processing → completed/failed/paused
    status = CharField(choices=[
        'draft', 'processing', 'completed', 'failed', 'paused'
    ])

    # 关联
    prompt_template_set = ForeignKey('prompts.PromptTemplateSet')
    user = ForeignKey('users.User')

    # 剪映草稿路径
    jianying_draft_path = CharField(max_length=500, blank=True)

    # 时间戳
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    completed_at = DateTimeField(null=True)
```

### ProjectStage (工作流阶段)

```python
class ProjectStage(models.Model):
    """工作流阶段追踪"""
    STAGE_TYPES = [
        'rewrite',          # 文案改写
        'storyboard',       # 分镜生成
        'image_generation', # 文生图
        'camera_movement',  # 运镜生成
        'video_generation', # 图生视频
    ]

    STATUS_CHOICES = [
        'pending', 'processing', 'completed', 'failed'
    ]

    project = ForeignKey(Project, related_name='stages')
    stage_type = CharField(choices=STAGE_TYPES)
    status = CharField(choices=STATUS_CHOICES, default='pending')

    # 重试机制
    retry_count = IntegerField(default=0)
    max_retries = IntegerField(default=3)

    # 输入输出数据
    input_data = JSONField(default=dict)
    output_data = JSONField(default=dict)
    error_message = TextField(blank=True)

    # 时间戳
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
```

### ProjectModelConfig (项目模型配置)

```python
class ProjectModelConfig(models.Model):
    """项目AI模型配置"""
    project = ForeignKey(Project, related_name='model_configs')
    stage = CharField(choices=ProjectStage.STAGE_TYPES)

    # 多对多: 每个阶段可配置多个模型
    model_providers = ManyToManyField('models.ModelProvider')

    # 负载均衡策略
    load_balance_strategy = CharField(choices=[
        'round_robin',  # 轮询
        'random',       # 随机
        'weighted',     # 权重
        'least_loaded'  # 最少负载
    ], default='round_robin')
```

---

## 测试与质量

### 当前测试覆盖 (Day 6更新)

- ✅ **Views 38%覆盖** - `test_projects_views.py` (12个测试)
- ✅ **WebSocket 93%覆盖** - `test_websocket_consumers.py` (10个测试，6通过)
- ✅ **集成测试** - `tests/integration/` (19个测试，100%通过) 🏆
  - `test_project_creation_flow.py` (10个测试)
  - `test_workflow_trigger.py` (9个测试)

### 测试文件清单

```
tests/
├── test_projects_views.py           # 12个测试，Views基础测试
├── test_websocket_consumers.py      # 10个测试，WebSocket消费者
└── integration/
    ├── test_project_creation_flow.py  # 10个测试，项目创建流程
    └── test_workflow_trigger.py       # 9个测试，Celery任务触发
```

### 测试重点

1. **模型测试**
   - Project 状态机转换
   - ProjectStage 自动重试逻辑
   - 关联关系验证

2. **视图测试**
   - 18个 action 的功能测试
   - 权限控制测试
   - 参数验证测试

3. **任务测试**
   - Celery 任务执行流程
   - Redis Pub/Sub 消息推送
   - 超时和重试机制

---

## 常见问题 (FAQ)

### Q1: 项目状态如何流转？

**A:** 状态机规则：
- `draft` → `processing` (调用 start API)
- `processing` → `completed` (所有阶段成功)
- `processing` → `failed` (任一阶段失败且重试耗尽)
- `processing` ↔ `paused` (手动暂停/恢复)

### Q2: 如何重试失败的项目？

**A:** 调用 `POST /api/v1/projects/{id}/retry/`，系统会：
1. 重置失败阶段状态为 `pending`
2. 清空 error_message
3. 重新触发 Celery 任务

### Q3: WebSocket 连接失败怎么办？

**A:** 检查：
1. Django ASGI 服务器是否运行（`./run_asgi.sh`）
2. Redis 是否运行（Channels层依赖 Redis DB3）
3. 前端 WebSocket URL 配置是否正确

### Q4: 剪映草稿路径如何使用？

**A:** 路径存储在 `Project.jianying_draft_path`，由剪映草稿生成服务写入：
```python
from core.services.jianying_draft_service import JianyingDraftGenerator
generator = JianyingDraftGenerator()
generator.generate_draft(project)
```

---

## 相关文件清单

### 核心文件

```
backend/apps/projects/
├── models.py           # 领域模型（3个模型）
├── views.py            # API视图（18个action）
├── tasks.py            # Celery任务（3个任务）
├── consumers.py        # WebSocket消费者
├── services.py         # 业务服务层
├── serializers.py      # DRF序列化器
├── urls.py             # URL配置
├── sse_views.py        # SSE视图（备用）
├── routing.py          # WebSocket路由
├── admin.py            # Django Admin配置
├── apps.py             # App配置
├── utils.py            # 工具函数
└── migrations/         # 数据库迁移
    ├── 0001_initial.py
    └── 0002_project_jianying_draft_path.py
```

### 关键依赖

```
# 领域依赖
apps/prompts/           # 提示词管理
apps/models/            # 模型管理
apps/content/           # 内容生成
apps/users/             # 用户管理

# 核心依赖
core/pipeline/          # 工作流引擎
core/redis/             # Redis Pub/Sub
core/services/          # 剪映草稿服务

# 配置依赖
config/celery.py        # Celery配置
config/settings/        # Django配置
```

---

## 变更记录 (Changelog)

### 2026-01-26 12:08:52
- 初始化项目管理域文档
- 添加导航面包屑
- 完成接口、模型、测试覆盖分析
