---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments:
  - /home/code/ai_story/docs/index.md
  - /home/code/ai_story/docs/architecture-backend.md
  - /home/code/ai_story/docs/architecture-frontend.md
  - /home/code/ai_story/docs/project-overview.md
  - /home/code/ai_story/docs/technology-stack.md
  - /home/code/ai_story/docs/source-tree-analysis.md
  - /home/code/ai_story/docs/existing-documentation-inventory.md
workflowType: 'prd'
documentCounts:
  briefCount: 0
  researchCount: 0
  brainstormingCount: 0
  projectDocsCount: 7
classification:
  projectType: '系统维护与部署'
  domain: 'DevOps/系统运维'
  complexity: '中等'
  projectContext: 'brownfield'
  focus: '系统稳定性与部署验证'
---

# Product Requirements Document - AI Story

**Author:** Root
**Date:** 2026-01-26
**Project Type:** 系统维护与部署 (Brownfield)
**Focus:** 系统稳定性验证与部署运行

---

## Executive Summary

AI Story通过AI自动化将创意转化为成品视频,将传统2小时的视频剪辑工作缩短至10分钟。

**PRD目标**: 系统稳定性验证(非新功能开发) - 确保Django+Vue技术栈、Celery异步任务、Redis消息队列、WebSocket实时通信等核心组件稳定运行。

**核心价值**: 10倍效率提升。

**技术栈**: Django 3.2.15 + Vue 2.7.14 + Celery + Redis (5数据库分离) + WebSocket

---

## Success Criteria

### User Success

用户能够使用 AI Story 完成核心视频生成工作流：
- ✅ 能够成功创建新项目
- ✅ 能够输入故事主题并完成 5 个阶段的处理（文案改写 → 分镜生成 → 文生图 → 运镜生成 → 图生视频）
- ✅ 能够实时看到处理进度（WebSocket/SSE 推送）
- ✅ 能够生成最终的视频文件
- ✅ 即使有一些小的 UI 问题或非关键功能异常，核心流程能走通

### Business Success

系统处于可用状态，支撑后续开发和改进：
- ✅ 系统可以稳定运行，不会频繁崩溃
- ✅ 主要功能可用率 > 90%（允许小 bug 存在）
- ✅ 开发环境配置清晰，可复现
- ✅ 为后续功能开发提供稳定基础

### Technical Success

所有服务组件正常工作：
- ✅ **后端服务**：Django ASGI 服务器启动成功，响应 API 请求
- ✅ **异步任务**：Celery Worker 运行正常，能处理队列任务
- ✅ **消息队列**：Redis 5 个数据库配置正确，各组件通信正常
- ✅ **实时通信**：WebSocket 连接建立成功，进度推送正常
- ✅ **数据库**：SQLite/PostgreSQL 连接正常，数据读写无误
- ✅ **前端应用**：Vue 应用成功构建，能够访问和使用

### Measurable Outcomes

1. **服务启动检查清单**：
   - [ ] Django ASGI 服务器启动（`./run_asgi.sh`）
   - [ ] Celery Worker 启动（`uv run celery -A config worker -Q llm,image,video -l info`）
   - [ ] Redis 服务运行（`docker run -d -p 6379:6379 redis:latest`）
   - [ ] 前端开发服务器启动（`npm run dev`）

2. **核心功能验证清单**：
   - [ ] 创建项目功能正常
   - [ ] 5 个阶段工作流能执行
   - [ ] WebSocket 实时进度显示
   - [ ] AI 模型调用正常（如果配置了 API Key）
   - [ ] 文件上传/下载正常

3. **已知问题记录**：
   - 记录所有发现的小 bug（不影响主要功能）
   - 区分：阻塞性问题（必须修复） vs 小问题（可延后）

## Product Scope

### MVP - Minimum Viable Product（本次目标）

**系统稳定运行验证**：
- 所有服务正常启动并保持运行
- 核心视频生成工作流可用
- 关键 API 端点正常响应
- 已知小 bug 记录在案

**不包括**：
- ❌ 修复所有非关键 bug
- ❌ 性能优化
- ❌ 新功能开发
- ❌ 用户体验改进

### Growth Features（后续改进）

- 修复已知的小 bug
- 性能优化（数据库查询、缓存）
- 错误处理增强
- 监控和日志改进

### Vision（未来方向）

- 系统生产环境部署
- 高可用性和容错
- 自动化测试覆盖
- CI/CD 流水线

---

## User Journeys

### Journey 0: 创作者 - 使用 AI Story 制作短视频

**角色**: 小雅(内容创作者)
**目标**: 快速制作猫咪搞笑短视频

**核心流程**:

1. **创建项目**: 输入名称"萌猫日常"
2. **输入主题**: "一只橘猫在客厅里追逐激光笔,最后跳上沙发睡觉",选择风格"可爱搞笑风"
3. **阶段1-文案改写**: AI生成生动文案,实时显示进度30%
4. **阶段2-分镜生成**: 自动生成5个分镜(躺地板→激光点→追逐→跑跳→睡觉)
5. **阶段3-文生图**: 为每个分镜生成图片,支持重新生成
6. **阶段4-运镜生成**: 为图片添加运镜描述(推、拉、摇、移)
7. **阶段5-图生视频**: 生成15秒视频,等待1-2分钟

