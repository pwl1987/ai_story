# Story 1.1: README文档完善

Status: done

## Story

作为开发者,
我希望有清晰的README文档,
以便快速理解项目结构和启动开发环境

## Acceptance Criteria

1. **Given** 开发者克隆项目到本地
2. **When** 阅读README.md文件
3. **Then** 包含项目概述、技术栈、快速启动指南
4. **And** 包含依赖安装说明(uv + npm)
5. **And** 包含服务启动顺序(Redis → Celery → Django → 前端)
6. **And** 包含常见问题排查链接
7. **And** 包含环境变量配置(.env示例)
8. **And** 包含数据库迁移命令

## Tasks / Subtasks

- [x] 审查现有backend/README.md和frontend/README.md (AC: 3)
  - [x] 检查项目概述完整性
  - [x] 验证技术栈版本信息准确性
  - [x] 确认快速启动指南可执行性
- [x] 更新依赖安装说明 (AC: 4)
  - [x] 添加uv包管理器使用说明
  - [x] 更新npm依赖安装步骤
  - [x] 验证依赖列表完整性
- [x] 添加服务启动顺序说明 (AC: 5)
  - [x] 文档化Redis 5数据库分离架构启动步骤
  - [x] 添加Celery worker启动命令和队列说明
  - [x] 添加Django ASGI服务器启动(run_asgi.sh)
  - [x] 添加前端开发服务器启动步骤
- [x] 创建.env示例文件 (AC: 7)
  - [x] 创建backend/.env.example
  - [x] 包含所有必需的环境变量
  - [x] 添加变量说明和默认值
- [x] 添加数据库迁移文档引用 (AC: 8)
  - [x] 链接到CLAUDE.md中的数据库迁移说明
  - [x] 添加常用迁移命令快速参考
- [x] 添加常见问题排查部分 (AC: 6)
  - [x] 链接到docs/目录下的文档
  - [x] 添加快速故障排查步骤
  - [x] 包含日志查看方法

## Dev Notes

### 现有README状态分析

**Backend README (backend/README.md):**
- ✅ 已有项目概述和技术栈说明
- ✅ 已有项目结构图
- ⚠️ 使用pip而非uv (需要更新)
- ⚠️ 缺少服务启动顺序说明
- ⚠️ 缺少环境变量配置示例
- ⚠️ 缺少常见问题排查部分

**Frontend README (frontend/README.md):**
- ✅ 已有技术栈说明
- ✅ 已有项目结构图
- ✅ 已有npm install说明
- ⚠️ 缺少与后端集成的环境变量配置
- ⚠️ 缺少常见问题排查部分

### 需要补充的关键内容

#### 1. 服务启动顺序 (关键!)

当前README缺少这个**至关重要**的信息。正确的启动顺序:

```bash
# 步骤1: 启动Redis (5个数据库)
docker run -d -p 6379:6379 redis:latest

# 步骤2: 启动Celery Worker (3个队列: llm, image, video)
cd backend
uv run celery -A config worker -Q llm,image,video -l info

# 步骤3: 启动Django ASGI服务器 (支持WebSocket)
./run_asgi.sh

# 步骤4: 启动前端开发服务器
cd frontend
npm run dev
```

#### 2. 环境变量配置

创建`.env.example`文件示例:

```env
# Django配置
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DATABASE_URL=sqlite:///db.sqlite3

# Redis配置 (5个数据库分离)
REDIS_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_PUBSUB_URL=redis://localhost:6379/2
CHANNEL_LAYER_REDIS=redis://localhost:6379/3
CACHE_REDIS=redis://localhost:6379/4

# AI API密钥
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk--ant-...

# Celery配置
CELERY_TASK_ALWAYS_EAGER=False
```

#### 3. uv包管理器说明

替换现有的pip命令:

```bash
# 使用uv同步依赖
cd backend
uv sync

# 使用uv运行命令
uv run python manage.py migrate
uv run python manage.py runserver
```

### Project Structure Notes

**README文档放置位置:**
- backend/README.md (后端开发文档)
- frontend/README.md (前端开发文档)
- README.md (根目录,项目总览)

**环境变量文件:**
- backend/.env.example (后端环境变量模板)
- frontend/.env.example (前端环境变量模板)
- .gitignore必须包含.env以防止密钥泄露

### 技术要求详解

1. **更新backend/README.md:**
   - 第52-62行: 将pip install替换为uv sync
   - 新增章节: "服务启动顺序" (在"启动开发服务器"之前)
   - 新增章节: "环境变量配置" (链接到.env.example)
   - 新增章节: "常见问题排查" (链接到docs/)

2. **更新frontend/README.md:**
   - 新增章节: "与后端集成" (说明API_BASE_URL和WS_URL)
   - 新增章节: "环境变量配置" (链接到.env.example)
   - 新增章节: "常见问题排查"

3. **创建backend/.env.example:**
   - 包含所有必需的环境变量
   - 添加注释说明每个变量的用途
   - 提供安全的默认值

4. **创建frontend/.env.example:**
   - VUE_APP_API_BASE_URL
   - VUE_APP_WS_URL

5. **添加故障排查链接:**
   - 链接到CLAUDE.md (快速了解架构)
   - 链接到docs/目录 (详细文档)
   - 添加Celery + Redis文档链接 (CELERY_REDIS_STREAMING.md)

### References

- [Source: backend/README.md - 现有后端文档]
- [Source: frontend/README.md - 现有前端文档]
- [Source: CLAUDE.md - 项目架构导航]
- [Source: docs/project-overview.md - 项目概述]
- [Source: docs/CELERY_REDIS_STREAMING.md - Celery和Redis流式架构]
- [Source: backend/config/settings/base.py - Django配置参考]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

无

### Completion Notes List

- ✅ 本Story专注于文档完善,不涉及代码修改
- ✅ 现有README已经相当完整,主要缺少服务启动顺序和环境变量配置
- ✅ 已添加关键的服务启动顺序说明(Redis → Celery → Django → Frontend)
- ✅ 已将pip命令替换为uv包管理器
- ✅ 已创建backend/.env.example和frontend/.env.example
- ✅ 已添加详细的常见问题排查部分,包含Redis、Celery、WebSocket问题
- ✅ 所有README文档已链接到详细文档(docs/目录)
- ✅ 环境变量文件已添加注释说明

### File List

**修改的文件:**
- backend/README.md
  - 更新依赖安装说明(pip → uv)
  - 添加服务启动顺序章节
  - 添加常见问题排查章节
  - 链接到.env.example和详细文档
- frontend/README.md
  - 添加环境变量配置章节
  - 添加与后端集成说明
  - 扩展常见问题排查章节
  - 链接到后端文档

**创建的文件:**
- backend/.env.example (包含所有必需环境变量及注释)
- frontend/.env.example (包含API和WebSocket配置)
