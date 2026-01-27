# Backend 架构文档

**生成时间:** 2026-01-26T12:23:00Z
**项目部分:** backend
**技术栈:** Django 3.2.15 + DRF + Celery + Channels

---

## 执行摘要

Backend 采用**服务导向分层架构**,遵循领域驱动设计 (DDD) 原则,将业务逻辑划分为独立的领域应用 (apps/)。

**核心特性:**
- 分层架构: API 层 → 业务逻辑层 → 工作流引擎 → AI 客户端层 → 数据层
- 领域驱动设计: 5 个独立业务域
- 设计模式: 责任链、策略、工厂模式
- 异步任务处理: Celery + Redis
- 实时通信: Django Channels + WebSocket

---

## 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Django | 3.2.15 | Web 框架 |
| DRF | 3.14.0 | REST API |
| Celery | 5.5.0b2 | 异步任务 |
| Channels | 4.0.0 | WebSocket |
| Redis | 5.x | 消息队列 + Pub/Sub |

### 架构模式

**服务导向分层架构 (Service-Oriented Layered Architecture)**

```
┌─────────────────────────────────────────┐
│  API 层 (DRF ViewSets)                  │
│  - HTTP 请求处理                         │
│  - 权限控制                              │
│  - 序列化/反序列化                       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  业务逻辑层 (Services + Tasks)           │
│  - 领域服务                              │
│  - Celery 异步任务                       │
│  - 业务编排                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  工作流引擎 (Pipeline)                   │
│  - 责任链模式                            │
│  - 阶段处理器编排                        │
│  - 上下文传递                            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  AI 客户端层 (Strategy + Factory)       │
│  - 策略模式                              │
│  - 工厂模式                              │
│  - AI 模型抽象                           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  数据层 (Django ORM)                     │
│  - 数据模型                              │
│  - 数据库操作                            │
│  - 事务管理                              │
└─────────────────────────────────────────┘
```

---

## 数据架构

### 领域模型

**项目管理域 (apps/projects)** - 聚合根
- `Project` - 项目主实体
- `ProjectStage` - 工作流阶段 (5 个阶段)
- `ProjectModelConfig` - 模型配置

**内容生成域 (apps/content)**
- `ContentRewrite` - 文案改写结果
- `Storyboard` - 分镜脚本
- `GeneratedImage` - 生成的图片
- `GeneratedVideo` - 生成的视频
- `CameraMovement` - 运镜参数

**提示词管理域 (apps/prompts)**
- `PromptTemplateSet` - 提示词集
- `PromptTemplate` - 提示词模板 (支持 Jinja2)
- `GlobalVariable` - 全局变量

**模型管理域 (apps/models)**
- `ModelProvider` - AI 模型提供商
- `ModelUsageLog` - 使用日志

**用户管理域 (apps/users)**
- `User` - 用户模型扩展

### 数据库

- **开发环境:** SQLite 3
- **生产环境:** PostgreSQL (推荐)

### Redis 数据库分离

```python
DB 0: Celery 任务队列
DB 1: Celery 结果存储
DB 2: Redis Pub/Sub (实时通知)
DB 3: Channels (WebSocket)
DB 4: Django 缓存
```

---

## API 设计

### REST API 端点

**基础路径:** `/api/v1/`

**项目管理 API:**
- `GET/POST /projects/` - 项目列表/创建
- `GET/PUT/DELETE /projects/{id}/` - 项目详情/更新/删除
- `POST /projects/{id}/execute_stage/` - 执行阶段
- `POST /projects/{id}/retry/` - 重试失败阶段
- `GET /projects/{id}/stages/` - 获取阶段列表

**提示词管理 API:**
- `GET/POST /prompts/sets/` - 提示词集列表/创建
- `GET/POST /prompts/templates/` - 模板列表/创建
- `GET/POST /prompts/variables/` - 全局变量列表/创建

**模型管理 API:**
- `GET/POST /models/providers/` - 模型提供商列表/创建
- `POST /models/providers/{id}/test/` - 测试连接

**内容管理 API:**
- `GET /content/rewrites/` - 文案改写列表
- `GET /content/storyboards/` - 分镜列表
- `GET /content/images/` - 图片列表
- `GET /content/videos/` - 视频列表

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

### 认证

- **方式:** JWT (JSON Web Token)
- **实现:** djangorestframework-simplejwt
- **Header:** `Authorization: Bearer <token>`

---

## 组件概览

### Pipeline 工作流引擎

**位置:** `core/pipeline/`

**职责:**
- 阶段处理器编排
- 责任链模式实现
- 上下文传递和状态管理

**关键类:**
- `StageProcessor` - 处理器基类
- `ProjectPipeline` - Pipeline 编排器