**成功标准**:
- ✅ 10分钟内完成视频创作
- ✅ 视频质量满足发布要求
- ✅ 实时进度推送正常工作
- ⚠️ 允许小问题存在(如某个分镜需重新生成)

---

### Journey 1: 开发者 - 搭建并运行开发环境

**角色：Alex（开发者）**

**场景：**
Alex 是一名新加入项目的开发者，他需要在本地搭建 AI Story 的开发环境。

**故事：**

**开场场景：**
Alex 刚拿到项目代码，在终端输入 `cd ai_story`，然后开始探索如何让这个系统跑起来。

**发展过程：**
1. 查看 README.md，了解项目结构
2. 安装 Python 依赖：`cd backend && uv sync`
3. 运行数据库迁移：`uv run python manage.py migrate`
4. 启动 Redis：`docker run -d -p 6379:6379 redis:latest`
5. 启动后端：`./run_asgi.sh`
6. 安装前端依赖：`cd frontend && npm install`
7. 启动前端：`npm run dev`
8. 启动 Celery Worker：`uv run celery -A config worker -Q llm,image,video -l info`

**高潮时刻：**
Alex 打开浏览器访问 `http://localhost:3000`，看到项目列表页面成功显示！他创建了一个测试项目，看到 WebSocket 实时进度推送正常工作。

**结局：**
Alex 成功让整个系统在本地运行，可以开始开发工作。他记录了一些小问题（比如某个警告信息），但不影响主要功能。

---

### Journey 2: 运维人员 - 部署到服务器

**角色：Sam（运维工程师）**

**场景：**
Sam 需要将 AI Story 部署到生产服务器。

**故事：**

**开场场景：**
Sam 收到部署任务，需要确保系统在生产环境稳定运行。

**发展过程：**
1. 检查服务器环境（Python 3.11+、Node.js、Redis）
2. 配置环境变量（`.env` 文件）
3. 设置 PostgreSQL 数据库
4. 配置 Redis 5 个数据库分离
5. 配置 Celery 任务队列
6. 配置 Nginx 反向代理
7. 启动所有服务

**高潮时刻：**
Sam 验证所有服务正常运行：
- Django ASGI 服务器响应 API 请求
- Celery Worker 处理异步任务
- WebSocket 连接成功
- 前端应用可以访问

**结局：**
系统成功部署，Sam 准备好监控脚本，确保系统稳定运行。

---

### Journey 3: 测试人员 - 功能验证

**角色：Taylor（QA 工程师）**

**场景：**
Taylor 需要验证 AI Story 的核心功能是否正常工作。

**故事：**

**开场场景：**
Taylor 收到测试任务："验证系统能够正常运行"。

**发展过程：**
1. 启动所有必要的服务
2. 打开前端应用
3. 创建新项目："测试视频生成"
4. 输入故事主题："一只猫在花园里玩耍"
5. 观察 5 个阶段的处理进度
6. 检查 WebSocket 实时更新
7. 验证生成的视频文件

**高潮时刻：**
Taylor 看到项目从 0% 完成到 100%，每个阶段都正常执行。他生成了一段测试视频，确认核心功能工作正常。

**结局：**
Taylor 记录了测试结果：
- ✅ 核心功能正常
- ⚠️ 发现 2-3 个小 bug（不影响主要功能）
- 📋 整理了已知问题清单

---

## Journey Requirements Summary

这些用户旅程揭示了以下核心需求：

**创作者需求（小雅）：**
- 直观易用的用户界面
- 实时进度反馈（WebSocket/SSE）
- 可调整的创作流程（每个阶段可微调）
- 快速视频生成（10 分钟内完成）
- 视频下载功能

**开发者需求（Alex）：**
- 清晰的环境配置文档
- 服务启动顺序说明
- 常见问题排查指南
- 依赖安装脚本/命令

**运维人员需求（Sam）：**
- 部署配置指南
- 环境变量说明
- 服务健康检查方法
- 监控和日志配置

**测试人员需求（Taylor）：**
- 功能验证清单
- 已知问题记录模板
- 问题优先级分类标准

---

## Web Application Specific Requirements

### Project-Type Overview

AI Story 是一个全栈 Web 应用，采用前后端分离架构：
- **后端：** Django 3.2.15 + DRF + Celery + Channels
- **前端：** Vue 2.7.14 + Vuex + daisyUI + Tailwind CSS
- **核心特性：** 实时 WebSocket 通信、异步任务处理、AI 模型集成

#### 1. 服务组件架构

**必需组件**:
- **Django ASGI服务器**: 支持WebSocket,监听8000端口
- **Celery Worker**: 3个队列(llm, image, video),处理异步任务
- **Redis服务**: 5数据库分离架构(DB0/DB1/DB2/DB3/DB4)
- **Vue前端应用**: SPA,监听3000端口

#### 2. 实时通信架构

**WebSocket进度推送**: 路径`ws://localhost:8000/ws/projects/{project_id}/`,消息格式JSON
**Redis Pub/Sub**: Celery任务进度发布到Redis Pub/Sub,Django Consumer监听并推送到WebSocket

#### 3. 5阶段异步工作流

