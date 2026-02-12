# Story 12-6: 章节工作室 UI - 开发故事文件（锁定版）

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P0
> **预估工作量:** 2-3天
> **依赖:** 12-1.1, 12-1.2, 12-1.3, 12-4, 12-5, Epic 11.2, Epic 11.4
> **状态:** ready-for-dev
> **锁定日期:** 2026-02-12

---

## 📋 需求描述

### 用户故事

> 作为内容创作者，我希望有一个统一的章节工作室界面，能够一键启动章节的自动化制作流程，实时查看进度，并在需要时暂停/继续工作流，以便高效完成章节内容制作。

### 功能说明

| 功能 | 描述 |
|------|------|
| **工作流控制面板** | 一键启动、暂停、继续章节工作流，显示当前状态 |
| **场景进度可视化** | 卡片式展示所有场景的完成状态，实时更新进度 |
| **实时进度推送** | 通过 WebSocket 接收工作流进度更新 |
| **首尾帧预览** | 显示场景的首帧和尾帧（由 Story 12-5 生成） |
| **错误处理与提示** | 显示工作流错误信息，提供重试和修复建议 |
| **场景快速操作** | 跳转到 StoryboardEditor 编辑特定场景 |
| **工作流事件历史** | 显示工作流的操作日志（可选展开） |

### 业务价值

- **效率提升**：自动化处理章节内所有场景，替代手动逐个处理
- **质量保证**：统一的首尾帧提取，为转场提供素材基础
- **用户体验**：可视化进度反馈，让用户了解当前处理状态
- **灵活性**：支持暂停/继续，允许用户在处理过程中调整参数

### 边界条件

| 场景 | 预期行为 |
|------|----------|
| 章节没有场景 | 显示空状态提示，引导用户先添加场景 |
| 工作流运行中 | 禁用启动按钮，启用暂停按钮 |
| 工作流暂停中 | 禁用暂停按钮，启用继续按钮 |
| 工作流已完成 | 显示完成状态，启用重新启动按钮 |
| 工作流失败 | 显示错误信息，提供重试按钮 |
| WebSocket 断开 | 降级到轮询模式（5秒间隔） |
| 场景无首尾帧 | 显示"待提取"占位图，点击可手动触发提取 |

### 验收标准

- [ ] AC1: ChapterStudio.vue 页面组件完整实现，路由配置正确
- [ ] AC2: WorkflowControlPanel 组件支持启动/暂停/继续/状态查询
- [ ] AC3: SceneProgressCard 组件显示场景状态（待处理/处理中/已完成/失败）
- [ ] AC4: WebSocket 连接正常，实时接收进度更新
- [ ] AC5: 首尾帧预览正常显示（支持加载状态和错误处理）
- [ ] AC6: 错误提示清晰，包含重试和修复建议
- [ ] AC7: 支持跳转到 StoryboardEditor 编辑特定场景
- [ ] AC8: 响应式布局适配（桌面端/平板端）
- [ ] AC9: API 集成测试通过（4个端点）
- [ ] AC10: WebSocket 事件处理测试通过
- [ ] AC11: 组件单元测试覆盖率 >80%
- [ ] AC12: API 文档和组件使用文档完整

---

## 🔧 技术上下文

### 关联文件路径

```
frontend/
├── src/
│   ├── views/
│   │   └── artworks/
│   │       └── ChapterStudio.vue              # 新建：章节工作室主页面
│   ├── components/
│   │   └── artworks/
│   │       ├── WorkflowControlPanel.vue      # 新建：工作流控制面板
│   │       ├── SceneProgressCard.vue         # 新建：场景进度卡片
│   │       ├── WorkflowEventLog.vue         # 新建：工作流事件日志
│   │       └── FramePreview.vue             # 新建：首尾帧预览组件
│   ├── router/
│   │   └── index.js                        # 修改：添加章节工作室路由
│   ├── services/
│   │   └── api/
│   │       └── chapters.js                # 新建：章节 API 服务
│   └── utils/
│       └── workflowWebSocket.js            # 新建：工作流 WebSocket 客户端
```

### 依赖组件

| 组件 | 来源 Story/Epic | 职责 |
|-------|---------------|--------|
| `WorkflowStateMachine` | Story 12-2 | 后端状态机服务 |
| `ChapterWorkflow` API | Story 12-4 | 工作流控制端点 |
| `FrameExtractionService` | Story 12-5 | 首尾帧提取服务 |
| `ProgressBar` | Epic 11.4 | 进度条组件（可复用） |
| `ShotList` | Epic 11.2 | 镜头列表（跳转目标） |
| `RedisStreamPublisher` | Epic 3 | WebSocket 进度推送 |
| `daisyUI` | UI框架 | 按钮、卡片、进度条等基础组件 |
| `Tailwind CSS` | CSS框架 | 响应式布局 |

### 后端 API 端点

**工作流控制 API（Story 12-4 已实现）：**

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/artworks/chapters/{id}/start-workflow/` | POST | 启动工作流 |
| `/api/v1/artworks/chapters/{id}/pause-workflow/` | POST | 暂停工作流 |
| `/api/v1/artworks/chapters/{id}/resume-workflow/` | POST | 继续工作流 |
| `/api/v1/artworks/chapters/{id}/workflow-status/` | GET | 查询工作流状态 |

**场景 API（已存在）：**

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/artworks/chapters/{id}/scenes/` | GET | 获取章节所有场景 |
| `/api/v1/artworks/scenes/{id}/` | GET | 获取场景详情 |
| `/api/v1/artworks/scenes/{id}/extract-frames/` | POST | 提取首尾帧 |

