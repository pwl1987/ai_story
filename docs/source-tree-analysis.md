# Source Tree Analysis

**Generated:** 2026-01-26T12:20:00Z
**Scan Mode:** Deep Scan
**Project Type:** Multi-part (Backend + Frontend)

---

## Repository Structure

```
ai_story/                          # 项目根目录
├── backend/                       # [Part: backend] Django 后端
├── frontend/                      # [Part: frontend] Vue 前端
├── docs/                          # 生成的项目文档
├── _bmad/                         # BMAD 工作流配置
├── docker/                        # Docker 配置
├── CLAUDE.md                      # 项目主架构文档
├── pyproject.toml                 # Python 依赖 (uv)
├── docker-compose.yml             # Docker Compose 配置
├── README.md                      # 项目说明
└── .env.example                   # 环境变量示例
```

---

## Backend Structure (Part: backend)

**Technology:** Django 3.2.15 + DRF + Celery + Channels
**Root Path:** /home/code/ai_story/backend

```
backend/
├── manage.py                      # [Entry Point] Django 管理命令
├── run_asgi.sh                    # [Script] ASGI 服务器启动脚本
├── start_services.sh              # [Script] 服务启动脚本
├── pyproject.toml                 # → Parent project dependency
│
├── config/                        # [Critical] Django 配置目录
│   ├── __init__.py
│   ├── asgi.py                    # [Entry Point] ASGI 应用配置 (Channels)
│   ├── wsgi.py                    # WSGI 应用配置
│   ├── urls.py                    # [Integration] 根 URL 配置
│   ├── celery.py                  # [Config] Celery 配置
│   └── settings/                  # [Settings] 分层设置
│       ├── __init__.py
│       ├── base.py                # 基础配置 (数据库、应用、中间件)
│       ├── development.py         # 开发环境配置
│       └── production.py          # 生产环境配置
│
├── apps/                          # [Critical] 业务应用目录 (领域驱动设计)
│   ├── __init__.py
│   │
│   ├── projects/                  # [Domain] 项目管理域 (聚合根)
│   │   ├── __init__.py
│   │   ├── models.py              # Project, ProjectStage, ProjectModelConfig (203行)
│   │   ├── views.py               # ProjectViewSet (18个actions, 774行)
│   │   ├── tasks.py               # Celery 异步任务 (execute_llm_stage等)
│   │   ├── consumers.py           # WebSocket 消费者 (实时进度推送)
│   │   ├── services.py            # 业务服务层
│   │   ├── serializers.py         # DRF 序列化器
│   │   ├── urls.py                # [API] /api/v1/projects/
│   │   ├── sse_views.py           # SSE 流式响应视图 (备用)
│   │   ├── routing.py             # [WebSocket] ws/projects/{id}/
│   │   ├── admin.py               # Django Admin 配置
│   │   ├── utils.py               # 工具函数
│   │   └── migrations/            # 数据库迁移文件
│   │
│   ├── content/                   # [Domain] 内容生成域 (处理器)
│   │   ├── __init__.py
│   │   ├── models.py              # ContentRewrite, Storyboard, GeneratedImage等 (266行)
│   │   ├── views.py               # 内容 API 视图 (175行)
│   │   ├── urls.py                # [API] /api/v1/content/
│   │   └── processors/            # [Critical] Pipeline 阶段处理器
│   │       ├── __init__.py
│   │       ├── llm_stage.py       # LLM 处理器 (文案改写、分镜生成)
│   │       ├── text2image_stage.py # 文生图处理器
│   │       ├── image2video_stage.py # 图生视频处理器
│   │       └── camera_movement.py  # 运镜生成处理器
│   │
│   ├── prompts/                   # [Domain] 提示词管理域
│   │   ├── __init__.py
│   │   ├── models.py              # PromptTemplateSet, PromptTemplate等 (231行)
│   │   ├── views.py               # 提示词 API 视图 (566行)
│   │   ├── services.py            # 提示词渲染服务 (Jinja2)
│   │   ├── serializers.py         # DRF 序列化器
│   │   ├── urls.py                # [API] /api/v1/prompts/
│   │   ├── admin.py               # Django Admin 配置
│   │   ├── management/            # Django 管理命令
│   │   │   └── commands/
│   │   └── migrations/            # 数据库迁移文件
│   │
│   ├── models/                    # [Domain] 模型管理域
│   │   ├── __init__.py
│   │   ├── models.py              # ModelProvider, ModelUsageLog (169行)
│   │   ├── views.py               # 模型 API 视图 (375行)
│   │   ├── services.py            # 负载均衡服务
│   │   ├── serializers.py         # DRF 序列化器
│   │   ├── urls.py                # [API] /api/v1/models/
│   │   └── admin.py               # Django Admin 配置
│   │
│   ├── users/                     # [Domain] 用户管理域
│   │   ├── __init__.py
│   │   ├── models.py              # User 模型扩展 (9行)
│   │   ├── views.py               # 用户 API 视图 (149行)
│   │   ├── serializers.py         # DRF 序列化器
│   │   └── urls.py                # [API] /api/v1/users/
│   │
│   └── mock_api/                  # [Testing] Mock API (开发/测试用)
│       ├── __init__.py
│       ├── views.py               # Mock API 视图 (349行)
│       ├── urls.py                # [API] /api/v1/mock/
│       └── tests/                 # 测试文件
│           └── test_views.py      # Mock API 视图测试
│
├── core/                          # [Critical] 核心基础设施层 (不应包含业务逻辑)
│   ├── __init__.py
│   │
│   ├── ai_client/                 # [Infrastructure] AI 客户端抽象层
│   │   ├── __init__.py
│   │   ├── base.py                # AI 客户端抽象基类
│   │   ├── factory.py             # AI 客户端工厂模式
│   │   ├── registry.py            # 客户端注册表
│   │   ├── openai_client.py       # OpenAI 客户端实现
│   │   ├── text2image_client.py   # 文生图客户端
│   │   ├── image2video_client.py  # 图生视频客户端
│   │   ├── comfyui_client.py      # ComfyUI 客户端
│   │   ├── mock_llm_client.py     # Mock LLM 客户端 (测试)
│   │   ├── mock_text2image_client.py # Mock 文生图客户端
│   │   └── mock_image2video_client.py # Mock 图生视频客户端
│   │
│   ├── pipeline/                  # [Infrastructure] Pipeline 工作流引擎
│   │   ├── __init__.py
│   │   ├── base.py                # Pipeline 基类 (责任链模式)
│   │   └── orchestrator.py        # Pipeline 编排器
│   │
│   ├── redis/                     # [Infrastructure] Redis Pub/Sub 发布订阅
│   │   ├── __init__.py
│   │   ├── publisher.py           # Redis 发布者
│   │   └── subscriber.py          # Redis 订阅者
│   │
│   ├── services/                  # [Infrastructure] 基础服务
│   │   ├── jianying_draft_service.py # 剪映草稿生成服务
│   │
│   └── utils/                     # [Utilities] 工具函数
│       ├── file_storage.py        # 文件存储工具
│       ├── image_downloader.py    # 图片下载工具
│       ├── jianying.py            # 剪映格式处理
│       └── jianying copy.py       # 剪映格式处理 (备份)
│
├── docs/                          # [Documentation] 后端文档
│   ├── JIANYING_DRAFT_INTEGRATION.md  # 剪映草稿集成指南
│   └── JIANYING_QUICKSTART.md         # 剪映快速开始
│
├── test_celery_redis.py           # [Testing] Celery + Redis 测试
├── test_file_storage.py           # [Testing] 文件存储测试
└── test_mock_api.py               # [Testing] Mock API 测试

---

## Frontend Structure (Part: frontend)

**Technology:** Vue 2.7.14 + Vuex + daisyUI + Tailwind CSS
**Root Path:** /home/code/ai_story/frontend

```
frontend/
├── package.json                   # [Config] npm 依赖和脚本
├── package-lock.json              # npm 依赖锁定文件
├── tailwind.config.js             # [Config] Tailwind CSS 配置
├── postcss.config.js              # PostCSS 配置
├── .eslintrc.js                   # ESLint 配置
├── .babelrc.js                    # Babel 配置
├── .gitignore                     # Git 忽略文件
│
├── public/                        # [Static] 静态资源目录
│   └── index.html                 # HTML 入口模板
│
├── config/                        # [Critical] Webpack 构建配置
│   ├── webpack.dev.js             # 开发环境配置
│   └── webpack.prod.js            # 生产环境配置
│
└── src/                           # [Critical] 源代码目录
    ├── main.js                    # [Entry Point] Vue 应用入口
    ├── App.vue                    # [Root Component] 根组件
    ├── input.css                  # Tailwind 输入 CSS
    ├── output.css                 # 编译后的 CSS (不应提交)
    │
    ├── views/                     # [Critical] 页面视图组件 (路由级)
    │   ├── projects/              # [Feature] 项目管理模块
    │   │   ├── ProjectList.vue    # 项目列表页
    │   │   ├── ProjectDetail.vue  # 项目详情页
    │   │   └── StageContent.vue   # 阶段内容组件
    │   ├── prompts/               # [Feature] 提示词管理模块
    │   │   └── ...
    │   ├── models/                # [Feature] 模型管理模块
    │   │   └── ...
    │   └── ...                    # 其他页面视图
    │
    ├── components/                # [Critical] 可复用组件库
    │   ├── common/                # 通用组件
    │   ├── project/               # 项目相关组件
    │   └── ...                    # 其他可复用组件
    │
    ├── store/                     # [State Management] Vuex 状态管理
    │   ├── index.js               # Vuex Store 入口
    │   └── modules/               # [Modules] Vuex 模块
    │       ├── projects.js        # 项目状态模块
    │       ├── prompts.js         # 提示词状态模块
    │       ├── models.js          # 模型状态模块
    │       └── ...                # 其他状态模块
    │
    ├── router/                    # [Routing] Vue Router 配置
    │   └── index.js               # 路由定义
    │
    ├── services/                  # [Service Layer] API 服务层
    │   └── api/                   # API 客户端
    │       ├── client.js          # Axios 客户端配置
    │       ├── projects.js        # 项目 API
    │       ├── prompts.js         # 提示词 API
    │       └── models.js          # 模型 API
    │
    ├── utils/                     # [Utilities] 工具函数
    │   └── ...                    # 通用工具函数
    │
    └── assets/                    # [Assets] 资源文件
        └── ...                    # 图片、字体等