1. **文案改写(LLM队列)**: 调用LLM API,处理时间5-15秒
2. **分镜生成(LLM队列)**: 调用LLM API生成分镜描述,处理时间10-30秒
3. **文生图(Image队列)**: 调用AI模型生成图片,处理时间30-60秒/图
4. **运镜生成(LLM队列)**: 为图片添加运镜描述,处理时间5-10秒
5. **图生视频(Video队列)**: 调用AI模型生成视频,处理时间1-2分钟/视频

**任务状态跟踪**: 数据库模型`StageContent`,状态枚举pending→processing→completed→failed,进度0-100%

#### 4. 数据库与状态管理

**数据库模型（核心）：**
- `Project`：项目信息
- `StageContent`：5 个阶段的内容和状态
- `GeneratedAsset`：生成的图片、视频文件记录
- `PromptSet`：提示词模板（可选）

**文件存储：**
- 本地文件系统：`backend/media/uploads/`
- 生成文件路径：`uploads/projects/{project_id}/{stage}/{filename}`

### Implementation Considerations

#### 1. 环境配置要求

**环境变量（.env）：**
```bash
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# 或 PostgreSQL: postgres://user:password@localhost:5432/ai_story

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI API Keys（可选）
OPENAI_API_KEY=
STABLE_DIFFUSION_API_KEY=
RUNWAY_API_KEY=
```

**依赖安装：**
- 后端：`cd backend && uv sync`
- 前端：`cd frontend && npm install`

#### 2. 服务启动顺序

**正确启动顺序：**
1. Redis：`docker run -d -p 6379:6379 redis:latest`
2. 数据库迁移：`cd backend && uv run python manage.py migrate`
3. Celery Worker：`cd backend && uv run celery -A config worker -Q llm,image,video -l info`
4. Django ASGI：`cd backend && ./run_asgi.sh`
5. Vue 前端：`cd frontend && npm run dev`

**停止顺序：**
1. 前端（Ctrl+C）
2. Celery Worker（Ctrl+C）
3. Django ASGI（Ctrl+C）
4. Redis：`docker stop <container_id>`

#### 3. 健康检查端点

**关键健康检查：**
- `/api/v1/health/` - 系统健康状态
- `/api/v1/projects/` - API 可用性
- WebSocket 连接测试：`ws://localhost:8000/ws/projects/1/`

#### 4. 常见问题排查

**问题 1：WebSocket 连接失败**
- 检查 ASGI 服务器是否运行
- 检查 Redis DB3 是否可用
- 检查前端 WebSocket URL 配置

**问题 2：Celery 任务不执行**
- 检查 Celery Worker 是否启动
- 检查 Redis DB0（broker）是否连接
- 查看 Celery 日志：`-l info`

**问题 3：前端构建失败**
- 清除 `node_modules/`：`rm -rf node_modules && npm install`
- 检查 Node.js 版本兼容性

#### 5. 浏览器兼容性

**目标浏览器：**
- Chrome/Edge（最新版）：完全支持
- Firefox（最新版）：完全支持
- Safari（最新版）：基本支持（需测试 WebSocket）

**不支持的浏览器：**
- Internet Explorer（任何版本）

#### 6. 性能目标

**响应时间要求：**
- API 请求：< 500ms（P95）
- WebSocket 连接：< 1 秒建立
- 页面加载：< 3 秒（首屏）

**异步任务处理时间：**
- 文案改写：< 30 秒
- 分镜生成：< 60 秒
- 文生图：< 120 秒
- 图生视频：< 300 秒

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP定位**: 系统验证(非产品开发) - 确保现有系统稳定运行,核心功能可用

**资源需求**: 1名开发者即可完成验证工作

### MVP Feature Set (Phase 1) - 本次目标

**Core User Journeys Supported:**
- ✅ 创作者（小雅）：能够完成端到端的视频生成流程
- ✅ 开发者（Alex）：能够在本地搭建和运行开发环境
- ✅ 运维人员（Sam）：能够了解部署配置和系统架构
- ✅ 测试人员（Taylor）：能够验证核心功能并记录问题

**Must-Have Capabilities:**

**服务层：**
1. Django ASGI 服务器启动和运行
2. Celery Worker 处理异步任务
3. Redis 5 数据库配置正确
4. 数据库（SQLite/PostgreSQL）连接正常
5. Vue 前端应用构建和访问

**功能层：**
1. 项目 CRUD 操作（创建、查看、删除项目）
2. 5 阶段工作流执行（文案 → 分镜 → 文生图 → 运镜 → 图生视频）
3. WebSocket/SSE 实时进度推送
4. 生成的图片和视频文件存储和下载
5. 基本错误处理和日志记录

**不包括（本次 MVP）：**
- ❌ 修复非关键 bug
- ❌ 性能优化
- ❌ 新功能开发
- ❌ 用户体验改进

### Post-MVP Features

**Phase 2 (Post-MVP) - 稳定性改进：**

基于 MVP 验证中发现的阻塞性问题：
- 修复影响核心功能的 bug
- 改进错误处理和用户反馈
- 完善开发文档和部署指南
- 添加健康检查和监控端点

**Phase 3 (Expansion) - 生产就绪：**

- 生产环境部署配置
- 性能优化（数据库查询、缓存策略）
- 高可用性和容错机制
- 自动化测试覆盖
- CI/CD 流水线
- 监控和告警系统

### Risk Mitigation Strategy

**技术风险：**
- **风险：** AI API 调用失败或超时
- **缓解：** 配置重试机制（3 次），记录错误日志，提供重试按钮