### WebSocket 事件格式

**频道：** `workflow:{workflow_id}`

| 事件类型 | 数据结构 | 描述 |
|---------|----------|------|
| `workflow_started` | `{workflow_id, chapter_id}` | 工作流启动 |
| `scene_started` | `{scene_id, scene_title}` | 场景处理开始 |
| `scene_completed` | `{scene_id, progress}` | 场景处理完成 |
| `workflow_paused` | `{workflow_id, current_scene}` | 工作流暂停 |
| `workflow_resumed` | `{workflow_id, current_scene}` | 工作流继续 |
| `workflow_completed` | `{workflow_id, total_scenes}` | 工作流完成 |
| `workflow_failed` | `{workflow_id, error_message}` | 工作流失败 |

---

## 🏗️ 架构设计

### 页面结构

```
┌─────────────────────────────────────────────────────────────────┐
│  ChapterStudio.vue (章节工作室主页面)                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 页面头部                                               │  │
│  │ - 面包屑导航：作品 > 章节 > 工作室                          │  │
│  │ - 章节标题和描述                                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ WorkflowControlPanel.vue (工作流控制面板)                    │  │
│  │ - 当前状态徽章（待处理/运行中/已暂停/已完成/失败）              │  │
│  │ - 进度条（0-100%）                                       │  │
│  │ - 操作按钮：启动 / 暂停 / 继续 / 重新启动                        │  │
│  │ - 统计信息：总场景数 / 已完成 / 耗时                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ 场景网格（响应式：grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3）│  │
│  │  ┌──────────────────┐  ┌──────────────────┐            │  │
│  │  │ SceneProgressCard │  │ SceneProgressCard │            │  │
│  │  │ 场景 1          │  │ 场景 2          │            │  │
│  │  │ - 首尾帧预览    │  │ - 首尾帧预览    │            │  │
│  │  │ - 状态徽章      │  │ - 状态徽章      │            │  │
│  │  │ - 编辑按钮      │  │ - 编辑按钮      │            │  │
│  │  └──────────────────┘  └──────────────────┘            │  │
│  │  ... 更多场景卡片 ...                                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ WorkflowEventLog.vue (可折叠的事件日志)                     │  │
│  │ - [展开] 10:00:00 工作流启动                             │  │
│  │ - [展开] 10:00:15 场景 1 处理开始                         │  │
│  │ - [展开] 10:01:30 场景 1 处理完成                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 路由配置

```javascript
// src/router/index.js

{
  path: '/artworks',
  component: () => import('@/views/Layout.vue'),
  meta: { requiresAuth: true },
  children: [
    {
      path: 'chapters/:id/studio',
      name: 'ChapterStudio',
      component: () => import('@/views/artworks/ChapterStudio.vue'),
      meta: {
        title: '章节工作室',
        description: '章节自动化制作工作台'
      }
    },
    // ... 其他 artworks 路由
  ],
}
```

### 状态管理（Vuex）

**新增模块：`workflow.js`**

```javascript
// src/store/modules/workflow.js

const state = {
  currentWorkflow: null,      // 当前工作流对象
  status: 'idle',            // idle/running/paused/completed/failed
  progress: 0,               // 进度百分比
  currentScene: null,         // 当前处理的场景
  events: [],                 // 工作流事件日志
  isConnected: false,         // WebSocket 连接状态
};

const actions = {
  async startWorkflow({ commit }, chapterId) {
    commit('SET_STATUS', 'starting');
    const workflow = await api.chapters.startWorkflow(chapterId);
    commit('SET_WORKFLOW', workflow);
    commit('SET_STATUS', 'running');
  },

  async pauseWorkflow({ commit, state }) {
    const workflowId = state.currentWorkflow?.workflow_id;
    if (!workflowId) return;

    await api.chapters.pauseWorkflow(workflowId);
    commit('SET_STATUS', 'paused');
  },

  async resumeWorkflow({ commit, state }) {
    const workflowId = state.currentWorkflow?.workflow_id;
    if (!workflowId) return;

    await api.chapters.resumeWorkflow(workflowId);
    commit('SET_STATUS', 'running');
  },

  async fetchWorkflowStatus({ commit }, chapterId) {
    const workflow = await api.chapters.getWorkflowStatus(chapterId);
    commit('SET_WORKFLOW', workflow);
  },

  addEvent({ commit }, event) {
    commit('ADD_EVENT', event);
  },

  updateProgress({ commit }, progress) {
    commit('SET_PROGRESS', progress);
  },
};

const mutations = {
  SET_WORKFLOW(state, workflow) {
    state.currentWorkflow = workflow;
  },

  SET_STATUS(state, status) {
    state.status = status;
  },

  SET_PROGRESS(state, progress) {
    state.progress = progress;
  },

  SET_CURRENT_SCENE(state, scene) {
    state.currentScene = scene;
  },

  ADD_EVENT(state, event) {
    state.events.unshift({
      ...event,
      timestamp: new Date().toISOString(),
    });
  },

  SET_CONNECTED(state, isConnected) {
    state.isConnected = isConnected;
  },

  RESET_STATE(state) {
    Object.assign(state, {
      currentWorkflow: null,
      status: 'idle',
      progress: 0,
      currentScene: null,
      events: [],
      isConnected: false,
    });
  },
};

