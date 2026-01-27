# AI Story生成系统 - 后端框架

## 项目概述

这是一个基于Django 3.2.15的AI Story生成系统后端,严格遵循SOLID、KISS、DRY、YAGNI原则,采用分层架构设计。

## 技术栈

- **框架**: Django 3.2.15 + Django REST Framework
- **异步**: Celery + Redis
- **WebSocket**: Django Channels
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **容器化**: Docker + Docker Compose

## 项目结构

```
backend/
├── config/                    # Django配置
│   ├── settings/             # 分层设置(base/development/production)
│   ├── urls.py               # 主路由
│   ├── asgi.py               # ASGI配置
│   ├── wsgi.py               # WSGI配置
│   └── celery.py             # Celery配置
│
├── apps/                     # 应用模块
│   ├── projects/            # 项目管理
│   ├── prompts/             # 提示词管理
│   ├── models/              # AI模型管理
│   ├── content/             # 内容生成
│   └── users/               # 用户管理
│
├── core/                     # 核心抽象
│   ├── ai_client/           # AI客户端抽象层
│   │   ├── base.py          # 抽象基类
│   │   ├── openai_client.py
│   │   ├── text2image_client.py
│   │   └── image2video_client.py
│   │
│   └── pipeline/            # 工作流引擎
│       ├── base.py          # Pipeline抽象
│       └── orchestrator.py  # 编排器
│
│
└── manage.py                # Django管理脚本
```

## 快速开始

### 1. 环境准备

```bash
# 使用uv包管理器同步依赖 (推荐)
cd backend
uv sync

# 或使用传统方式
# python -m venv venv
# source venv/bin/activate  # Linux/Mac
# pip install -r requirements/development.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件,配置必要的环境变量
# 必须配置: SECRET_KEY, OPENAI_API_KEY或ANTHROPIC_API_KEY
```

**重要:** 环境变量说明请参考 `.env.example` 文件中的详细注释。

### 3. 服务启动顺序 (重要!)

**必须按照以下顺序启动服务:**

```bash
# 步骤1: 启动Redis (5个数据库分离架构)
docker run -d -p 6379:6379 redis:latest
# 验证: docker ps | grep redis

# 步骤2: 启动Celery Worker (3个队列: llm, image, video)
cd backend
uv run celery -A config worker -Q llm,image,video -l info
# 验证: 看到 "celery@xxx ready" 消息

# 步骤3: 启动Django ASGI服务器 (支持WebSocket)
cd backend
./run_asgi.sh
# 或手动启动: uv run python manage.py runserver
# 验证: 访问 http://localhost:8000/api/v1/health/

# 步骤4: 启动前端开发服务器 (新终端)
cd frontend
npm run dev
# 验证: 访问 http://localhost:3000
```

**为什么这个顺序很重要?**
- Django依赖Redis(Celery broker和Channels)
- Celery Worker需要在Django之前启动以处理异步任务
- WebSocket连接需要Django ASGI服务器运行

### 4. 初始化数据库

```bash
# 执行迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 4. 启动开发服务器

```bash
# 启动Django ASGI服务器 (支持WebSocket)
./run_asgi.sh

# 或手动启动
uv run python manage.py runserver
```

### 6. 访问后台

访问 http://localhost:8000/admin 使用超级用户登录

## 使用Docker

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 执行数据库迁移
docker-compose exec backend python manage.py migrate

# 创建超级用户
docker-compose exec backend python manage.py createsuperuser

# 停止服务
docker-compose down
```

## 核心设计原则

### SOLID原则

- **单一职责(SRP)**: 每个模型、处理器只负责一项功能
- **开闭原则(OCP)**: 通过继承扩展功能,无需修改核心代码
- **里氏替换(LSP)**: AI客户端可互相替换
- **接口隔离(ISP)**: 接口专一,避免胖接口
- **依赖倒置(DIP)**: 依赖抽象接口,而非具体实现

### 其他原则

- **KISS**: 保持简单,避免过度设计
- **DRY**: 代码复用,杜绝重复
- **YAGNI**: 只实现当前需要的功能

## 领域模型

### 项目管理域
- `Project`: 项目聚合根
- `ProjectStage`: 项目阶段状态追踪
- `ProjectModelConfig`: 项目模型配置

### 提示词管理域
- `PromptTemplateSet`: 提示词集
- `PromptTemplate`: 提示词模板

### 模型管理域
- `ModelProvider`: AI模型提供商
- `ModelUsageLog`: 模型使用日志

### 内容生成域
- `ContentRewrite`: 文案改写
- `Storyboard`: 分镜
- `GeneratedImage`: 生成图片
- `CameraMovement`: 运镜
- `GeneratedVideo`: 生成视频