**资源风险：**
- **风险：** 依赖服务（Redis、AI API）不可用
- **缓解：** 提供依赖检查脚本，添加健康检查端点，记录服务状态

**范围风险：**
- **风险：** 范围蔓延，开始修复非关键 bug
- **缓解：** 严格区分"阻塞性问题"（必须修复） vs "小问题"（可延后），聚焦核心验证目标

**验证风险：**
- **风险：** 发现大量现有 bug，影响验证信心
- **缓解：** 提前告知"这是 brownfield 项目，可能会有一些历史遗留问题"，聚焦验证核心流程而非完美体验

---

## Functional Requirements

> **This section defines WHAT the system must do - the capability contract for all downstream work.**
> These requirements are implementation-agnostic and testable.

### Capability Area 1: 项目管理 (Project Management)

**FR1.1** 创作者可以创建新项目,输入项目名称、故事主题和视频风格

**FR1.2** 创作者可以查看项目列表,看到所有已创建的项目及其当前状态

**FR1.3** 创作者可以查看单个项目的详细信息,包括项目设置、生成的内容和当前进度

**FR1.4** 创作者可以删除不需要的项目

**FR1.5** 系统为每个项目分配唯一标识符,用于关联所有生成的内容

### Capability Area 2: 内容生成工作流 (Content Generation Workflow)

**FR2.1** 系统支持 5 阶段工作流:文案改写 → 分镜生成 → 文生图 → 运镜生成 → 图生视频

**FR2.2** 创作者可以启动项目的完整工作流,自动按顺序执行所有 5 个阶段

**FR2.3** 系统在每个阶段完成后自动触发下一阶段

**FR2.4** 创作者可以在任意阶段暂停工作流执行

**FR2.5** 创作者可以从任意失败阶段重新开始工作流

**FR2.6** 系统支持单个阶段的独立执行和重试

**FR2.7** 系统记录每个阶段的输入、输出和执行状态

### Capability Area 3: AI 模型集成 (AI Model Integration)

**FR3.1** 系统可以调用 LLM API(OpenAI/Claude)执行文案改写任务

**FR3.2** 系统可以调用 LLM API 生成分镜描述

**FR3.3** 系统可以调用文生图 AI 模型(Stable Diffusion)生成图片

**FR3.4** 系统可以调用图生视频 AI 模型(Runway)生成视频

**FR3.5** 系统支持多个 AI 模型提供商的配置和切换

**FR3.6** 系统对失败的 AI API 调用执行自动重试(最多 3 次)

**FR3.7** 开发者可以配置 AI API 密钥和模型参数

### Capability Area 4: 实时进度跟踪 (Real-time Progress Tracking)

**FR4.1** 创作者可以通过 WebSocket 连接实时查看项目处理进度

**FR4.2** 系统在每个阶段处理时推送进度更新(0-100%)

**FR4.3** 系统推送当前执行阶段的名称和状态

**FR4.4** 系统在阶段完成时推送完成通知和结果摘要

**FR4.5** 系统在任务失败时推送错误信息和建议

**FR4.6** 创作者可以查看历史进度记录,了解每个阶段的执行时间和结果

**FR4.7** 系统支持 SSE(Server-Sent Events)作为 WebSocket 的备用方案

### Capability Area 5: 文件管理 (File Management)

**FR5.1** 系统存储生成的图片文件,按项目、阶段组织目录结构

**FR5.2** 系统存储生成的视频文件,关联到对应项目

**FR5.3** 创作者可以预览生成的图片和视频

**FR5.4** 创作者可以下载生成的图片和视频到本地

**FR5.5** 系统支持图片文件的重新生成,替换不满意的结果

**FR5.6** 系统自动清理临时文件和过期的缓存内容

**FR5.7** 系统记录文件的元数据(生成时间、文件大小、AI 模型版本)

### Capability Area 6: 系统配置与部署 (System Configuration & Deployment)

**FR6.1** 开发者可以通过环境变量(.env)配置所有系统参数

**FR6.2** 系统支持 SQLite(开发)和 PostgreSQL(生产)数据库

**FR6.3** 系统通过数据库迁移脚本自动创建和更新数据库结构

**FR6.4** 开发者可以按正确的启动顺序启动所有服务组件(Redis → Celery → Django → 前端)

**FR6.5** 系统提供健康检查端点,验证所有服务组件的状态

**FR6.6** 运维人员可以配置Redis 5数据库分离架构

**FR6.7** 运维人员可以配置 Celery 的任务队列和 Worker 数量

**FR6.8** 系统提供部署配置文档和脚本

### Capability Area 7: 错误处理与日志 (Error Handling & Logging)

**FR7.1** 系统捕获并记录所有 API 调用错误(AI API、数据库、Redis)

**FR7.2** 系统捕获并记录异步任务执行失败(Celery 任务)

**FR7.3** 系统向用户显示友好的错误消息,隐藏技术细节

**FR7.4** 系统记录详细的错误日志,包括时间戳、错误类型、堆栈跟踪

**FR7.5** 系统在任务失败后支持手动重试

**FR7.6** 系统提供日志级别控制(DEBUG/INFO/WARNING/ERROR)

**FR7.7** 开发者可以通过日志文件排查问题

### Capability Area 8: API 接口 (API Interfaces)