export default {
  namespaced: true,
  state,
  actions,
  mutations,
};
```

---

## 💻 实现指南

### 任务清单

- [ ] 1. 创建 `ChapterStudio.vue` 主页面组件
- [ ] 2. 创建 `WorkflowControlPanel.vue` 组件
- [ ] 3. 创建 `SceneProgressCard.vue` 组件
- [ ] 4. 创建 `WorkflowEventLog.vue` 组件（可选）
- [ ] 5. 创建 `FramePreview.vue` 组件
- [ ] 6. 创建 `chapters.js` API 服务
- [ ] 7. 创建 `workflowWebSocket.js` WebSocket 客户端
- [ ] 8. 创建 `workflow.js` Vuex 模块
- [ ] 9. 配置路由
- [ ] 10. 实现 WebSocket 事件处理
- [ ] 11. 实现错误处理和重试逻辑
- [ ] 12. 编写单元测试
- [ ] 13. 编写 API 集成测试
- [ ] 14. 更新组件使用文档

### 主页面组件实现

```vue
<!-- src/views/artworks/ChapterStudio.vue -->
<template>
  <Layout>
    <div class="chapter-studio p-6">
      <!-- 页面头部 -->
      <div class="mb-6">
        <div class="text-sm breadcrumbs mb-2">
          <ul>
            <li><router-link to="/artworks">作品列表</router-link></li>
            <li><router-link :to="`/artworks/${artworkId}`">{{ artwork?.title }}</router-link></li>
            <li>{{ chapter?.title }} - 工作室</li>
          </ul>
        </div>
        <h1 class="text-3xl font-bold mb-2">{{ chapter?.title }}</h1>
        <p class="text-base-content/70" v-if="chapter">
          {{ chapter.original_text?.substring(0, 200) }}...
        </p>
      </div>

      <!-- 空状态：无场景 -->
      <div
        v-if="!loading && scenes.length === 0"
        class="flex flex-col items-center justify-center py-20 bg-base-200 rounded-lg"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-base-content/20 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
        </svg>
        <h3 class="text-xl font-semibold mb-2">该章节还没有场景</h3>
        <p class="text-base-content/60 mb-4">请先添加场景，然后再启动工作流</p>
        <button class="btn btn-primary" @click="goToStoryboard">
          前往分镜编辑器
        </button>
      </div>

      <!-- 主内容 -->
      <template v-else>
        <!-- 工作流控制面板 -->
        <WorkflowControlPanel
          :status="workflowStatus"
          :progress="workflowProgress"
          :current-scene="currentScene"
          :total-scenes="scenes.length"
          :completed-scenes="completedScenes"
          :is-loading="isLoading"
          @start="handleStartWorkflow"
          @pause="handlePauseWorkflow"
          @resume="handleResumeWorkflow"
          @retry="handleRetryWorkflow"
          class="mb-6"
        />

        <!-- 场景网格 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SceneProgressCard
            v-for="scene in scenes"
            :key="scene.id"
            :scene="scene"
            :is-active="currentScene?.id === scene.id"
            :workflow-status="workflowStatus"
            @edit="goToSceneEditor"
            @extract-frames="handleExtractFrames"
          />
        </div>

        <!-- 工作流事件日志 -->
        <WorkflowEventLog
          v-if="showEventLog"
          :events="workflowEvents"
          class="mt-6"
        />
      </template>
    </div>
  </Layout>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import Layout from '@/components/Layout.vue';
import WorkflowControlPanel from '@/components/artworks/WorkflowControlPanel.vue';
import SceneProgressCard from '@/components/artworks/SceneProgressCard.vue';
import WorkflowEventLog from '@/components/artworks/WorkflowEventLog.vue';
import api from '@/services/api/chapters';
import WorkflowWebSocket from '@/utils/workflowWebSocket';