## Pipeline工作流

系统使用责任链模式实现工作流:

```python
from core.pipeline import ProjectPipeline, PipelineContext
from apps.content.processors.rewrite import RewriteProcessor

# 创建Pipeline
pipeline = ProjectPipeline(stages=[
    RewriteProcessor(),
    # StoryboardProcessor(),
    # ImageGenerationProcessor(),
    # CameraMovementProcessor(),
    # VideoGenerationProcessor(),
])

# 执行工作流
context = await pipeline.execute(project_id='xxx')
```

## API文档

API端点遵循RESTful规范:

- `/api/v1/projects/` - 项目管理
- `/api/v1/prompts/` - 提示词管理
- `/api/v1/models/` - 模型管理
- `/api/v1/content/` - 内容生成

详细API文档启动服务后访问: http://localhost:8000/api/docs/

## 开发规范

### 代码风格

```bash
# 格式化代码
black .

# 代码检查
flake8 .
```

### 测试

本项目使用 **pytest + pytest-django + pytest-cov** 测试框架。

#### 测试框架配置

**配置文件:**
- `pytest.ini` - pytest主配置文件
- `tests/conftest.py` - 全局fixtures和钩子
- `tests/fixtures/` - 可复用的fixtures

**目录结构:**
```
backend/
├── pytest.ini              # pytest配置
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # 全局fixtures
│   ├── fixtures/           # 自定义fixtures
│   │   ├── __init__.py
│   │   └── sample_fixtures.py
│   └── test_*.py           # 测试文件
```

#### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_sample.py

# 运行特定测试函数
pytest tests/test_sample.py::test_pytest_installed

# 显示详细输出
pytest -v

# 显示打印输出
pytest -s
```

#### 覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=apps --cov=core --cov-report=html

# 在终端显示覆盖率
pytest --cov=apps --cov=core --cov-report=term-missing

# 生成XML报告（CI/CD）
pytest --cov=apps --cov=core --cov-report=xml

# 查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**覆盖率目标:**
- 当前基准: < 2% (Story 1.2建立)
- 目标: > 70%

#### 使用Fixtures

```python
import pytest

@pytest.mark.django_db
def test_project_creation(test_project):
    """使用test_project fixture"""
    assert test_project.name == '测试项目'
```

**可用fixtures:**
- `test_project` - 创建测试项目
- `test_user` - 创建测试用户
- `authenticated_client` - 已认证的客户端
- `mock_ai_response` - Mock AI API响应
- `sample_project_data` - 示例项目数据

更多fixtures参考 `tests/fixtures/sample_fixtures.py`

#### 验证测试框架

```bash
# 运行验证脚本
./verify_pytest.sh

# 手动验证
pytest --version              # 检查pytest版本
pytest --collect-only         # 列出所有测试
pytest tests/test_sample.py   # 运行示例测试
```

#### 测试标记

```python
@pytest.mark.unit
def test_unit_test():
    """单元测试"""

@pytest.mark.integration
@pytest.mark.django_db
def test_integration_test():
    """集成测试"""

@pytest.mark.slow
def test_slow_test():
    """慢速测试"""
```

```bash
# 只运行单元测试
pytest -m unit

# 排除慢速测试
pytest -m "not slow"
```

#### Mock AI客户端

系统提供了Mock AI客户端，用于离线测试和开发环境验证。

**启用Mock AI:**
```bash
# 方式1: 环境变量
export ENABLE_MOCK_AI=true

# 方式2: 在.env文件中
echo "ENABLE_MOCK_AI=true" >> .env

# 方式3: pytest fixture (自动启用)
# tests/conftest.py中的enable_mock_ai fixture
```

**Mock客户端类型:**
- `MockLLMClient` - 模拟文本生成 (文案改写、分镜生成、运镜生成)
- `MockText2ImageClient` - 模拟文生图 (返回占位图片URL)
- `MockImage2VideoClient` - 模拟图生视频 (返回示例视频URL)

**使用示例:**
```python
# 自动使用Mock客户端 (当ENABLE_MOCK_AI=true时)
from core.ai_client.factory import create_ai_client
client = create_ai_client(provider)  # 返回Mock实例

# 测试中使用fixture
@pytest.mark.unit
def test_with_mock_ai(enable_mock_ai):
    # Mock AI自动启用
    response = await client.generate("test prompt")
    assert response.success is True
```

**Mock响应数据:**
- 返回真实格式的假数据
- 模拟API延迟 (0.5-2秒)
- 包含metadata标记 (`is_mock: true`)
- 支持流式输出 (LLM)

**运行Mock AI测试:**
```bash
# 运行Mock AI客户端测试
pytest tests/test_mock_ai_clients.py -v