**FR8.1** 系统提供 RESTful API 端点用于项目 CRUD 操作

**FR8.2** 系统提供 API 端点用于启动、暂停、重试工作流

**FR8.3** 系统提供 API 端点用于查询项目状态和进度

**FR8.4** 系统提供 API 端点用于获取生成的文件列表和下载链接

**FR8.5** 系统实现 API 认证和授权机制(如果需要)

**FR8.6** API 返回标准的 HTTP 状态码和错误消息

**FR8.7** API 支持分页、过滤和排序功能(项目列表)

### Capability Area 9: 前端用户界面 (Frontend User Interface)

**FR9.1** 前端应用显示项目列表页面,展示所有项目

**FR9.2** 前端应用提供创建项目的表单界面

**FR9.3** 前端应用显示项目详情页面,展示项目设置和生成内容

**FR9.4** 前端应用实时显示工作流进度(进度条、百分比、当前阶段)

**FR9.5** 前端应用提供控制按钮(开始、暂停、重试、删除)

**FR9.6** 前端应用显示生成的图片和视频预览

**FR9.7** 前端应用响应式设计,支持桌面浏览器

**FR9.8** 前端应用在 WebSocket 连接失败时显示重连提示

### Capability Area 10: 开发者工具与文档 (Developer Tools & Documentation)

**FR10.1** 系统提供 README 文档,说明项目结构和快速开始

**FR10.2** 系统提供环境配置文档,列出所有必需的环境变量

**FR10.3** 系统提供服务启动指南,说明正确的启动顺序

**FR10.4** 系统提供常见问题排查指南,列出常见问题和解决方案

**FR10.5** 系统提供 API 文档,描述所有 API 端点和参数

**FR10.6** 系统提供架构文档,说明技术栈和组件关系

**FR10.7** 系统提供数据库迁移文档,说明如何执行数据库变更

---

### Functional Requirements Summary

**Total Requirements:** 60 Functional Requirements across 10 capability areas

**Requirements by Priority:**

**Must-Have (MVP - 系统验证):**
- All FR1.x (项目管理) - 5 requirements
- All FR2.x (内容生成工作流) - 7 requirements
- All FR3.x (AI 模型集成) - 7 requirements
- All FR4.x (实时进度跟踪) - 7 requirements
- All FR5.x (文件管理) - 7 requirements
- FR6.1, FR6.2, FR6.3, FR6.4, FR6.5 (系统配置核心) - 5 requirements
- All FR7.x (错误处理与日志) - 7 requirements
- All FR8.x (API 接口) - 7 requirements
- All FR9.x (前端用户界面) - 8 requirements
- FR10.1, FR10.2, FR10.3, FR10.4 (核心文档) - 4 requirements

**Total Must-Have:** 64 requirements (涵盖所有 10 个能力领域)

**Post-MVP (Phase 2 & 3):**
- FR6.6, FR6.7, FR6.8 (高级配置和部署)
- FR10.5, FR10.6, FR10.7 (完善文档)

**Total Post-MVP:** 6 requirements

---

### Requirements Traceability Matrix

| User Journey | Key Requirements Supported |
|--------------|----------------------------|
| **创作者(小雅)** | FR1.1, FR1.2, FR1.3, FR2.2, FR4.1, FR4.2, FR4.4, FR5.3, FR5.4, FR9.1-9.8 |
| **开发者** | FR6.1, FR6.2, FR6.3, FR6.4, FR7.6, FR7.7, FR10.1-10.4 |
| **运维人员** | FR6.5, FR6.6, FR6.7, FR6.8, FR7.4 |
| **测试人员** | FR2.2, FR4.1, FR4.2, FR7.1, FR7.3, FR8.6 |

---

## Non-Functional Requirements

> **This section defines HOW WELL the system must perform - quality attributes that matter for system verification.**
> After advanced elicitation analysis, we now have 48 NFRs across 8 categories (up from 30 NFRs in 5 categories).

### NFR Priority Framework

**P0 - MVP Verification Essential (8 requirements):**
- Must be testable and achievable
- Directly impacts system validation capability
- Foundation for all other quality attributes

**P1 - Stability Essential (15 requirements):**
- Required for reliable system operation
- Enables monitoring and troubleshooting
- Supports continuous improvement

**P2 - Optimization Enhancement (25 requirements):**
- Nice-to-have for production readiness
- Performance optimization targets
- Advanced operational capabilities

---

### 1. Performance (性能)

**P0 - MVP Requirements:**

- **NFR-P1:** API请求必须在500ms内响应(P95) - 排除AI API延迟
- **NFR-P2:** WebSocket连接必须在1秒内建立成功

**P1 - Stability Requirements:**

- **NFR-P3:** 前端首屏加载时间必须 < 3秒(基于标准网络)
- **NFR-P4:** 实时进度推送延迟必须 < 500ms(WebSocket到前端)
- **NFR-P5:** API调用超时必须在30秒后触发指数退避重试(1s→2s→4s),最多3次

**P2 - Optimization Targets:**

- **NFR-P6:** 文案改写本地处理时间(不含AI API)必须 < 5秒
- **NFR-P7:** 分镜生成本地处理时间(不含AI API)必须 < 10秒
- **NFR-P8:** 文生图本地处理时间(不含AI API)必须 < 15秒
- **NFR-P9:** 图生视频本地处理时间(不含AI API)必须 < 20秒
- **NFR-P10:** 系统必须支持至少5个并发项目处理(开发环境)

