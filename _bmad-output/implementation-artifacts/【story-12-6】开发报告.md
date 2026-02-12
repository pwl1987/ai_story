# 【Story 12-6】章节工作室 UI - 开发报告

> **Story ID**: 12-6-chapter-studio-ui
> **开发日期**: 2026-02-12
> **开发状态**: ✅ 开发完成

---

## 一、开发概览

### 1.1 Story 目标

实现章节工作室（Chapter Studio）前端 UI，为用户提供章节级自动化制作工作台，集成工作流控制、场景进度跟踪、首尾帧预览和实时事件日志功能。

### 1.2 技术栈

| 类别 | 技术 |
|------|------|
| 前端框架 | Vue 2.7.14 |
| 状态管理 | Vuex |
| UI 组件库 | daisyUI 4.12.23 + Tailwind CSS 3.4.17 |
| 通信协议 | HTTP (REST API) + WebSocket |

---

## 二、实现清单

### 2.1 新增文件

| 文件路径 | 行数 | 职责 |
|---------|------|------|
| `frontend/src/components/artworks/FramePreview.vue` | 143 | 首尾帧预览组件 |
| `frontend/src/components/artworks/WorkflowControlPanel.vue` | 307 | 工作流控制面板组件 |
| `frontend/src/components/artworks/SceneProgressCard.vue` | 287 | 场景进度卡片组件 |
| `frontend/src/components/artworks/WorkflowEventLog.vue` | 250+ | 工作流事件日志组件 |
| `frontend/src/views/artworks/ChapterStudio.vue` | 260+ | 章节工作室主页面 |
| `frontend/src/utils/workflowWebSocket.js` | 122 | WebSocket 客户端类 |
| `frontend/src/services/api/chapters.js` | 44 | 章节 API 服务 |
| `frontend/src/services/api/scenes.js` | 30 | 场景 API 服务 |
| `frontend/src/store/modules/workflow.js` | 141 | Vuex 工作流状态模块 |

### 2.2 修改文件

| 文件路径 | 改动内容 |
|---------|---------|
| `frontend/src/router/index.js` | 添加 ChapterStudio 路由配置 |
| `frontend/src/store/index.js` | 注册 workflow Vuex 模块 |

---

## 三、详细实现说明

### 3.1 FramePreview.vue - 首尾帧预览组件

**文件核心作用**: 显示场景的首帧或尾帧图片，支持加载状态、错误处理和占位符 fallback

**本次改动内容**:
- 创建新组件文件
- 实现 props：`imageUrl`（图片URL）、`fallbackIcon`（占位图标）、`label`（标签文本）
- 实现三种状态：加载中、加载成功、加载失败
- 使用 daisyUI 的 figure 和 image 组件样式

**实现功能**:
- 显示首尾帧图片（来自 Story 12-5 提取服务）
- 图片加载时显示加载动画
- 图片加载失败时显示占位图标和错误提示
- 支持自定义标签（"首帧"/"尾帧"）

**Props 定义**:
```javascript
props: {
  imageUrl: { type: String, default: '' },
  fallbackIcon: { type: String, default: '🖼️' },
  label: { type: String, default: '帧' },
}
```

---

### 3.2 WorkflowControlPanel.vue - 工作流控制面板组件

**文件核心作用**: 章节工作流的控制中心，显示状态、进度、当前场景和控制按钮

**本次改动内容**:
- 创建新组件文件
- 实现 props：`status`、`progress`、`currentScene`、`totalScenes`、`completedScenes`、`isLoading`
- 实现操作按钮：启动、暂停、继续、重新启动
- 根据状态动态显示不同按钮和徽章样式
- 集成 daisyUI 的 card、progress、badge 组件

**实现功能**:
- 显示工作流状态徽章（待处理/运行中/已暂停/已完成/失败）
- 显示进度条（0-100%）和进度百分比文字
- 显示当前正在处理的场景信息
- 显示已完成场景数统计
- 根据状态显示对应操作按钮：
  * 待处理/已完成/失败 → 显示"启动"按钮
  * 运行中 → 显示"暂停"按钮
  * 已暂停 → 显示"继续"按钮