export default {
  name: 'ChapterStudio',

  components: {
    Layout,
    WorkflowControlPanel,
    SceneProgressCard,
    WorkflowEventLog,
  },

  data() {
    return {
      chapterId: null,
      artworkId: null,
      chapter: null,
      artwork: null,
      scenes: [],
      loading: true,
      wsClient: null,
      showEventLog: false,
    };
  },

  computed: {
    ...mapState('workflow', [
      'status',
      'progress',
      'currentScene',
      'events',
      'isConnected',
    ]),

    workflowStatus() {
      return this.status;
    },

    workflowProgress() {
      return this.progress;
    },

    workflowEvents() {
      return this.events;
    },

    completedScenes() {
      return this.scenes.filter(scene => scene.is_completed).length;
    },

    isLoading() {
      return this.loading || ['starting', 'stopping'].includes(this.status);
    },
  },

  async mounted() {
    this.chapterId = parseInt(this.$route.params.id);
    await this.loadChapterData();
    this.setupWebSocket();
  },

  beforeDestroy() {
    this.cleanup();
  },

  methods: {
    ...mapActions('workflow', [
      'startWorkflow',
      'pauseWorkflow',
      'resumeWorkflow',
      'fetchWorkflowStatus',
      'addEvent',
      'updateProgress',
      'resetState',
    ]),

    async loadChapterData() {
      try {
        this.loading = true;

        // 加载章节详情
        const chapter = await api.chapters.get(this.chapterId);
        this.chapter = chapter;

        // 加载作品信息
        this.artworkId = chapter.artwork;
        this.artwork = await api.artworks.get(this.artworkId);

        // 加载场景列表
        this.scenes = await api.chapters.getScenes(this.chapterId);

        // 加载工作流状态
        await this.fetchWorkflowStatus(this.chapterId);

      } catch (error) {
        this.$message.error(`加载数据失败: ${error.message}`);
      } finally {
        this.loading = false;
      }
    },

    setupWebSocket() {
      this.wsClient = new WorkflowWebSocket(
        this.$route.params.id,
        {
          onConnected: () => {
            console.log('WebSocket 已连接');
          },
          onEvent: (event) => {
            this.handleWorkflowEvent(event);
          },
          onDisconnected: () => {
            console.warn('WebSocket 断开，启用轮询模式');
            this.startPolling();
          },
          onError: (error) => {
            console.error('WebSocket 错误:', error);
            this.$message.warning('实时连接不稳定，已切换到轮询模式');
          },
        }
      );

      this.wsClient.connect();
    },

    handleWorkflowEvent(event) {
      this.addEvent(event);

      switch (event.type) {
        case 'scene_started':
          this.currentScene = { id: event.scene_id, title: event.scene_title };
          break;

        case 'scene_completed':
          this.updateProgress(event.progress);
          // 更新场景状态
          const sceneIndex = this.scenes.findIndex(s => s.id === event.scene_id);
          if (sceneIndex !== -1) {
            this.scenes[sceneIndex].is_completed = true;
          }
          break;

        case 'workflow_completed':
          this.updateProgress(100);
          this.$message.success('工作流已完成！');
          break;

        case 'workflow_failed':
          this.$message.error(`工作流失败: ${event.error_message}`);
          break;
      }
    },

    async handleStartWorkflow() {
      try {
        await this.startWorkflow(this.chapterId);
        this.$message.success('工作流已启动');
      } catch (error) {
        this.$message.error(`启动失败: ${error.response?.data?.error || error.message}`);
      }
    },

    async handlePauseWorkflow() {
      try {
        await this.pauseWorkflow();
        this.$message.success('工作流已暂停');
      } catch (error) {
        this.$message.error(`暂停失败: ${error.message}`);
      }
    },

    async handleResumeWorkflow() {
      try {
        await this.resumeWorkflow();
        this.$message.success('工作流已继续');
      } catch (error) {
        this.$message.error(`继续失败: ${error.message}`);
      }
    },

    async handleRetryWorkflow() {
      try {
        await this.startWorkflow(this.chapterId);
        this.$message.success('工作流已重新启动');
      } catch (error) {
        this.$message.error(`重试失败: ${error.message}`);
      }
    },

    goToSceneEditor(scene) {
      this.$router.push({
        name: 'StoryboardEditor',
        params: { chapterId: this.chapterId, sceneId: scene.id },
      });
    },

    goToStoryboard() {
      this.$router.push({
        name: 'StoryboardEditor',
        params: { chapterId: this.chapterId },
      });
    },

    async handleExtractFrames(scene) {
      try {
        await api.scenes.extractFrames(scene.id);
        this.$message.success('首尾帧提取已开始');
        // 刷新场景数据
        const updated = await api.scenes.get(scene.id);
        const index = this.scenes.findIndex(s => s.id === scene.id);
        if (index !== -1) {
          this.$set(this.scenes, index, updated);
        }
      } catch (error) {
        this.$message.error(`提取失败: ${error.message}`);
      }
    },

    startPolling() {
      // 降级到轮询模式
      this.pollingInterval = setInterval(async () => {
        await this.fetchWorkflowStatus(this.chapterId);
      }, 5000);
    },

    cleanup() {
      if (this.wsClient) {
        this.wsClient.disconnect();
      }
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
      }
      this.resetState();
    },
  },
};
</script>

<style scoped>
.chapter-studio {
  min-height: 100vh;
}
</style>
```

### 工作流控制面板组件

```vue
<!-- src/components/artworks/WorkflowControlPanel.vue -->
<template>
  <div class="workflow-control-panel card bg-base-100 shadow-xl">
    <div class="card-body">
      <!-- 状态行 -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="badge" :class="statusBadgeClass">{{ statusDisplay }}</div>
          <h2 class="card-title">章节工作流控制</h2>
        </div>
        <div class="text-sm text-base-content/60">
          {{ completedCount }} / {{ totalScenes }} 场景已完成
        </div>
      </div>

      <!-- 进度条 -->
      <div class="mb-4">
        <progress
          class="progress progress-primary w-full"
          :value="progress"
          max="100"
        ></progress>
        <div class="text-xs text-center mt-1">{{ progress }}%</div>
      </div>

      <!-- 当前场景 -->
      <div v-if="currentScene" class="mb-4">
        <div class="text-sm text-base-content/60 mb-1">当前处理:</div>
        <div class="font-medium">{{ currentScene.title || `场景 ${currentScene.id}` }}</div>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions justify-end">
        <button
          v-if="canStart"
          class="btn btn-primary"
          :class="{ 'loading': isLoading }"
          :disabled="isLoading"
          @click="$emit('start')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          启动工作流
        </button>

        <button
          v-if="canPause"
          class="btn btn-warning"
          :disabled="isLoading"
          @click="$emit('pause')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          暂停
        </button>

        <button
          v-if="canResume"
          class="btn btn-success"
          :disabled="isLoading"
          @click="$emit('resume')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
          </svg>
          继续
        </button>

        <button
          v-if="canRetry"
          class="btn btn-error"
          :disabled="isLoading"
          @click="$emit('retry')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          重新启动
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkflowControlPanel',

  props: {
    status: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'running', 'paused', 'completed', 'failed'].includes(value),
    },
    progress: {
      type: Number,
      default: 0,
    },
    currentScene: {
      type: Object,
      default: null,
    },
    totalScenes: {
      type: Number,
      required: true,
    },
    completedScenes: {
      type: Number,
      default: 0,
    },
    isLoading: {
      type: Boolean,
      default: false,
    },
  },

  computed: {
    statusDisplay() {
      const displays = {
        idle: '待处理',
        running: '运行中',
        paused: '已暂停',
        completed: '已完成',
        failed: '失败',
      };
      return displays[this.status] || '未知';
    },

    statusBadgeClass() {
      const classes = {
        idle: 'badge-ghost',
        running: 'badge-primary',
        paused: 'badge-warning',
        completed: 'badge-success',
        failed: 'badge-error',
      };
      return classes[this.status] || 'badge-ghost';
    },

    canStart() {
      return ['idle', 'completed', 'failed'].includes(this.status);
    },

    canPause() {
      return this.status === 'running';
    },

    canResume() {
      return this.status === 'paused';
    },

    canRetry() {
      return this.status === 'failed';
    },

    completedCount() {
      return this.completedScenes || 0;
    },
  },
};
</script>