**Measurement Methods:**
- 使用Django middleware记录API响应时间
- 使用Celery hooks记录任务执行时间
- 使用浏览器DevTools测量前端加载时间

---

### 2. Reliability (可靠性)

**P0 - MVP Requirements:**

- **NFR-R1:** 健康检查端点必须在200ms内响应,包含所有Critical服务状态
- **NFR-R2:** 单个服务组件故障不得导致整个系统崩溃(隔离性)

**P1 - Stability Requirements:**

- **NFR-R3:** 系统崩溃后必须能在2分钟内恢复(重启服务脚本)
- **NFR-R4:** 失败的AI API调用必须自动重试(最多3次,指数退避)
- **NFR-R5:** Celery任务失败后必须支持手动重试(通过API端点)
- **NFR-R6:** WebSocket连接断开后前端必须自动重连(最多5次,间隔递增)
- **NFR-R7:** 数据库事务失败必须回滚,保持数据一致性

**P2 - Optimization Targets:**

- **NFR-R8:** 核心服务月度可用率必须 > 99%(生产环境目标)
- **NFR-R9:** 生成的图片和视频文件必须正确存储,不得丢失
- **NFR-R10:** Redis故障时系统必须降级到数据库轮询模式(降级机制)
- **NFR-R11:** Celery故障时API必须返回"任务已提交"消息,避免用户等待

**Service Degradation Strategy:**
- Critical失败(数据库): 返回503 Service Unavailable
- Warning失败(Redis、Celery): 返回200但有降级警告
- Info失败(AI API): 记录日志,不影响核心功能

---

### 3. Testability (可测试性) ⭐ NEW CATEGORY

**P0 - MVP Requirements:**

- **NFR-T1:** 核心路径单元测试覆盖率必须 > 70%
  - 测量方法: 使用pytest-cov生成覆盖率报告
  - 覆盖模块: apps/projects、apps/content、core/pipeline
  - 验证标准: PR合并前必须达到70%,关键业务逻辑100%覆盖
  - 当前状态: < 2% (仅1个测试文件)

- **NFR-T2:** API集成测试必须覆盖100%的API端点
  - 测量方法: 使用DRF APITestCase
  - 验证标准: 每个API至少1个成功场景+1个失败场景
  - 覆盖范围: ProjectViewSet所有18个action
  - 当前状态: 0%

**P1 - Stability Requirements:**

- **NFR-T3:** Mock AI客户端必须支持离线测试
  - 验证标准: 所有AI客户端调用可切换为Mock模式
  - Mock客户端返回确定性数据
  - CI/CD可在无API密钥情况下运行
  - 当前状态: ✅ 已实现MockLLMClient等

**P2 - Optimization Targets:**

- **NFR-T4:** E2E测试必须覆盖核心用户旅程
  - 测量方法: 使用Playwright或Cypress
  - 验证标准: 从创建项目到生成视频的完整流程
  - 当前状态: ❌ 未实现

- **NFR-T5:** 测试执行时间必须 < 5分钟(快速反馈)
  - 测量方法: 使用pytest --durations=10
  - 验证标准: 单元测试 < 2分钟,集成测试 < 3分钟

---

### 4. Observability (可观测性) ⭐ ENHANCED

**P0 - MVP Requirements:**

- **NFR-O1:** 所有关键操作必须记录结构化日志
  - 日志格式: JSON
  - 包含字段: timestamp, level, request_id, user_id, action, duration_ms
  - 验证标准:
    - 项目创建/更新/删除100%记录
    - Celery任务开始/结束/失败100%记录
  - 当前状态: ⚠️ 仅有基础console logging

**P1 - Stability Requirements:**

- **NFR-O2:** API响应时间必须可监控(P95可观测化)
  - 测量方法: 使用Django middleware记录响应时间
  - 验证标准: 每日生成响应时间分布报告
  - P95超标的API自动告警
  - 当前状态: ❌ 无监控

- **NFR-O3:** Celery任务执行时间必须监控
  - 测量方法: 使用Celery hooks记录任务开始/结束时间
  - 验证标准: 任务执行超过阈值时发送告警
  - 任务失败率统计
  - 当前状态: ⚠️ 部分实现在tasks.py中

**P2 - Optimization Targets:**

- **NFR-O4:** 系统必须支持分布式追踪(生产环境)
  - 测量方法: 集成OpenTelemetry或Jaeger
  - 验证标准: 跨服务请求(trace from API to Celery to AI API)

- **NFR-O5:** 业务指标必须可视化
  - 测量方法: Prometheus + Grafana
  - 验证标准: 实时显示项目创建成功率、任务完成率

---

### 5. Data Consistency (数据一致性) ⭐ NEW CATEGORY

**P0 - MVP Requirements:**

- **NFR-D1:** 数据库事务完整性必须保证
  - 配置要求: DATABASES['default']['ATOMIC_REQUESTS'] = True
  - Celery任务使用transaction.on_commit()
  - 验证标准:
    - 项目创建失败时回滚所有关联数据
    - 任务失败时不保存部分结果
  - 当前状态: ❌ ATOMIC_REQUESTS未启用

**P1 - Stability Requirements:**

