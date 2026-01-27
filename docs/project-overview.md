# AI Story 项目概览

**生成时间:** 2026-01-26T12:22:30Z
**项目类型:** Multi-part (Backend + Frontend)
**扫描级别:** Deep Scan

---

## 项目简介

**AI Story 生成系统** - 基于 Django + Vue 的 AI 驱动的故事脚本到视频的自动化生成平台。

**核心工作流:**
```
文案改写 → 分镜生成 → 文生图 → 运镜生成 → 图生视频
```

### 业务价值

- **自动化内容生成:** 从简单的主题描述自动生成完整的视频故事
- **多阶段 Pipeline:** 5 个独立但关联的处理阶段
- **AI 模型集成:** 支持 OpenAI、Stable Diffusion、Runway、ComfyUI 等多种 AI 模型
- **剪映草稿导出:** 生成剪映可识别的草稿格式,便于后期编辑
- **实时进度反馈:** WebSocket + Redis Pub/Sub 实现任务进度实时推送

---

## 技术栈总览

### 后端技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **Web 框架** | Django | 3.2.15 | Web 应用框架 |
| **API 框架** | Django REST Framework | 3.14.0 | RESTful API |
| **异步任务** | Celery | 5.5.0b2 | 异步任务处理 |
| **实时通信** | Django Channels | 4.0.0 | WebSocket 支持 |
| **消息队列** | Redis | 5.x | Celery broker + Pub/Sub |
| **数据库** | SQLite / PostgreSQL | - | 数据持久化 |
| **AI 集成** | aiohttp, requests | - | AI API 调用 |
| **包管理** | uv | - | Python 包管理器 |

### 前端技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | Vue.js | 2.7.14 | 前端框架 |
| **状态管理** | Vuex | 3.6.2 | 集中式状态管理 |
| **路由** | Vue Router | 3.6.5 | 客户端路由 |
| **HTTP 客户端** | Axios | 1.6.2 | API 请求 |
| **WebSocket** | Socket.IO Client | 4.6.1 | 实时通信 |
| **UI 框架** | Tailwind CSS | 3.4.17 | 原子化 CSS |
| **UI 组件** | daisyUI | 4.12.23 | 组件库 |
| **构建工具** | Webpack | 5.89.0 | 模块打包 |

---

## 架构类型

### 仓库类型

**Multi-part Project (多部分项目)**

本项目采用前后端分离架构,分为两个独立但紧密协作的部分:

1. **Backend (Django)** - 位于 `/backend/`
2. **Frontend (Vue)** - 位于 `/frontend/`

### 架构模式

**Backend:** 服务导向分层架构 (Service-Oriented Layered Architecture)

```
API 层 (DRF ViewSets)
    ↓
业务逻辑层 (Services + Tasks)
    ↓
工作流引擎 (Pipeline - 责任链模式)
    ↓
AI 客户端层 (Strategy + Factory 模式)
    ↓
数据层 (Django ORM)
```

**Frontend:** 组件化架构 (Component-Based Architecture)

```
视图层 (Views)
    ↓
组件层 (Components)
    ↓
状态管理 (Vuex)
    ↓
服务层 (API Services)
```

---

## 项目结构

```
ai_story/
├── backend/                 # Django 后端
│   ├── apps/                # 业务应用 (DDD)
│   │   ├── projects/        # 项目管理域 (聚合根)
│   │   ├── content/         # 内容生成域 (处理器)
│   │   ├── prompts/         # 提示词管理域
│   │   ├── models/          # 模型管理域
│   │   └── users/           # 用户管理域
│   ├── core/                # 核心基础设施
│   │   ├── ai_client/       # AI 客户端抽象层
│   │   ├── pipeline/        # Pipeline 工作流引擎
│   │   └── redis/           # Redis Pub/Sub
│   └── config/              # Django 配置
│
├── frontend/                # Vue 前端
│   ├── src/
│   │   ├── views/           # 页面视图
│   │   ├── components/      # 可复用组件
│   │   ├── store/           # Vuex 状态管理
│   │   ├── router/          # Vue Router
│   │   └── services/        # API 服务层
│   └── config/              # Webpack 配置
│
└── docs/                    # 项目文档
```

---

## 核心功能

### 1. 项目管理 (apps/projects)

**职责:** 项目的生命周期管理和工作流编排

**关键功能:**
- 项目 CRUD 操作
- 5 阶段工作流管理
- Celery 异步任务调度
- WebSocket 实时进度推送
- 任务重试和回滚机制

**主要 API:**
- `POST /api/v1/projects/` - 创建项目
- `GET /api/v1/projects/{id}/stages/` - 获取阶段列表
- `POST /api/v1/projects/{id}/execute_stage/` - 执行指定阶段
- `POST /api/v1/projects/{id}/retry/` - 重试失败阶段

### 2. 内容生成 (apps/content)

**职责:** Pipeline 阶段处理器实现

**处理器:**
- `LLMStageProcessor` - 文案改写、分镜生成
- `Text2ImageStageProcessor` - 文生图
- `Image2VideoStageProcessor` - 图生视频
- `CameraMovementProcessor` - 运镜参数生成