---

## Critical Directories Summary

### Backend Critical Directories

| Directory | Purpose | File Count (approx) |
|-----------|---------|-------------------|
| `config/settings/` | Django 分层配置 | 3 files |
| `apps/projects/` | 项目管理域 (聚合根) | 13 files |
| `apps/content/` | 内容生成域 (处理器) | 11 files |
| `apps/prompts/` | 提示词管理域 | 10 files |
| `apps/models/` | 模型管理域 | 7 files |
| `apps/users/` | 用户管理域 | 5 files |
| `core/ai_client/` | AI 客户端抽象层 | 10 files |
| `core/pipeline/` | Pipeline 工作流引擎 | 2 files |
| `core/redis/` | Redis Pub/Sub | 2 files |

### Frontend Critical Directories

| Directory | Purpose | File Count (approx) |
|-----------|---------|-------------------|
| `config/` | Webpack 构建配置 | 2 files |
| `src/views/` | 页面视图组件 | 10+ files |
| `src/components/` | 可复用组件 | 20+ files |
| `src/store/modules/` | Vuex 状态模块 | 5+ files |
| `src/services/api/` | API 服务层 | 5+ files |
| `src/router/` | Vue Router 配置 | 1 file |

---

## Entry Points

### Backend Entry Points

| File | Type | Purpose |
|------|------|---------|
| `manage.py` | Django CLI | Django 管理命令入口 |
| `config/asgi.py` | ASGI App | ASGI 应用 (WebSocket 支持) |
| `config/wsgi.py` | WSGI App | WSGI 应用 (生产环境) |
| `config/celery.py` | Celery App | Celery 应用入口 |
| `run_asgi.sh` | Shell Script | ASGI 服务器启动脚本 |