### AI 客户端层

**位置:** `core/ai_client/`

**职责:**
- AI 模型抽象
- 客户端实例化 (工厂模式)
- 负载均衡

**客户端实现:**
- `OpenAIClient` - OpenAI API (LLM)
- `Text2ImageClient` - 文生图 API
- `Image2VideoClient` - 图生视频 API
- `ComfyUIClient` - ComfyUI 集成
- Mock 客户端 (测试用)

### Redis Pub/Sub

**位置:** `core/redis/`

**职责:**
- 实时进度推送
- Celery 任务结果通知

**组件:**
- `RedisStreamPublisher` - 发布者
- `RedisStreamSubscriber` - 订阅者

---

## 开发工作流

### 开发环境设置

```bash
# 1. 安装依赖
cd backend
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 数据库迁移
uv run python manage.py migrate

# 4. 创建超级用户
uv run python manage.py createsuperuser

# 5. 启动 ASGI 服务器
./run_asgi.sh

# 6. 启动 Celery Worker (新终端)
uv run celery -A config worker -Q llm,image,video -l info

# 7. 启动 Redis (如果未运行)
docker run -d -p 6379:6379 redis:latest
```

### 开发命令

```bash
# 运行开发服务器
uv run python manage.py runserver

# 启动 ASGI 服务器 (支持 WebSocket)
./run_asgi.sh

# 创建数据库迁移
uv run python manage.py makemigrations
uv run python manage.py migrate

# Django Shell
uv run python manage.py shell

# 测试
uv run pytest
```

### 代码规范

**SOLID 原则:**
- 单一职责原则 (SRP)
- 开闭原则 (OCP)
- 里氏替换原则 (LSP)
- 接口隔离原则 (ISP)
- 依赖倒置原则 (DIP)

**重要原则:**
- 业务逻辑必须放在 `apps/` 目录下
- `core/` 目录仅存放通用基础设施代码

---

## 部署架构

### 生产环境要求

**服务器:**
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (前端构建)

**Python 依赖:**
见 `pyproject.toml`

### 环境变量

```bash
# Django
DJANGO_SECRET_KEY=<secret-key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=example.com

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI API Keys
OPENAI_API_KEY=<key>
STABLE_DIFFUSION_API_KEY=<key>
RUNWAY_API_KEY=<key>
```

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### ASGI 服务器

**生产环境推荐:** Daphne

```bash
daphne config.asgi:application -b 0.0.0.0 -p 8000
```

**备选:** Gunicorn + Uvicorn

---

## 测试策略

### 当前测试覆盖

- ✅ `apps/mock_api/tests/test_views.py` - Mock API 视图测试
- ❌ 其他模块 - **缺少测试**

### 测试建议

**单元测试:**
```python
# apps/projects/tests/test_models.py
class ProjectModelTest(TestCase):
    def test_project_creation(self):
        project = Project.objects.create(...)
        self.assertEqual(project.status, 'draft')

# apps/projects/tests/test_views.py
class ProjectViewSetTest(APITestCase):
    def test_create_project(self):
        response = self.client.post('/api/v1/projects/', ...)
        self.assertEqual(response.status_code, 201)
```

**集成测试:**
- Celery 任务测试
- WebSocket 连接测试
- Pipeline 工作流测试

---

## 监控和日志

### Celery 监控

```bash
# Flower (Celery 监控工具)
pip install flower
celery -A config flower
```

### Django 日志

配置在 `config/settings/base.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 性能优化

### 数据库优化

- `select_related()` - ForeignKey 优化
- `prefetch_related()` - ManyToMany 优化
- 数据库索引 - 常查询字段

### 缓存策略

- Redis 缓存 (DB 4)
- 查询结果缓存
- 模型配置缓存

### 异步任务

- Celery 任务队列分离 (llm, image, video)
- 任务优先级
- 超时和重试机制

---

## 安全性

### 认证和授权

- JWT 认证
- 基于用户的权限控制 (`IsAuthenticated`)
- 对象级权限控制 (用户只能访问自己的项目)

### 数据验证

- DRF Serializers 验证
- Django Form 验证
- SQL 注入防护 (ORM)

### CORS 配置

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://example.com",
]
```

---

## 相关文档

- [API 契约](./api-contracts-backend.md) _(To be generated)_
- [数据模型](./data-models-backend.md) _(To be generated)_
- [Celery + Redis 流式架构](../backend/CELERY_REDIS_STREAMING.md)
- [CLAUDE.md](../CLAUDE.md) - 项目主架构文档

---

**生成信息:**
- 扫描模式: Deep Scan
- 生成时间: 2026-01-26T12:23:00Z
