# AI Story 项目文档索引

**生成时间:** 2026-01-26T12:25:00Z
**扫描模式:** Deep Scan
**工作流版本:** 1.2.0

> 👆 **这是 AI 辅助开发的主要入口点**

---

## 项目概览

- **类型:** Multi-part (多部分项目),包含 2 个部分
- **主要语言:** Python (Backend), JavaScript (Frontend)
- **架构:** 服务导向分层架构 (Backend) + 组件化架构 (Frontend)

---

## 快速参考

### Backend (Django)

- **技术栈:** Django 3.2.15 + DRF + Celery + Channels
- **入口点:** `backend/manage.py`, `backend/config/asgi.py`
- **架构模式:** 服务导向分层架构
- **数据库:** SQLite (dev) / PostgreSQL (prod)
- **消息队列:** Redis (5 个数据库)

### Frontend (Vue)

- **技术栈:** Vue 2.7.14 + Vuex + daisyUI + Tailwind CSS
- **入口点:** `frontend/src/main.js`
- **架构模式:** 组件化架构
- **构建工具:** Webpack 5.89.0
- **HTTP 客户端:** Axios
- **WebSocket:** Socket.IO Client

---

## 生成的文档

### 核心文档

- [项目概览](./project-overview.md) - 项目简介、技术栈、核心功能
- [项目结构](./project-structure.md) - 仓库类型和项目部分分析
- [技术栈](./technology-stack.md) - 详细技术栈分析
- [源代码树分析](./source-tree-analysis.md) - 完整目录结构注释
- [现有文档清单](./existing-documentation-inventory.md) - 已有文档列表

### 架构文档

- [Backend 架构](./architecture-backend.md) - Django 后端架构详解
- [Frontend 架构](./architecture-frontend.md) - Vue 前端架构详解

### 详细文档 _(待生成)_

- [API 契约 - Backend](./api-contracts-backend.md) _(To be generated)_
- [数据模型 - Backend](./data-models-backend.md) _(To be generated)_
- [组件清单](./component-inventory.md) _(To be generated)_
- [开发指南](./development-guide.md) _(To be generated)_
- [集成架构](./integration-architecture.md) _(To be generated)_

---

## 现有文档 (根目录)

### 项目级文档

- [CLAUDE.md](../CLAUDE.md) - **项目主架构文档** (AI 友好,最重要)
- [README.md](../README.md) - 项目总体说明
- [AGENTS.md](../AGENTS.md) - Agent 开发指南
- [GEMINI.md](../GEMINI.md) - Gemini AI 集成文档

### 技术实现文档

- [SSE_IMPLEMENTATION.md](../SSE_IMPLEMENTATION.md) - SSE 实现指南
- [SSE_STREAMING_IMPLEMENTATION.md](../SSE_STREAMING_IMPLEMENTATION.md) - SSE 流式实现

### Backend 文档

- [Backend README](../backend/README.md) - 后端应用说明
- [API_MIGRATION_GUIDE.md](../backend/API_MIGRATION_GUIDE.md) - API 迁移指南
- [ASYNC_OPTIMIZATION.md](../backend/ASYNC_OPTIMIZATION.md) - 异步优化策略
- [CELERY_REDIS_STREAMING.md](../backend/CELERY_REDIS_STREAMING.md) - **Celery + Redis 流式架构** (重要,523 行)
- [GLOBAL_VARIABLES.md](../backend/GLOBAL_VARIABLES.md) - 全局变量管理
- [MOCK_API_GUIDE.md](../backend/MOCK_API_GUIDE.md) - Mock API 使用指南
- [JIANYING_DRAFT_INTEGRATION.md](../backend/docs/JIANYING_DRAFT_INTEGRATION.md) - 剪映草稿集成
- [JIANYING_QUICKSTART.md](../backend/docs/JIANYING_QUICKSTART.md) - 剪映快速开始