### Frontend Entry Points

| File | Type | Purpose |
|------|------|---------|
| `src/main.js` | JavaScript | Vue 应用入口 |
| `public/index.html` | HTML | HTML 模板 |
| `config/webpack.dev.js` | Webpack Config | 开发环境构建配置 |

---

## Integration Points

### Backend → Frontend Integration

**REST API Endpoints:**
- Projects: `/api/v1/projects/` → `src/services/api/projects.js`
- Prompts: `/api/v1/prompts/` → `src/services/api/prompts.js`
- Models: `/api/v1/models/` → `src/services/api/models.js`
- Content: `/api/v1/content/` → `src/services/api/content.js`

**WebSocket Endpoints:**
- `ws://localhost:8000/ws/projects/{id}/` → `src/utils/websocket.js`

### Backend Internal Integration

**Cross-Domain Dependencies:**
```
projects (聚合根)
  ├─→ prompts (提示词管理)
  ├─→ models (模型管理)
  └─→ content (内容生成)
       └─→ core/pipeline (工作流引擎)
            └─→ core/ai_client (AI 客户端)
                 └─→ core/redis (Redis Pub/Sub)
```

---

## File Statistics

### Backend Python Files (excluding migrations)

| App | Views (LOC) | Models (LOC) | Total Files |
|-----|-----------|-------------|-------------|
| projects | 774 | 203 | 13 |
| prompts | 566 | 231 | 10 |
| models | 375 | 169 | 7 |
| content | 175 | 266 | 11 |
| users | 149 | 9 | 5 |
| mock_api | 349 | 0 | 3 |
| **Total** | **2388** | **878** | **49** |