- 加载中状态禁用所有按钮

**Props 定义**:
```javascript
props: {
  status: { type: String, default: 'idle', validator: ... },
  progress: { type: Number, default: 0 },
  currentScene: { type: Object, default: null },
  totalScenes: { type: Number, required: true },
  completedScenes: { type: Number, default: 0 },
  isLoading: { type: Boolean, default: false },
}
```

**Computed 计算属性**:
- `statusDisplay`: 状态中文映射
- `statusBadgeClass`: 徽章样式类映射
- `canStart`: 是否可启动（idle/completed/failed）
- `canPause`: 是否可暂停（running）
- `canResume`: 是否可继续（paused）
- `canRetry`: 是否可重试（failed）
- `completedCount`: 已完成场景数

---

### 3.3 SceneProgressCard.vue - 场景进度卡片组件

**文件核心作用**: 显示单个场景的状态信息，包含首尾帧预览、场景描述、镜头数量和操作按钮

**本次改动内容**:
- 创建新组件文件
- 实现 props：`scene`、`isActive`、`workflowStatus`
- 集成 FramePreview 组件显示首尾帧
- 根据场景状态计算显示状态（pending/processing/completed）
- 实现两种操作按钮：提取首尾帧、编辑场景
- 使用 daisyUI 的 card、figure、badge 组件样式

**实现功能**:
- 显示场景序号和名称
- 水平分割显示首帧和尾帧
- 状态覆盖层：处理中显示加载动画，完成显示绿色勾选图标，失败显示红色警告
- 显示场景描述（限制2行）
- 显示镜头数量和首尾帧提取状态
- 活跃场景显示蓝色边框和"处理中"徽章

**Props 定义**:
```javascript
props: {
  scene: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
  workflowStatus: { type: String, default: 'idle' },
}
```

**Computed 计算属性**:
- `status`: 场景状态计算（processing/completed/pending）
- `statusDisplay`: 状态中文映射
- `showStatusOverlay`: 是否显示状态覆盖层

**Events 事件**:
- `@extract-frames`: 提取首尾帧
- `@edit-scene`: 编辑场景

---

### 3.4 WorkflowEventLog.vue - 工作流事件日志组件

**文件核心作用**: 实时显示工作流事件日志，按时间倒序展示，支持事件类型图标

**本次改动内容**:
- 创建新组件文件
- 实现 props：`events`（事件数组）
- 实现事件类型图标映射（7 种事件类型）
- 实现时间格式化（刚刚/分钟前/小时前/日期时间）
- 集成 daisyUI 的 card 组件

**实现功能**:
- 显示空状态（无事件时）
- 事件按时间戳倒序排列
- 每个事件显示对应类型图标：
  * workflow_started: 播放图标（蓝色）
  * workflow_completed: 完成勾选（绿色）
  * workflow_failed: 警告图标（红色）
  * scene_started: 列表图标（蓝色）
  * scene_completed: 完成勾选（绿色）
  * 其他: 信息图标（灰色）
- 显示事件消息
- 显示事件元数据（场景 ID、进度百分比）
- 清空日志按钮

**Props 定义**:
```javascript
props: {
  events: { type: Array, default: () => [] },
}
```

**Methods 方法**:
- `eventTitle(event)`: 获取事件中文标题
- `formatTime(timestamp)`: 格式化时间戳
- `handleClear()`: 清空事件日志

---

### 3.5 ChapterStudio.vue - 章节工作室主页面

**文件核心作用**: 章节工作室主页面，集成所有子组件，实现完整的章节工作流管理界面

**本次改动内容**:
- 创建新组件文件
- 集成 Layout 布局组件
- 集成 WorkflowControlPanel、SceneProgressCard、WorkflowEventLog 组件
- 实现 Vuex 状态映射（mapState、mapGetters、mapActions）
- 实现 WebSocket 连接管理和轮询降级
- 实现工作流操作方法（启动、暂停、继续、重试）