**数据模型:**
- `ContentRewrite` - 文案改写结果
- `Storyboard` - 分镜脚本
- `GeneratedImage` - 生成的图片
- `GeneratedVideo` - 生成的视频

### 3. 提示词管理 (apps/prompts)

**职责:** 提示词模板和全局变量管理

**关键功能:**
- 提示词集管理 (可复用)
- Jinja2 模板语法支持
- 全局变量定义和注入

### 4. 模型管理 (apps/models)

**职责:** AI 模型提供商和负载均衡

**关键功能:**
- 模型提供商注册
- 负载均衡策略 (轮询、随机、权重、最少负载)
- API 连接测试
- 使用日志和成本统计

---

## 集成架构

### Backend ↔ Frontend 通信

**REST API:**
- 前端通过 Axios 调用后端 REST API
- 认证: JWT (djangorestframework-simplejwt)

**WebSocket:**
- 后端: Django Channels + Daphne ASGI 服务器
- 前端: Socket.IO Client
- 用途: 实时任务进度推送

**SSE (备用):**
- Server-Sent Events 用于流式响应
- 当前推荐使用 Celery + WebSocket 方案

### Redis 数据库分离策略

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'      # 数据库0: Celery任务队列
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'  # 数据库1: Celery结果存储
REDIS_PUBSUB_URL = 'redis://localhost:6379/2'       # 数据库2: Pub/Sub专用
CHANNEL_LAYERS = {'hosts': ['redis://localhost:6379/3']}  # 数据库3: Channels专用
CACHES = {'LOCATION': 'redis://localhost:6379/4'}   # 数据库4: Django缓存
```

---

## 设计模式

### Backend 核心设计模式

1. **责任链模式 (Chain of Responsibility)**
   - 位置: `core/pipeline/`
   - 用途: Pipeline 工作流引擎

2. **策略模式 (Strategy)**
   - 位置: `core/ai_client/`
   - 用途: AI 客户端抽象层

3. **工厂模式 (Factory)**
   - 位置: `core/ai_client/factory.py`
   - 用途: AI 客户端实例化

4. **领域驱动设计 (DDD)**
   - 位置: `apps/`
   - 用途: 业务领域边界划分

---

## 快速开始

### 后端启动

```bash
cd backend

# 安装依赖
uv sync

# 数据库迁移
uv run python manage.py migrate

# 启动 ASGI 服务器 (支持 WebSocket)
./run_asgi.sh

# 启动 Celery Worker (新终端)
uv run celery -A config worker -Q llm,image,video -l info

# 启动 Redis (Docker)
docker run -d -p 6379:6379 redis:latest
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产构建
npm run build
```

### 访问地址

- 前端应用: http://localhost:3000
- 后端 API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin
- WebSocket: ws://localhost:8000/ws/projects/{project_id}/

---

## 相关文档

### 生成的文档

- [项目结构](./project-structure.md) - 仓库类型和项目部分
- [技术栈](./technology-stack.md) - 详细技术栈分析
- [源代码树分析](./source-tree-analysis.md) - 完整目录结构
- [现有文档清单](./existing-documentation-inventory.md) - 已有文档列表

### 后端架构

- [Backend 架构](./architecture-backend.md) _(To be generated)_
- [API 契约 - Backend](./api-contracts-backend.md) _(To be generated)_
- [数据模型 - Backend](./data-models-backend.md) _(To be generated)_

### 前端架构

- [Frontend 架构](./architecture-frontend.md) _(To be generated)_
- [组件清单](./component-inventory.md) _(To be generated)_

### 开发指南

- [开发指南](./development-guide.md) _(To be generated)_
- [集成架构](./integration-architecture.md) _(To be generated)_

### 现有文档 (根目录)

- [CLAUDE.md](../CLAUDE.md) - 项目主架构文档 (AI 友好)
- [README.md](../README.md) - 项目总体说明
- [SSE_IMPLEMENTATION.md](../SSE_IMPLEMENTATION.md) - SSE 实现指南
- [CELERY_REDIS_STREAMING.md](../backend/CELERY_REDIS_STREAMING.md) - Celery + Redis 流式架构

---

## 项目统计

### 代码规模

| 部分 | 文件数 | 代码行数 (约) |
|------|--------|---------------|
| Backend (Python) | 49+ | 3,266 LOC |
| Frontend (Vue/JS) | 50+ | 5,000+ LOC (估计) |
| **总计** | **100+** | **8,000+ LOC** |

### 测试覆盖

| 模块 | 测试文件 | 覆盖范围 |
|------|---------|---------|
| apps/mock_api | ✅ tests/test_views.py | Mock API 视图 |
| 其他模块 | ❌ 无 | **测试缺口大** |

---

## 下一步

1. **阅读架构文档** - 了解系统整体设计
2. **查看源代码树** - 熟悉项目结构
3. **探索现有文档** - 查看已有的技术文档
4. **开始开发** - 参考 [开发指南](./development-guide.md) _(待生成)_

---

**生成信息:**
- 工作流版本: 1.2.0
- 扫描模式: Deep Scan
- 生成时间: 2026-01-26T12:22:30Z
- 文档路径: `/home/code/ai_story/docs/`