<style scoped>
.workflow-control-panel {
  /* 可以添加自定义样式 */
}
</style>
```

### 场景进度卡片组件

```vue
<!-- src/components/artworks/SceneProgressCard.vue -->
<template>
  <div class="scene-progress-card card bg-base-100 shadow-md" :class="{ 'ring-2 ring-primary': isActive }">
    <figure class="px-4 pt-4">
      <div class="relative aspect-video bg-base-200 rounded-lg overflow-hidden">
        <!-- 首尾帧预览 -->
        <div class="flex h-full">
          <FramePreview
            :image-url="scene.head_frame"
            :fallback-icon="'🎬'"
            label="首帧"
            class="flex-1"
          />
          <FramePreview
            :image-url="scene.tail_frame"
            :fallback-icon="'🎞'"
            label="尾帧"
            class="flex-1 border-l border-base-300"
          />
        </div>

        <!-- 状态覆盖层 -->
        <div v-if="showStatusOverlay" class="absolute inset-0 bg-black/60 flex items-center justify-center">
          <div class="text-white text-center">
            <svg v-if="status === 'processing'" xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <svg v-else-if="status === 'completed'" xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="status === 'failed'" xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-sm">{{ statusDisplay }}</div>
          </div>
        </div>

        <!-- 活跃指示器 -->
        <div v-if="isActive" class="absolute top-2 left-2 badge badge-primary">处理中</div>
      </div>
    </figure>

    <div class="card-body p-4">
      <h3 class="card-title text-base">
        场景 {{ scene.scene_number }}: {{ scene.scene_name }}
      </h3>
      <p class="text-xs text-base-content/60 line-clamp-2 mb-3">
        {{ scene.description }}
      </p>

      <!-- 场景统计 -->
      <div class="flex gap-4 text-xs text-base-content/60 mb-3">
        <span>{{ scene.shot_count || 0 }} 个镜头</span>
        <span v-if="scene.head_frame || scene.tail_frame">已提取帧</span>
        <span v-else class="text-warning">待提取帧</span>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions justify-end">
        <button
          v-if="!scene.head_frame && !scene.tail_frame && workflowStatus !== 'running'"
          class="btn btn-sm btn-ghost"
          @click="$emit('extract-frames', scene)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          提取首尾帧
        </button>

        <button
          class="btn btn-sm btn-primary"
          @click="$emit('edit', scene)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          编辑场景
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import FramePreview from './FramePreview.vue';

export default {
  name: 'SceneProgressCard',

  components: {
    FramePreview,
  },

  props: {
    scene: {
      type: Object,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: false,
    },
    workflowStatus: {
      type: String,
      default: 'idle',
    },
  },

  computed: {
    status() {
      if (this.isActive) return 'processing';
      if (this.scene.is_completed) return 'completed';
      return 'pending';
    },

    statusDisplay() {
      const displays = {
        pending: '待处理',
        processing: '处理中',
        completed: '已完成',
        failed: '失败',
      };
      return displays[this.status];
    },

    showStatusOverlay() {
      return ['processing', 'completed', 'failed'].includes(this.status);
    },
  },
};
</script>

<style scoped>
.scene-progress-card {
  transition: all 0.2s ease;
}

.scene-progress-card:hover {
  transform: translateY(-2px);
}

.scene-progress-card.ring-2 {
  transform: translateY(-2px);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
}
</style>
```

### API 服务实现

```javascript
// src/services/api/chapters.js

import client from './client';

export default {
  /**
   * 获取章节详情
   */
  async get(chapterId) {
    const response = await client.get(`/artworks/chapters/${chapterId}/`);
    return response.data;
  },

  /**
   * 获取章节的所有场景
   */
  async getScenes(chapterId) {
    const response = await client.get(`/artworks/chapters/${chapterId}/scenes/`);
    return response.data;
  },

  /**
   * 启动工作流
   */
  async startWorkflow(chapterId) {
    const response = await client.post(`/artworks/chapters/${chapterId}/start-workflow/`);
    return response.data;
  },

  /**
   * 暂停工作流
   */
  async pauseWorkflow(chapterId) {
    const response = await client.post(`/artworks/chapters/${chapterId}/pause-workflow/`);
    return response.data;
  },

  /**
   * 继续工作流
   */
  async resumeWorkflow(chapterId) {
    const response = await client.post(`/artworks/chapters/${chapterId}/resume-workflow/`);
    return response.data;
  },

  /**
   * 获取工作流状态
   */
  async getWorkflowStatus(chapterId) {
    const response = await client.get(`/artworks/chapters/${chapterId}/workflow-status/`);
    return response.data;
  },
};