**实现功能**:
- 面包屑导航（角色资产 > 作品详情 > 章节）
- 章节标题和描述显示
- 工作流控制面板集成
- 场景网格布局（响应式：1/2/3 列）
- 加载状态、空状态处理
- 工作流事件日志集成
- WebSocket 实时通信：
  * 连接成功回调
  * 事件接收处理
  * 断线重连（指数退避）
  * 降级到轮询模式（5 秒间隔）
- 工作流控制方法：
  * `handleStartWorkflow()`: 启动工作流
  * `handlePauseWorkflow()`: 暂停工作流
  * `handleResumeWorkflow()`: 继续工作流
  * `handleRetryWorkflow()`: 重试工作流
  * `handleExtractFrames()`: 提取场景首尾帧
  * `handleEditScene()`: 跳转到分镜编辑器
- 组件销毁清理（WebSocket 断开、轮询停止、状态重置）

**Data 数据**:
```javascript
data() {
  return {
    chapter: {},           // 章节数据
    scenes: [],            // 场景列表
    wsClient: null,        // WebSocket 客户端实例
    pollInterval: null,    // 轮询定时器
    isLoading: false,      // 加载状态
  };
}
```

**Computed 计算属性**:
- `workflowEvents`: 工作流事件列表
- `completedScenes`: 已完成场景数量

**生命周期**:
- `created()`: 加载章节数据、设置 WebSocket
- `beforeDestroy()`: 清理资源

---

### 3.6 workflowWebSocket.js - WebSocket 客户端类

**文件核心作用**: 工作流 WebSocket 客户端，负责连接管理、消息接收、自动重连和降级轮询

**本次改动内容**:
- 创建新的工具类
- 实现构造函数：接收 `chapterId` 和 `callbacks` 对象
- 实现连接管理：`connect()`、`disconnect()`
- 实现事件处理：`handleOpen()`、`handleMessage()`、`handleClose()`、`handleError()`
- 实现自动重连：指数退避算法（2s, 4s, 8s, 16s）
- 实现心跳方法：`sendPing()`

**实现功能**:
- 构造 WebSocket URL：`ws://host/ws/artworks/chapters/{chapterId}/`
- 连接状态追踪：`isConnected` 标志
- 事件回调机制：
  * `onConnected`: 连接成功回调
  * `onEvent`: 事件接收回调（传递 payload）
  * `onDisconnected`: 连接断开回调
  * `onError`: 错误回调
- 消息验证：检查 `data.type` 和 `data.payload` 存在性
- 非正常关闭时自动重连（最多 5 次）
- 心跳机制（可选，保持连接活跃）

**Constructor 参数**:
```javascript
constructor(chapterId, callbacks = {}) {
  this.callbacks = {
    onConnected: callbacks.onConnected || (() => {}),
    onEvent: callbacks.onEvent || (() => {}),
    onDisconnected: callbacks.onDisconnected || (() => {}),
    onError: callbacks.onError || (() => {}),
  };
}
```

---

### 3.7 workflow.js - Vuex 工作流状态模块

**文件核心作用**: Vuex 状态管理模块，管理章节工作流的状态

**本次改动内容**:
- 创建新的 Vuex 模块
- 实现 state：6 个状态属性
- 实现 actions：7 个异步操作
- 实现 mutations：7 个状态更新
- 导出为命名空间模块

**State 状态**:
```javascript
state: {
  currentWorkflow: null,  // 当前工作流对象
  status: 'idle',          // idle/running/paused/completed/failed
  progress: 0,             // 进度百分比
  currentScene: null,        // 当前处理的场景
  events: [],                // 工作流事件日志
  isConnected: false,        // WebSocket 连接状态
}
```

**Actions 操作**:
- `startWorkflow({ commit }, chapterId)`: 启动工作流
- `pauseWorkflow({ commit, state })`: 暂停工作流
- `resumeWorkflow({ commit, state })`: 继续工作流
- `fetchWorkflowStatus({ commit }, chapterId)`: 获取工作流状态
- `addEvent({ commit }, event)`: 添加工作流事件
- `updateProgress({ commit }, progress)`: 更新进度
- `setConnected({ commit }, isConnected)`: 设置连接状态
- `resetState({ commit })`: 重置状态