- **NFR-D2:** 外键约束完整性必须保证
  - 验证标准:
    - Project删除时级联删除所有ProjectStage
    - User删除时级联删除所有Project
    - 无孤儿数据
  - 当前状态: ✅ models.py中已配置on_delete=CASCADE

**P2 - Optimization Targets:**

- **NFR-D3:** 数据库迁移必须可回滚
  - 验证标准: 所有migration文件可安全回滚
  - 使用./manage.py migrate backward测试
  - 当前状态: ✅ Django migrations默认支持

---

### 6. Resource Management (资源管理) ⭐ NEW CATEGORY

**P1 - Stability Requirements:**

- **NFR-RM1:** 磁盘空间必须监控
  - 配置要求: 每次上传前检查可用空间 > 1GB
  - 健康检查包含磁盘空间
  - 验证标准: 空间不足时拒绝上传并返回友好错误
  - 当前状态: ❌ 未实现

**P2 - Optimization Targets:**

- **NFR-RM2:** 生成文件必须自动清理
  - 配置要求: Celery Beat定时任务清理7天前的临时文件
  - 项目删除时删除关联文件
  - 验证标准: 不会因文件堆积导致磁盘满
  - 当前状态: ❌ 未实现

- **NFR-RM3:** 内存使用必须限制
  - 配置要求: Celery Worker max_tasks_per_child=100
  - 验证标准: 单个Worker内存使用 < 2GB

---

### 7. Integration (集成)

**P0 - MVP Requirements:**

- **NFR-I1:** AI客户端接口抽象必须支持2个LLM提供商
  - 验证标准: core/ai_client/base.py定义统一接口
  - 至少实现1个Mock客户端用于测试
  - OpenAI和Claude客户端可选配置
  - 当前状态: ✅ 已实现接口抽象

- **NFR-I2:** Celery Worker必须成功连接到Redis(DB0/DB1)
  - 验证标准: Worker启动时输出"connected to redis"
  - 健康检查验证连接状态

- **NFR-I3:** Django Channels必须成功连接到Redis(DB3)
  - 验证标准: WebSocket连接建立成功
  - 健康检查验证Channels层状态

**P1 - Stability Requirements:**

- **NFR-I4:** AI API调用超时必须在30秒后触发指数退避重试
  - 重试策略: 1s → 2s → 4s,最多3次
  - 验证标准: 超时日志记录详细错误信息
  - 当前状态: ⚠️ 超时设置为60秒,过长

- **NFR-I5:** Redis Pub/Sub消息必须在100ms内传递给WebSocket
  - 验证标准: 使用Redis Benchmark测试
  - 消息延迟监控和告警

**P2 - Optimization Targets:**

- **NFR-I6:** 系统必须集成文生图API(Stable Diffusion或同等服务)
  - 验证标准: 可配置多个图生图提供商
  - 支持降级到Mock模式

- **NFR-I7:** 系统必须集成图生视频API(Runway或同等服务)
  - 验证标准: 可配置多个图生视频提供商
  - 支持降级到Mock模式

- **NFR-I8:** 系统必须支持RESTful API v1版本
  - 验证标准: 所有API端点以/api/v1/开头
  - API版本不破坏向后兼容性

- **NFR-I9:** WebSocket消息格式必须遵循JSON schema
  - 验证标准: 使用JSON Schema验证消息格式
  - 消息类型字段必须有: type, data, timestamp

---

### 8. Security (安全性)

**P0 - MVP Requirements:**

- **NFR-S1:** AI API密钥必须通过环境变量配置,不得硬编码
  - 验证标准: 代码仓库中无API密钥
  - .env文件在.gitignore中
  - 当前状态: ✅ 已实现

- **NFR-S2:** 配置信息不得提交到代码仓库
  - 验证标准: .env、.env.local在.gitignore中
  - 敏感配置使用环境变量
  - 当前状态: ✅ 已实现

**P1 - Stability Requirements:**

- **NFR-S3:** API密钥不得记录在日志文件中
  - 验证标准: 日志中过滤Authorization、api_key等字段
  - 使用Django的settings.SENSITIVE_HEADERS

- **NFR-S4:** 用户内容必须隐私保护
  - 验证标准: 用户的提示词和生成内容私有,不跨项目泄露
  - 项目级别的权限控制
  - 当前状态: ✅ 已实现基本权限

**P2 - Optimization Targets:**

- **NFR-S5:** 数据库连接必须使用SSL/TLS(生产环境)
  - 验证标准: DATABASE_URL包含sslmode=require
  - 开发环境可豁免

- **NFR-S6:** 生产环境API密钥必须使用密钥管理服务
  - 验证标准: 集成AWS Secrets Manager或HashiCorp Vault
  - 定期轮换密钥

- **NFR-S7:** Django Admin界面必须需要身份验证
  - 验证标准: 访问/admin时要求登录
  - 生产环境启用双因素认证

- **NFR-S8:** API端点必须实现基本认证机制(如果需要)
  - 验证标准: 使用DRF TokenAuthentication或SessionAuthentication
  - 敏感操作需要验证

---

### 9. User Experience (用户体验) ⭐ NEW CATEGORY

**P1 - Stability Requirements:**

- **NFR-UX1:** 前端必须显示友好的错误提示
  - 验证标准: 所有API错误在前端显示用户友好消息
  - 不暴露技术堆栈信息
  - 提供解决建议
  - 当前状态: ⚠️ 部分实现