// src/services/api/scenes.js

import client from './client';

export default {
  /**
   * 获取场景详情
   */
  async get(sceneId) {
    const response = await client.get(`/artworks/scenes/${sceneId}/`);
    return response.data;
  },

  /**
   * 提取首尾帧
   */
  async extractFrames(sceneId) {
    const response = await client.post(`/artworks/scenes/${sceneId}/extract-frames/`);
    return response.data;
  },
};
```

### WebSocket 客户端实现

```javascript
// src/utils/workflowWebSocket.js

/**
 * 工作流 WebSocket 客户端
 *
 * 负责：
 * - 连接到 Redis Stream WebSocket 频道
 * - 接收工作流进度事件
 * - 处理连接断开重连
 * - 降级到轮询模式
 */
export default class WorkflowWebSocket {
  constructor(chapterId, callbacks = {}) {
    this.chapterId = chapterId;
    this.callbacks = {
      onConnected: callbacks.onConnected || (() => {}),
      onEvent: callbacks.onEvent || (() => {}),
      onDisconnected: callbacks.onDisconnected || (() => {}),
      onError: callbacks.onError || (() => {}),
    };

    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000; // 2秒
    this.isConnected = false;
  }

  connect() {
    try {
      // 构造 WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.VUE_APP_WS_HOST || window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/ws/artworks/chapters/${this.chapterId}/`;

      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);

    } catch (error) {
      this.callbacks.onError(error);
      this.callbacks.onDisconnected();
    }
  }

  disconnect() {
    if (this.socket) {
      this.reconnectAttempts = this.maxReconnectAttempts; // 防止自动重连
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
    }
  }

  handleOpen() {
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.callbacks.onConnected();
  }

  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);

      // 验证事件格式
      if (data.type && data.payload) {
        this.callbacks.onEvent(data.payload);
      }
    } catch (error) {
      console.error('解析 WebSocket 消息失败:', error);
    }
  }

  handleClose(event) {
    this.isConnected = false;
    this.socket = null;

    // 非正常关闭时尝试重连
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      setTimeout(() => this.connect(), delay);
    } else {
      this.callbacks.onDisconnected();
    }
  }

  handleError(error) {
    console.error('WebSocket 错误:', error);
    this.callbacks.onError(error);
  }

  /**
   * 发送心跳（可选）
   */
  sendPing() {
    if (this.isConnected && this.socket) {
      this.socket.send(JSON.stringify({ type: 'ping' }));
    }
  }
}
```

---

## 🧪 测试策略

### 测试覆盖范围

| 测试类别 | 用例数 | 覆盖内容 |
|----------|--------|----------|
| **组件单元测试** | 15 | 组件渲染、交互、props 验证 |
| **API 集成测试** | 8 | 4个端点的正常/异常流程 |
| **WebSocket 测试** | 6 | 连接、事件接收、断线重连 |
| **Vuex 模块测试** | 10 | 状态管理、actions、mutations |
| **总计** | **39** | **目标覆盖率 >80%** |

### 组件单元测试

```javascript
// src/components/artworks/__tests__/WorkflowControlPanel.test.js

import { mount } from '@vue/test-utils';
import WorkflowControlPanel from '../WorkflowControlPanel.vue';

describe('WorkflowControlPanel', () => {
  it('显示正确的状态徽章', () => {
    const statuses = ['idle', 'running', 'paused', 'completed', 'failed'];

    statuses.forEach(status => {
      const wrapper = mount(WorkflowControlPanel, {
        propsData: { status, totalScenes: 5 },
      });

      expect(wrapper.text()).toContain({
        idle: '待处理',
        running: '运行中',
        paused: '已暂停',
        completed: '已完成',
        failed: '失败',
      }[status]);
    });
  });

  it('根据状态显示正确的按钮', () => {
    const testCases = [
      { status: 'idle', expectedButton: '启动' },
      { status: 'running', expectedButton: '暂停' },
      { status: 'paused', expectedButton: '继续' },
      { status: 'failed', expectedButton: '重新启动' },
    ];

    testCases.forEach(({ status, expectedButton }) => {
      const wrapper = mount(WorkflowControlPanel, {
        propsData: { status, totalScenes: 5 },
      });

      expect(wrapper.text()).toContain(expectedButton);
    });
  });

  it('禁用加载中的按钮', () => {
    const wrapper = mount(WorkflowControlPanel, {
      propsData: { status: 'idle', totalScenes: 5, isLoading: true },
    });

    const button = wrapper.find('button');
    expect(button.attributes('disabled')).toBeDefined();
  });

  it('正确计算进度百分比', () => {
    const wrapper = mount(WorkflowControlPanel, {
      propsData: {
        status: 'running',
        totalScenes: 10,
        completedScenes: 6,
        progress: 60,
      },
    });

    expect(wrapper.text()).toContain('60%');
    expect(wrapper.text()).toContain('6 / 10 场景已完成');
  });
});
```

### API 集成测试

```javascript
// src/services/api/__tests__/chapters.test.js

import api from '@/services/api/chapters';
import { expect } from 'chai';