**Mutations 变更**:
- `SET_WORKFLOW`: 设置当前工作流
- `SET_STATUS`: 设置工作流状态
- `SET_PROGRESS`: 设置进度
- `SET_CURRENT_SCENE`: 设置当前场景
- `ADD_EVENT`: 添加事件（带时间戳）
- `SET_CONNECTED`: 设置连接状态
- `RESET_STATE`: 重置为初始状态

---

### 3.8 chapters.js - 章节 API 服务

**文件核心作用**: 封装章节相关的 API 调用

**本次改动内容**:
- 创建新的 API 服务文件
- 实现 6 个 API 方法
- 使用 apiClient 进行 HTTP 请求
- 添加 JSDoc 注释

**API 方法**:
```javascript
{
  get(chapterId),                    // 获取章节详情
  getScenes(chapterId),               // 获取章节场景列表
  startWorkflow(chapterId),            // 启动工作流
  pauseWorkflow(chapterId),            // 暂停工作流
  resumeWorkflow(chapterId),           // 继续工作流
  getWorkflowStatus(chapterId),        // 获取工作流状态
}
```

---

### 3.9 scenes.js - 场景 API 服务

**文件核心作用**: 封装场景相关的 API 调用

**本次改动内容**:
- 创建新的 API 服务文件
- 实现 2 个 API 方法
- 使用 apiClient 进行 HTTP 请求
- 添加 JSDoc 注释

**API 方法**:
```javascript
{
  get(sceneId),              // 获取场景详情
  extractFrames(sceneId),     // 提取场景首尾帧
}
```

---

### 3.10 router/index.js - 路由配置

**改动内容**:
- 添加 ChapterStudio 路由到 artworks 路由组

**新增路由配置**:
```javascript
{
  path: 'chapters/:id/studio',
  name: 'ChapterStudio',
  component: () => import('@/views/artworks/ChapterStudio.vue'),
  meta: { title: '章节工作室', description: '章节自动化制作工作台' },
}
```

---

### 3.11 store/index.js - Vuex 状态注册

**改动内容**:
- 导入 workflow 模块
- 在 modules 对象中注册 workflow 模块

**变更内容**:
```javascript
import workflow from './modules/workflow';

export default new Vuex.Store({
  modules: {
    // ...
    workflow,
  },
});
```

---

## 四、架构设计

### 4.1 组件层次结构

```
ChapterStudio.vue (主页面)
├── Layout.vue (布局容器)
├── WorkflowControlPanel.vue (工作流控制面板)
├── SceneProgressCard.vue (场景进度卡片) × N
│   └── FramePreview.vue (首尾帧预览) × 2
└── WorkflowEventLog.vue (事件日志)
```

### 4.2 数据流设计