**P2 - Optimization Targets:**

- **NFR-UX2:** 离线降级支持
  - 验证标准: WebSocket断开时自动切换到轮询模式
  - AI API失败时使用Mock数据演示流程
  - 当前状态: ⚠️ 轮询API已实现但未集成到前端

- **NFR-UX3:** 前端响应式设计
  - 验证标准: 支持桌面浏览器(Chrome、Firefox、Edge)
  - 移动端基本可用

---

### 10. Maintainability (可维护性)

**P0 - MVP Requirements:**

- **NFR-M1:** 系统必须提供健康检查端点
  - 端点路径: /api/v1/health/
  - 验证标准: 响应时间 < 200ms
  - 返回所有关键服务状态(数据库、Redis、Celery)
  - 当前状态: ❌ 未实现

- **NFR-M2:** 系统必须提供完整的环境配置文档
  - 文档路径: docs/ENVIRONMENT_SETUP.md
  - 验证标准: 新开发者可以按照文档在30分钟内完成环境搭建
  - 当前状态: ⚠️ 部分在README中

- **NFR-M3:** 系统必须提供服务启动和停止指南
  - 文档路径: docs/SERVICE_MANAGEMENT.md
  - 验证标准: 包含正确的启动顺序和故障恢复步骤
  - 当前状态: ⚠️ 部分在README中

**P1 - Stability Requirements:**

- **NFR-M4:** 所有服务组件必须记录结构化日志
  - 日志格式: JSON
  - 日志级别必须可配置(DEBUG/INFO/WARNING/ERROR)
  - 验证标准: 错误日志包含时间戳、错误类型、堆栈跟踪
  - 当前状态: ⚠️ 仅有基础配置

- **NFR-M5:** 日志文件必须结构化存储
  - 验证标准: 按日期轮转日志文件
  - 日志保留30天
  - 错误日志单独存储

**P2 - Optimization Targets:**

- **NFR-M6:** 系统必须提供常见问题排查指南
  - 文档路径: docs/TROUBLESHOOTING.md
  - 验证标准: 覆盖Top 10常见问题
  - 每个问题包含症状、原因、解决方案

- **NFR-M7:** 系统必须提供部署配置文档
  - 文档路径: docs/DEPLOYMENT.md
  - 验证标准: 包含Docker Compose配置
  - 包含生产环境checklist

- **NFR-M8:** 系统必须提供测试指南
  - 文档路径: docs/TESTING.md
  - 验证标准: 包含测试策略、Mock使用、CI配置

---

## Non-Functional Requirements Summary

**Total NFRs:** 48 Non-Functional Requirements across 10 categories

**By Priority:**

| Priority | Count | Focus |
|----------|-------|-------|
| **P0 - MVP Essential** | 8 | Testability, Data Consistency, Health Check, Logging |
| **P1 - Stability Essential** | 15 | Observability, Resource Mgmt, Integration, User Experience |
| **P2 - Optimization Enhancement** | 25 | Performance Targets, Security, Scalability, Advanced Features |

**By Category:**

| Category | P0 | P1 | P2 | Total |
|----------|----|----|----|----|
| Performance | 2 | 3 | 5 | 10 |
| Reliability | 2 | 5 | 4 | 11 |
| **Testability** ⭐ | **2** | **1** | **2** | **5** |
| **Observability** ⭐ | **1** | **2** | **2** | **5** |
| **Data Consistency** ⭐ | **1** | **1** | **1** | **3** |
| **Resource Management** ⭐ | **0** | **1** | **2** | **3** |
| Integration | 3 | 2 | 4 | 9 |
| Security | 2 | 2 | 4 | 8 |
| **User Experience** ⭐ | **0** | **1** | **2** | **3** |
| Maintainability | 3 | 2 | 3 | 8 |

**Key Changes from Advanced Elicitation:**
- ✅ Added **Testability** category (P0 priority, critical gap identified)
- ✅ Added **Data Consistency** category (transaction integrity)
- ✅ Added **Resource Management** category (disk space, file cleanup)
- ✅ Added **User Experience** category (error handling, offline mode)
- ✅ Enhanced **Observability** (structured logging, metrics)
- ✅ Refined **Performance** NFRs (focus on local processing, not AI API)
- ✅ Reprioritized based on achievability and verification needs

---

## NFR Validation Strategy

**Automated Testing:**
- Unit tests for transaction integrity (NFR-D1)
- Integration tests for API endpoints (NFR-T2)
- Health check endpoint tests (NFR-M1)
- Log format validation (NFR-O1)

**Manual Verification:**
- Service startup and shutdown procedures (NFR-M3)
- Configuration documentation walkthrough (NFR-M2)
- Error message usability (NFR-UX1)

**Monitoring:**
- Response time metrics (NFR-P1, NFR-O2)
- Task execution monitoring (NFR-O3)
- Disk space alerts (NFR-RM1)
- Service availability dashboards (NFR-R8)

---

### Testable Success Criteria

Each functional requirement is testable through:

1. **Automated Testing:** API endpoint tests, unit tests for core logic
2. **Manual Testing:** User interface testing, end-to-end workflow validation
3. **Integration Testing:** Service component interaction validation
4. **Health Check:** System component availability verification

---