describe('Chapters API', () => {
  const chapterId = 1;

  describe('startWorkflow', () => {
    it('成功启动工作流', async () => {
      const result = await api.startWorkflow(chapterId);

      expect(result).to.have.property('workflow_id');
      expect(result).to.have.property('status', 'pending');
      expect(result).to.have.property('total_scenes');
    });

    it('处理已有运行中工作流的错误', async () => {
      try {
        await api.startWorkflow(chapterId);
        throw new Error('应该抛出错误');
      } catch (error) {
        expect(error.response?.status).to.equal(400);
        expect(error.response?.data?.error).to.include('运行中');
      }
    });
  });

  describe('pauseWorkflow', () => {
    it('成功暂停工作流', async () => {
      const result = await api.pauseWorkflow(chapterId);

      expect(result).to.have.property('status', 'paused');
    });
  });

  describe('resumeWorkflow', () => {
    it('成功继续工作流', async () => {
      const result = await api.resumeWorkflow(chapterId);

      expect(result).to.have.property('status', 'running');
    });
  });

  describe('getWorkflowStatus', () => {
    it('获取工作流状态', async () => {
      const result = await api.getWorkflowStatus(chapterId);

      expect(result).to.have.property('workflow_id');
      expect(result).to.have.property('status');
      expect(result).to.have.property('progress_percentage');
    });
  });
});
```

### WebSocket 测试

```javascript
// src/utils/__tests__/workflowWebSocket.test.js

import WorkflowWebSocket from '../workflowWebSocket';

describe('WorkflowWebSocket', () => {
  let mockSocket;

  beforeEach(() => {
    mockSocket = {
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
    };

    global.WebSocket = jest.fn(() => mockSocket);
  });

  it('成功建立连接', (done) => {
    const callbacks = {
      onConnected: () => {
        expect(mockSocket.onopen).toBeDefined();
        done();
      },
    };

    const ws = new WorkflowWebSocket(1, callbacks);
    ws.connect();

    // 模拟连接成功
    mockSocket.onopen();
  });

  it('接收并解析事件', (done) => {
    const mockEvent = {
      type: 'scene_started',
      payload: { scene_id: 123, scene_title: '场景1' },
    };

    const callbacks = {
      onEvent: (event) => {
        expect(event).toEqual(mockEvent.payload);
        done();
      },
    };

    const ws = new WorkflowWebSocket(1, callbacks);
    ws.connect();

    // 模拟接收消息
    mockSocket.onmessage({ data: JSON.stringify(mockEvent) });
  });

  it('连接断开后自动重连', (done) => {
    let reconnectCount = 0;

    const callbacks = {
      onConnected: () => {
        reconnectCount++;
        if (reconnectCount === 1) {
          // 第一次连接成功后，模拟断开
          mockSocket.onclose({ code: 1006 });
        } else {
          // 第二次连接成功
          expect(reconnectCount).toBe(2);
          done();
        }
      },
    };

    const ws = new WorkflowWebSocket(1, callbacks);
    ws.connect();

    // 第一次连接成功
    mockSocket.onopen();
  });
});
```

### 执行测试命令

```bash
# ========== 单元测试 ==========
cd frontend

# 组件测试
npm run test:unit -- components/artworks/__tests__/

# Vuex 模块测试
npm run test:unit -- store/modules/__tests__/

# ========== 集成测试 ==========
# API 测试（需要 mock 后端）
npm run test:integration -- services/api/__tests__/

# ========== E2E 测试 ==========
# 完整流程测试（需要启动后端）
npm run test:e2e -- chapter-studio.spec.js

# ========== 覆盖率报告 ==========
npm run test:coverage -- --path=chapter-studio

# 目标覆盖率 >80%
```

---

## 📦 部署检查清单

### 代码变更

- [ ] `src/views/artworks/ChapterStudio.vue` - 新建主页面
- [ ] `src/components/artworks/WorkflowControlPanel.vue` - 新建控制面板
- [ ] `src/components/artworks/SceneProgressCard.vue` - 新建进度卡片
- [ ] `src/components/artworks/WorkflowEventLog.vue` - 新建事件日志
- [ ] `src/components/artworks/FramePreview.vue` - 新建首尾帧预览
- [ ] `src/services/api/chapters.js` - 新建章节 API
- [ ] `src/services/api/scenes.js` - 扩展场景 API
- [ ] `src/utils/workflowWebSocket.js` - 新建 WebSocket 客户端
- [ ] `src/store/modules/workflow.js` - 新建 Vuex 模块
- [ ] `src/router/index.js` - 添加路由配置

### 部署步骤

#### 1. 前端构建

```bash
cd frontend
npm run build
```

#### 2. 路由配置

```javascript
// src/router/index.js 添加路由
{
  path: '/artworks/chapters/:id/studio',
  name: 'ChapterStudio',
  component: () => import('@/views/artworks/ChapterStudio.vue'),
  meta: { requiresAuth: true },
}
```

#### 3. Vuex 模块注册

```javascript
// src/store/index.js
import workflow from './modules/workflow';