### Frontend Files (estimated)

| Type | Count (approx) |
|------|---------------|
| Vue Components | 30+ |
| Vuex Modules | 5+ |
| API Services | 5+ |
| Utils | 10+ |
| **Total** | **50+** |

---

## Key Configuration Files

### Backend Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python 依赖 (uv) |
| `config/settings/base.py` | Django 基础配置 |
| `config/settings/development.py` | 开发环境配置 |
| `config/settings/production.py` | 生产环境配置 |
| `config/celery.py` | Celery 任务队列配置 |
| `.env.example` | 环境变量模板 |

### Frontend Configuration

| File | Purpose |
|------|---------|
| `package.json` | npm 依赖和脚本 |
| `tailwind.config.js` | Tailwind CSS 配置 |
| `postcss.config.js` | PostCSS 配置 |
| `config/webpack.dev.js` | Webpack 开发配置 |
| `config/webpack.prod.js` | Webpack 生产配置 |
| `.eslintrc.js` | ESLint 代码检查配置 |
| `.babelrc.js` | Babel 转译配置 |

---

## Development vs Production Structure

### Development Environment

```
backend/
├── db.sqlite3                    # SQLite 开发数据库
└── .env                          # 本地环境变量

frontend/
└── output.css                    # 编译后的 CSS (开发)
```

### Production Environment

```
backend/
├── PostgreSQL database           # 生产数据库
├── .env (production)             # 生产环境变量
└── static/                       # 静态文件收集

frontend/
├── dist/                         # Webpack 生产构建输出
└── (served by Nginx)             # Nginx 静态文件服务
```

---

## Summary

- **Total Directories:** 50+ critical directories
- **Total Python Files:** 49+ (excluding migrations)
- **Total Vue Files:** 30+ components
- **Entry Points:** 5 backend, 3 frontend
- **Integration Points:** REST API + WebSocket

**Architecture:** Clean separation of concerns with DDD (Domain-Driven Design) in backend and Component-Based Architecture in frontend.