# 验证Mock客户端行为
pytest tests/test_mock_ai_clients.py::TestMockLLMClient -v
```

## Phase 1 - P0 MVP验证实施计划

**当前阶段:** Phase 1 - 系统稳定性验证 (预计3周)

**并行实施的3个Epic:**

### Epic 1: 测试基础设施 (进行中)
**目标:** 测试覆盖率从<2%提升到>70%

**当前进度:**
- ✅ Story 1.1: README文档完善 (进行中)
- ⏳ Story 1.2: 测试框架搭建(pytest + pytest-cov)
- ⏳ Story 1.3: Mock AI客户端实现
- ⏳ Story 1.4: 核心模块单元测试
- ⏳ Story 1.5: API集成测试
- ⏳ Story 1.6: 数据库迁移文档

**Phase 1完成标准:**
- ✅ 单元测试覆盖率>70%
- ✅ API集成测试100%覆盖
- ✅ Mock AI客户端正常工作

### Epic 2: 系统可观测性
**目标:** 实现结构化日志、健康检查和性能监控

**关键交付物:**
- ⏳ 结构化日志系统(JSON格式)
- ⏳ 健康检查端点(/api/v1/health/)
- ⏳ API错误日志中间件
- ⏳ Celery任务失败日志
- ⏳ API响应时间监控(P95)

**Phase 1完成标准:**
- ✅ 健康检查端点响应<200ms
- ✅ 结构化日志(JSON格式)完整记录
- ✅ API响应时间P95可监控

### Epic 3: 实时通信稳定性
**目标:** 确保WebSocket连接稳定可靠,进度推送及时准确

**关键交付物:**
- ⏳ WebSocket连接稳定性验证
- ⏳ 进度推送延迟优化(<500ms)
- ⏳ WebSocket自动重连机制
- ⏳ SSE备用方案

**Phase 1完成标准:**
- ✅ WebSocket实时进度推送正常工作
- ✅ WebSocket自动重连机制正常
- ✅ SSE降级方案可用

**详细实施计划:** 参见 `_bmad-output/planning-artifacts/implementation-plan.md`

---

## 下一步工作

**Phase 1后的规划:**

1. ✅ 基础框架搭建 (已完成)
2. ✅ 核心领域模型 (已完成)
3. ✅ AI客户端抽象层 (已完成)
4. ✅ Pipeline架构 (已完成)
5. ⏳ **Phase 1: 测试基础设施 + 可观测性 + 实时通信** (进行中)
6. ⏳ **Phase 2: 项目管理 + 内容生成工作流** (计划中)
7. ⏳ **Phase 3: 文件管理 + 开发者工具完善** (计划中)

## 许可证

MIT License

## 常见问题排查

### 服务启动问题

**1. Redis连接失败**
```bash
# 检查Redis是否运行
docker ps | grep redis
# 或
redis-cli ping  # 应该返回 PONG

# 解决: 启动Redis
docker run -d -p 6379:6379 redis:latest
```

**2. Celery Worker无法启动**
```bash
# 检查环境变量
cat .env | grep REDIS

# 常见错误: "Error reading redis config"
# 解决: 确保Redis先启动,检查REDIS_BROKER_URL配置

# 常见错误: "ImportError: No module named 'config'"
# 解决: 确保在backend目录下执行命令
```

**3. WebSocket连接失败**
```bash
# 检查Django ASGI服务器是否运行
curl http://localhost:8000/api/v1/health/

# 常见错误: "WebSocket connection failed"
# 解决: 使用run_asgi.sh而不是python manage.py runserver
```

### 数据库迁移问题

**如何执行迁移?**
```bash
# 查看完整迁移文档
cat docs/MIGRATIONS.md

# 快速迁移命令
python manage.py makemigrations
python manage.py migrate
```

**如何回滚迁移?**
```bash
# 查看完整迁移文档
cat docs/MIGRATIONS.md

# 快速回滚示例
python manage.py migrate projects 0001_initial
```

### 日志查看

```bash
# Django日志
tail -f logs/django.log

# Celery Worker日志
# 直接在终端查看,或重定向到文件
uv run celery -A config worker -Q llm,image,video -l info > logs/celery.log 2>&1

# Redis日志
docker logs -f <redis_container_id>
```

### 更多文档

- **项目架构:** 查看 [CLAUDE.md](../CLAUDE.md) 了解完整架构
- **Celery + Redis:** 查看 [docs/CELERY_REDIS_STREAMING.md](../docs/CELERY_REDIS_STREAMING.md)
- **前端文档:** 查看 [frontend/README.md](../frontend/README.md)
- **项目概览:** 查看 [docs/project-overview.md](../docs/project-overview.md)