export default new Vuex.Store({
  modules: {
    workflow,
    // ... 其他模块
  },
});
```

#### 4. 环境变量

```bash
# .env.production
VUE_APP_API_URL=https://api.example.com/api/v1/
VUE_APP_WS_HOST=wss://api.example.com
```

### 后端配置（无需变更）

- Story 12-4 的 API 端点已部署
- WebSocket 路由已在 Epic 3 配置
- 无需额外的数据库迁移

---

## ✅ 完成定义

Story 完成的标准：

1. **页面功能**：ChapterStudio 页面可访问，显示章节和场景信息
2. **工作流控制**：启动/暂停/继续按钮正常工作，API 调用成功
3. **进度可视化**：场景卡片正确显示状态，进度条实时更新
4. **实时通信**：WebSocket 连接正常，接收进度事件
5. **首尾帧显示**：FramePreview 组件正确显示图片或占位符
6. **错误处理**：API 错误和 WebSocket 断开有清晰的提示和降级方案
7. **路由导航**：可以跳转到 StoryboardEditor 编辑场景
8. **响应式布局**：在桌面端（1920px+）、平板端（768-1024px）正常显示
9. **测试覆盖**：39 个测试用例全部通过，覆盖率 >80%
10. **文档完整**：API 使用文档和组件使用文档完整

---

## 👥 团队署名确认

| 角色 | 代理 | 确认 | 签名 |
|------|------|-------|-------|
| Scrum Master | 🏃 Bob (SM) | ✅ | `Bob_SM_2026-02-12` |
| Architect | 🏗️ Winston (Architect) | ✅ | `Winston_ARCH_2026-02-12` |
| Developer | 💻 Amelia (Dev) | ✅ | `Amelia_DEV_2026-02-12` |
| Test Architect | 🧪 Murat (TEA) | ✅ | `Murat_TEA_2026-02-12` |
| Technical Writer | 📚 Paige (Tech Writer) | ✅ | `Paige_TW_2026-02-12` |
| UX Designer | 🎨 Sally (UX Designer) | ✅ | `Sally_UX_2026-02-12` |
| Business Analyst | 📊 Mary (Analyst) | ✅ | `Mary_ANALYST_2026-02-12` |

---

## 📝 实施完成记录

### 团队共识决策

| 决策点 | 最终选择 | 理由 |
|--------|----------|------|
| **页面结构** | 单页面 + 子组件 | 符合现有架构，便于维护 |
| **WebSocket 集成** | 专用客户端类 + 降级轮询 | KISS 原则，确保可用性 |
| **状态管理** | 新增 workflow 模块 | 与现有 Vuex 架构一致 |
| **首尾帧显示** | 水平分割预览 | 充分利用卡片空间 |

### 设计模式应用

- **单一职责 (SRP)**：每个组件只负责一个功能
- **开闭原则 (OCP)**：通过 props 和 events 扩展，不修改组件内部
- **依赖倒置 (DIP)**：通过 API 服务层与后端交互

### 质量标准

- **测试覆盖率**：>80% (39 个测试用例)
- **代码质量**：通过 ESLint 检查
- **文档完整性**：API 文档 + 组件使用文档

---

## 📚 附录

### 相关文档

- [Epic 12 总览](../epic-12.md)
- [Story 12-1.1: 章节工作流模型](./epic-12.1-story-chapter-workflow-model.md)
- [Story 12-1.2: 工作流状态机](./epic-12.2-story-workflow-state-machine.md)
- [Story 12-1.3: 场景处理器服务](./epic-12-story-12.1.3-scene-processor.md)
- [Story 12-4: 工作流控制API](./【story-12-4】开发故事文件-锁定版.md)
- [Story 12-5: 首尾帧自动提取服务](./【story-12-5】开发故事文件-锁定版.md)

### 错误码参考

| HTTP 状态 | 场景 | 错误代码 | 处理建议 |
|-----------|--------|-----------|----------|
| 400 | 已有运行中工作流 | `WORKFLOW_EXISTS` | 前端显示"工作流运行中"提示 |
| 400 | 没有场景 | `NO_SCENES` | 引导用户先添加场景 |
| 403 | 无权限 | `FORBIDDEN` | 返回登录或检查项目所有权 |
| 404 | 章节不存在 | `NOT_FOUND` | 检查章节 ID |
| 500 | 任务失败 | `TASK_FAILED` | 检查 Celery 日志 |

### WebSocket 事件格式

```javascript
// 工作流启动事件
{
  type: 'workflow_started',
  payload: {
    workflow_id: '550e8400-e29b-41d4-a716-446655440000',
    chapter_id: 1,
  }
}

// 场景开始事件
{
  type: 'scene_started',
  payload: {
    scene_id: 123,
    scene_title: '场景三',
  }
}

// 场景完成事件
{
  type: 'scene_completed',
  payload: {
    scene_id: 123,
    progress: 60,
  }
}

// 工作流完成事件
{
  type: 'workflow_completed',
  payload: {
    workflow_id: '550e8400-e29b-41d4-a716-446655440000',
    total_scenes: 5,
  }
}

// 工作流失败事件
{
  type: 'workflow_failed',
  payload: {
    workflow_id: '550e8400-e29b-41d4-a716-446655440000',
    error_message: '处理场景时发生错误',
  }
}
```

### 技术术语表

| 术语 | 定义 |
|------|------|
| **章节工作室** | 集中控制章节制作流程的前端界面 |
| **工作流** | 章节自动化制作流程的执行实例 |
| **首尾帧** | 场景的第一个和最后一个镜头，用于转场和预览 |
| **WebSocket 降级** | WebSocket 连接失败时切换到 HTTP 轮询模式 |
| **场景卡片** | 显示单个场景状态和操作的 UI 组件 |

### 后续优化建议

1. **P1**：支持批量选择场景，批量操作（重新生成、删除等）
2. **P2**：添加工作流预设配置（如处理顺序、并发数）
3. **P3**：支持场景拖拽排序，实时调整处理顺序

---

**文档版本:** v1.0 (锁定版)
**最后更新:** 2026-02-12
**状态:** READY-FOR-DEV