### Frontend 文档

- [Frontend README](../frontend/README.md) - 前端应用说明
- [FRONTEND_MIGRATION_GUIDE.md](../frontend/FRONTEND_MIGRATION_GUIDE.md) - 前端迁移指南
- [GLOBAL_VARIABLES_GUIDE.md](../frontend/GLOBAL_VARIABLES_GUIDE.md) - 前端全局变量
- [SSE_CONNECTION_FIX.md](../frontend/SSE_CONNECTION_FIX.md) - SSE 连接修复
- [SSE_INTEGRATION.md](../frontend/SSE_INTEGRATION.md) - SSE 集成指南
- [STAGECONTENT_SSE_USAGE.md](../frontend/STAGECONTENT_SSE_USAGE.md) - StageContent SSE 使用

### Generated Docs (docs/)

- [PROJECT_MANAGEMENT_GUIDE.md](./PROJECT_MANAGEMENT_GUIDE.md) - 项目管理指南
- [PROMPT_MANAGEMENT_DESIGN.md](./PROMPT_MANAGEMENT_DESIGN.md) - 提示词管理设计

---

## 快速开始

### 后端启动

```bash
cd backend

# 安装依赖
uv sync

# 数据库迁移
uv run python manage.py migrate

# 启动 ASGI 服务器
./run_asgi.sh

# 启动 Celery Worker (新终端)
uv run celery -A config worker -Q llm,image,video -l info

# 启动 Redis
docker run -d -p 6379:6379 redis:latest
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问地址

- 前端应用: http://localhost:3000
- 后端 API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin
- WebSocket: ws://localhost:8000/ws/projects/{project_id}/

---

## 项目部分详情

### Part 1: Backend

**类型:** backend
**技术栈:** Django 3.2.15 on Python 3.11+
**根路径:** `/home/code/ai_story/backend`

**核心域 (apps/):**
- `projects/` - 项目管理域 (聚合根)
- `content/` - 内容生成域 (处理器)
- `prompts/` - 提示词管理域
- `models/` - 模型管理域
- `users/` - 用户管理域

**核心基础设施 (core/):**
- `ai_client/` - AI 客户端抽象层
- `pipeline/` - Pipeline 工作流引擎
- `redis/` - Redis Pub/Sub

### Part 2: Frontend

**类型:** web
**技术栈:** Vue 2.7.14 on JavaScript ES6+
**根路径:** `/home/code/ai_story/frontend`

**核心目录:**
- `src/views/` - 页面视图组件
- `src/components/` - 可复用组件
- `src/store/` - Vuex 状态管理
- `src/router/` - Vue Router
- `src/services/` - API 服务层

---

## 集成架构

### Backend ↔ Frontend 通信

**REST API:**
- Projects: `/api/v1/projects/`
- Prompts: `/api/v1/prompts/`
- Models: `/api/v1/models/`
- Content: `/api/v1/content/`

**WebSocket:**
- `ws://localhost:8000/ws/projects/{id}/`

### Redis 数据库分离

```
DB 0: Celery 任务队列
DB 1: Celery 结果存储
DB 2: Redis Pub/Sub
DB 3: Channels (WebSocket)
DB 4: Django 缓存
```

---

## 核心功能

### 1. 项目管理 (apps/projects)

- 项目 CRUD 操作
- 5 阶段工作流管理
- Celery 异步任务调度
- WebSocket 实时进度推送

### 2. 内容生成 (apps/content)

- 文案改写 (LLM)
- 分镜生成 (LLM)
- 文生图 (Text2Image)
- 运镜生成 (Camera Movement)
- 图生视频 (Image2Video)

### 3. 提示词管理 (apps/prompts)

- 提示词集管理
- Jinja2 模板支持
- 全局变量定义

### 4. 模型管理 (apps/models)

- AI 模型提供商管理
- 负载均衡策略
- API 连接测试

---

## 设计模式