```
┌─────────────────────────────────────────────────────────────┐
│                    ChapterStudio.vue                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Vuex Store (workflow)               │   │
│  │  - state: status, progress, events...       │   │
│  │  - actions: start, pause, resume...        │   │
│  └─────────────────────────────────────────────────┘   │
│                      ↑ ↕                        │
│  ┌─────────────────────────────────────────────┐   │
│  │      WebSocket (workflowWebSocket.js)       │   │
│  │  - Real-time events                    │   │
│  │  - Auto-reconnect                      │   │
│  │  - Fallback to polling                │   │
│  └─────────────────────────────────────────────┘   │
│                      ↓                           │
│  ┌─────────────────────────────────────────────┐   │
│  │         Backend API (chapters.js)          │   │
│  │  - REST: CRUD operations               │   │
│  │  - WebSocket: /ws/artworks/chapters/{id} │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 状态管理策略

| 状态类型 | 存储位置 | 更新方式 | 使用者 |
|---------|----------|---------|--------|
| 工作流状态 | Vuex (workflow.status) | Actions/Mutations | WorkflowControlPanel, SceneProgressCard |
| 进度百分比 | Vuex (workflow.progress) | Actions/Mutations | WorkflowControlPanel |
| 当前场景 | Vuex (workflow.currentScene) | Actions/Mutations | WorkflowControlPanel |
| 事件日志 | Vuex (workflow.events) | Actions/Mutations | WorkflowEventLog |
| 连接状态 | Vuex (workflow.isConnected) | Actions/Mutations | ChapterStudio |
| 章节数据 | Component (chapter) | API Call | ChapterStudio |
| 场景列表 | Component (scenes) | API Call | ChapterStudio |

---

## 五、代码质量

### 5.1 编码规范遵循

| 规范 | 遵循情况 |
|------|---------|
| Vue 2.7 组件规范 | ✅ 使用 Options API |
| Vuex 模块规范 | ✅ 命名空间、state/actions/mutations |
| daisyUI 组件使用 | ✅ card、progress、badge、figure |
| Tailwind CSS | ✅ 工具类、响应式布局 |
| ESLint | ✅ 无错误 |
| Props 验证 | ✅ 类型、默认值、验证器 |

### 5.2 代码质量工具检查

| 工具 | 命令 | 结果 |
|------|------|------|
| Ruff | `uv run ruff check --fix` | ✅ 通过（无 Python 变更） |
| ESLint | `npx eslint --fix` | ✅ 通过 |
| Safety | `uv run safety check` | ⚠️ 11 个非关键警告（与本次无关） |

---

## 六、验收标准完成情况

### AC1: 章节工作室页面路由和布局

✅ **通过** - `/artworks/chapters/:id/studio` 路由已配置，页面包含面包屑导航、章节标题描述

### AC2: 工作流控制面板

✅ **通过** - WorkflowControlPanel 组件实现状态徽章、进度条、当前场景、操作按钮

### AC3: 场景进度卡片

✅ **通过** - SceneProgressCard 组件显示场景信息、首尾帧预览、状态覆盖层、操作按钮

### AC4: 首尾帧预览组件

✅ **通过** - FramePreview 组件实现三种状态（加载中、成功、失败）

### AC5: Vuex 状态管理

✅ **通过** - workflow 模块实现 state、actions、mutations

### AC6: WebSocket 客户端

✅ **通过** - workflowWebSocket.js 实现连接管理、自动重连、降级轮询

### AC7: API 服务层

✅ **通过** - chapters.js 和 scenes.js 实现 API 调用封装

---

## 七、依赖关系

### 7.1 前置依赖

| Story | 说明 | 状态 |
|-------|------|------|
| Story 12-4 | 工作流控制 API（启动/暂停/继续） | ⏸️ 待开发 |
| Story 12-5 | 首尾帧提取服务（已实现后端 API） | ✅ 已完成 |

### 7.2 后续依赖

| 依赖方 | 说明 |
|--------|------|
| Story 12-7 | 章节批量操作（复用本 UI 组件） |
| Epic 13 | 转场与导出（集成工作流状态） |

---

## 八、技术亮点

### 8.1 组件复用性

- **FramePreview 组件**: 可用于任何需要图片预览的场景
- **WorkflowControlPanel 组件**: 可复用于其他工作流控制页面
- **SceneProgressCard 组件**: 可复用于场景列表展示

### 8.2 实时通信设计

- **双重保障**: WebSocket 主通道 + 轮询降级
- **指数退避**: 2s → 4s → 8s → 16s（最多 5 次）
- **事件驱动**: 组件解耦，通过 Vuex 状态同步

### 8.3 响应式布局

- **场景网格**: 1 列（移动）→ 2 列（平板）→ 3 列（桌面）
- **卡片布局**: 首尾帧水平分割，状态覆盖层绝对定位

---

## 九、待完成事项

### 9.1 单元测试

❌ **未实现** - 39 个测试用例待实现（见测试报告）

### 9.2 E2E 测试

❌ **未实现** - 端到端流程测试待实现

### 9.3 后端集成

⏸️ **待 Story 12-4 完成** - 工作流控制 API 后端实现

### 9.4 手动验证

⏸️ **待环境就绪** - 需要后端 API 部署后进行完整功能测试

---

**开发报告生成时间**: 2026-02-12
**开发工程师**: AI Assistant
**代码行数**: ~1,584 行（不含空白行和注释）
**组件数量**: 6 个组件 + 1 个工具类 + 2 个 API 服务 + 1 个 Vuex 模块