### Backend

- **责任链模式:** Pipeline 工作流引擎
- **策略模式:** AI 客户端抽象
- **工厂模式:** AI 客户端工厂
- **领域驱动设计 (DDD):** apps/ 业务域划分

### Frontend

- **组件模式:** 可复用 UI 组件
- **状态模式:** Vuex 状态管理
- **观察者模式:** Vue 响应式系统

---

## 开发指南

### Backend 开发

**重要原则:** 业务逻辑必须放在 `apps/` 目录下,`core/` 目录仅存放通用基础设施代码

**关键文件:**
- `backend/apps/projects/views.py` (774 行)
- `backend/apps/projects/models.py` (203 行)
- `backend/apps/projects/tasks.py` (Celery 任务)

### Frontend 开发

**关键文件:**
- `frontend/src/views/projects/ProjectList.vue`
- `frontend/src/store/modules/projects.js`
- `frontend/src/services/api/projects.js`

---

## 测试覆盖

### 当前测试

- ✅ `apps/mock_api/tests/test_views.py` - Mock API 视图测试
- ❌ 其他模块 - **测试缺口大**

### 需要添加测试

- `apps/projects/` - 项目管理测试
- `apps/content/` - 处理器测试
- `apps/prompts/` - 提示词管理测试
- `core/ai_client/` - AI 客户端测试
- `core/pipeline/` - Pipeline 工作流测试

---

## 部署

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 环境变量

参考 `.env.example` 文件配置:
- Django SECRET_KEY
- Redis 连接
- AI API Keys

---

## 项目统计

| 部分 | 文件数 | 代码行数 (约) |
|------|--------|---------------|
| Backend (Python) | 49+ | 3,266 LOC |
| Frontend (Vue/JS) | 50+ | 5,000+ LOC |
| **总计** | **100+** | **8,000+ LOC** |

---

## 常见问题

### Q1: 如何重试失败的项目?

**A:** 调用 `POST /api/v1/projects/{id}/retry/`,系统会重置失败阶段并重新触发任务。

### Q2: WebSocket 连接失败怎么办?

**A:** 检查:
1. ASGI 服务器是否运行 (`./run_asgi.sh`)
2. Redis 是否运行 (Channels 依赖 Redis DB3)
3. 前端 WebSocket URL 配置是否正确

### Q3: 如何添加新的 AI 模型?

**A:**
1. 在 `core/ai_client/` 创建新的客户端类
2. 继承 `BaseAIClient` 接口
3. 在 `registry.py` 注册客户端
4. 在 ModelProvider 中配置

---

## 下一步

1. **阅读 CLAUDE.md** - 了解项目整体架构 (最重要)
2. **查看 Backend 架构** - 理解后端设计
3. **查看 Frontend 架构** - 理解前端设计
4. **探索源代码树** - 熟悉项目结构
5. **开始开发** - 参考现有代码和文档

---

## 项目资源

### 代码仓库

- **Backend:** `/home/code/ai_story/backend/`
- **Frontend:** `/home/code/ai_story/frontend/`
- **根目录:** `/home/code/ai_story/`

### 文档位置

- **生成文档:** `/home/code/ai_story/docs/`
- **现有文档:** 根目录和各子目录的 `*.md` 文件

### 配置文件

- **Backend:** `pyproject.toml`, `docker-compose.yml`
- **Frontend:** `package.json`, `tailwind.config.js`

---

**生成信息:**
- 工作流版本: 1.2.0
- 扫描模式: Deep Scan
- 生成时间: 2026-01-26T12:25:00Z
- 文档路径: `/home/code/ai_story/docs/`
- 状态文件: `/home/code/ai_story/docs/project-scan-report.json`

---

**AI 辅助开发提示:**
当创建 brownfield PRD 时,请将此索引文件 (`/home/code/ai_story/docs/index.md`) 作为输入提供给 PRD 工作流。
