# Story 12-3.1: 实现章节工作室主页面

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P1
> **预估工作量:** 2天
> **依赖:** 12-1.1, 12-1.2, 12-1.3, 12-1.4

---

## 📋 需求描述

**用户故事：** 作为内容创作者，我需要一个可视化的章节工作室界面，能够启动和监控章节工作流的执行进度。

**功能说明：**
- 创建章节工作室主页面
- 显示章节工作流状态和进度
- 提供工作流控制按钮（启动/暂停/继续）
- 显示场景处理进度卡片
- 实时进度更新（WebSocket）

**边界条件：**
- 不包含工作流后端逻辑
- 不包含视频导出功能（Epic 13）
- 只包含 UI 组件

**验收标准：**
- [ ] 主页面可访问
- [ ] 工作流状态实时更新
- [ ] 场景进度卡片正确显示
- [ ] WebSocket 连接正常

---

## 🔧 技术实现细节

### Vuex Store 模块

```javascript
// frontend/src/store/modules/chapterWorkflow.js

import api from '@/services/chapterWorkflowService'

const state = {
  currentWorkflow: null,
  workflowEvents: [],
  scenesProgress: [],
  isConnecting: false,
  error: null
}

const getters = {
  workflowProgress: (state) => {
    if (!state.currentWorkflow) return 0
    return state.currentWorkflow.progress_percentage || 0
  },
  isActive: (state) => {
    if (!state.currentWorkflow) return false
    return ['running', 'paused'].includes(state.currentWorkflow.status)
  },
  completedScenes: (state) => {
    return state.scenesProgress.filter(s => s.status === 'completed').length
  }
}

const mutations = {
  SET_WORKFLOW(state, workflow) {
    state.currentWorkflow = workflow
  },
  SET_WORKFLOW_EVENTS(state, events) {
    state.workflowEvents = events
  },
  SET_SCENES_PROGRESS(state, scenes) {
    state.scenesProgress = scenes
  },
  UPDATE_SCENE_PROGRESS(state, { sceneId, progress }) {
    const scene = state.scenesProgress.find(s => s.id === sceneId)
    if (scene) {
      scene.progress = progress
    }
  },
  SET_ERROR(state, error) {
    state.error = error
  },
  SET_CONNECTING(state, isConnecting) {
    state.isConnecting = isConnecting
  }
}

const actions = {
  async startWorkflow({ commit }, chapterId) {
    try {
      const workflow = await api.startWorkflow(chapterId)
      commit('SET_WORKFLOW', workflow)

      // 启动 WebSocket 监听
      dispatch('connectWebSocket', workflow.workflow_id)
    } catch (error) {
      commit('SET_ERROR', error.message)
      throw error
    }
  },

  async pauseWorkflow({ commit }, workflowId) {
    try {
      await api.pauseWorkflow(workflowId)
      if (state.currentWorkflow) {
        state.currentWorkflow.status = 'paused'
      }
    } catch (error) {
      commit('SET_ERROR', error.message)
      throw error
    }
  },

  async resumeWorkflow({ commit }, workflowId) {
    try {
      await api.resumeWorkflow(workflowId)
      if (state.currentWorkflow) {
        state.currentWorkflow.status = 'running'
      }
    } catch (error) {
      commit('SET_ERROR', error.message)
      throw error
    }
  },

  async fetchWorkflowStatus({ commit }, chapterId) {
    try {
      const workflow = await api.getWorkflowStatus(chapterId)
      commit('SET_WORKFLOW', workflow)
    } catch (error) {
      commit('SET_ERROR', error.message)
      throw error
    }
  },

  connectWebSocket({ commit, dispatch }, workflowId) {
    commit('SET_CONNECTING', true)

    const ws = new WebSocket(
      `${process.env.VUE_APP_WS_URL}/ws/workflows/${workflowId}/`
    )

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'scene_progress':
          commit('UPDATE_SCENE_PROGRESS', {
            sceneId: data.scene_id,
            progress: data.progress
          })
          break
        case 'scene_completed':
          dispatch('fetchWorkflowStatus', chapterId)
          break
        case 'workflow_failed':
          commit('SET_ERROR', data.message)
          break
      }
    }

    ws.onerror = (error) => {
      commit('SET_ERROR', 'WebSocket 连接失败')
      commit('SET_CONNECTING', false)
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
```

### API 服务

```javascript
// frontend/src/services/chapterWorkflowService.js

import client from './apiClient'

export default {
  async startWorkflow(chapterId) {
    const response = await client.post(
      `/artworks/chapters/${chapterId}/start-workflow/`
    )
    return response.data
  },

  async pauseWorkflow(chapterId) {
    const response = await client.post(
      `/artworks/chapters/${chapterId}/pause-workflow/`
    )
    return response.data
  },

  async resumeWorkflow(chapterId) {
    const response = await client.post(
      `/artworks/chapters/${chapterId}/resume-workflow/`
    )
    return response.data
  },

  async getWorkflowStatus(chapterId) {
    const response = await client.get(
      `/artworks/chapters/${chapterId}/workflow-status/`
    )
    return response.data
  }
}
```

### 主页面组件

```vue
<!-- frontend/src/views/artworks/ChapterStudio.vue -->
<template>
  <div class="chapter-studio min-h-screen bg-base-200">
    <!-- 顶部导航 -->
    <div class="navbar bg-base-100 shadow-md">
      <div class="flex items-center justify-between px-6 py-4">
        <div>
          <h1 class="text-xl font-bold">📖 章节工作室</h1>
          <p class="text-sm text-gray-500">{{ chapter.title }}</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="goBack"
            class="btn btn-outline btn-sm"
          >
            返回
          </button>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="flex h-[calc(100vh-64px)]">
      <!-- 左侧：工作流控制面板 -->
      <WorkflowControlPanel
        :workflow="currentWorkflow"
        :chapter="chapter"
        @start="handleStart"
        @pause="handlePause"
        @resume="handleResume"
      />

      <!-- 中间：场景进度卡片列表 -->
      <div class="flex-1 overflow-y-auto p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SceneProgressCard
            v-for="scene in scenes"
            :key="scene.id"
            :scene="scene"
            :progress="getSceneProgress(scene.id)"
          />
        </div>

        <!-- 空状态 -->
        <div
          v-if="!scenes.length"
          class="text-center text-gray-400 mt-20"
        >
          <p>暂无场景</p>
        </div>
      </div>

      <!-- 右侧：事件日志 -->
      <div class="w-80 bg-base-100 p-4 overflow-y-auto">
        <h3 class="font-bold mb-4">📋 事件日志</h3>
        <div class="space-y-2">
          <div
            v-for="event in workflowEvents"
            :key="event.id"
            class="text-sm p-2 bg-base-200 rounded"
          >
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ getEventIcon(event.type) }}</span>
              <div>
                <p class="font-medium">{{ event.message }}</p>
                <p class="text-xs text-gray-500">{{ formatTime(event.timestamp) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import WorkflowControlPanel from '@/components/artworks/WorkflowControlPanel.vue'
import SceneProgressCard from '@/components/artworks/SceneProgressCard.vue'

export default {
  name: 'ChapterStudio',

  components: {
    WorkflowControlPanel,
    SceneProgressCard
  },

  data() {
    return {
      chapter: null,
      scenes: [],
      loading: false
    }
  },

  computed: {
    ...mapState('chapterWorkflow', [
      'currentWorkflow',
      'workflowEvents',
      'workflowProgress',
      'isActive',
      'error'
    ])
  },

  async mounted() {
    const chapterId = this.$route.params.id
    await this.loadChapter(chapterId)
    await this.fetchWorkflowStatus(chapterId)
  },

  methods: {
    ...mapActions('chapterWorkflow', [
      'startWorkflow',
      'pauseWorkflow',
      'resumeWorkflow',
      'fetchWorkflowStatus'
    ]),

    async loadChapter(chapterId) {
      this.loading = true
      try {
        const response = await this.$http.get(`/artworks/chapters/${chapterId}/`)
        this.chapter = response.data
        this.scenes = response.data.scenes || []
      } finally {
        this.loading = false
      }
    },

    handleStart() {
      this.startWorkflow(this.chapter.id)
    },

    handlePause() {
      if (this.currentWorkflow) {
        this.pauseWorkflow(this.currentWorkflow.workflow_id)
      }
    },

    handleResume() {
      if (this.currentWorkflow) {
        this.resumeWorkflow(this.currentWorkflow.workflow_id)
      }
    },

    getSceneProgress(sceneId) {
      const event = this.workflowEvents.find(
        e => e.scene_id === sceneId && e.type === 'scene_progress'
      )
      return event ? event.progress : 0
    },

    getEventIcon(eventType) {
      const icons = {
        'workflow_started': '🚀',
        'workflow_completed': '✅',
        'scene_started': '🎬',
        'scene_completed': '✨',
        'scene_failed': '❌'
      }
      return icons[eventType] || '📌'
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },

    goBack() {
      this.$router.go(-1)
    }
  }
}
</script>
```

### 工作流控制面板组件

```vue
<!-- frontend/src/components/artworks/WorkflowControlPanel.vue -->
<template>
  <div class="workflow-control-panel bg-base-100 p-4 rounded-lg shadow-md">
    <h2 class="text-lg font-bold mb-4">🎛️ 工作流控制</h2>

    <!-- 状态指示器 -->
    <div class="mb-4">
      <div class="flex items-center gap-3">
        <span class="text-sm text-gray-600">当前状态：</span>
        <span
          :class="[
            'badge',
            status === 'running' ? 'badge-success' : '',
            status === 'paused' ? 'badge-warning' : '',
            status === 'completed' ? 'badge-info' : '',
            status === 'failed' ? 'badge-error' : ''
          ]"
        >
          {{ statusDisplay }}
        </span>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="mb-4">
      <div class="flex justify-between text-sm mb-1">
        <span>总进度</span>
        <span>{{ progress }}%</span>
      </div>
      <progress
        class="progress progress-primary"
        :value="progress"
        max="100"
      ></progress>
    </div>

    <!-- 场景统计 -->
    <div class="mb-4 grid grid-cols-2 gap-4 text-center">
      <div class="bg-base-200 p-2 rounded">
        <p class="text-2xl font-bold">{{ completedScenes }}</p>
        <p class="text-xs text-gray-600">已完成场景</p>
      </div>
      <div class="bg-base-200 p-2 rounded">
        <p class="text-2xl font-bold">{{ totalScenes }}</p>
        <p class="text-xs text-gray-600">总场景数</p>
      </div>
    </div>

    <!-- 控制按钮 -->
    <div class="flex gap-2">
      <button
        v-if="!workflow || status === 'pending'"
        @click="$emit('start')"
        class="btn btn-primary flex-1"
        :disabled="loading"
      >
        <span v-if="loading" class="loading loading-spinner"></span>
        <span v-else>▶️ 启动工作流</span>
      </button>

      <button
        v-if="status === 'running'"
        @click="$emit('pause')"
        class="btn btn-warning flex-1"
      >
        ⏸️ 暂停
      </button>

      <button
        v-if="status === 'paused'"
        @click="$emit('resume')"
        class="btn btn-success flex-1"
      >
        ▶️ 继续
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkflowControlPanel',

  props: {
    workflow: {
      type: Object,
      default: null
    },
    chapter: {
      type: Object,
      required: true
    }
  },

  computed: {
    status() {
      return this.workflow?.status || 'pending'
    },

    statusDisplay() {
      const displays = {
        'pending': '待处理',
        'running': '运行中',
        'paused': '已暂停',
        'completed': '已完成',
        'failed': '失败'
      }
      return displays[this.status] || '未知'
    },

    progress() {
      return this.workflow?.progress_percentage || 0
    },

    totalScenes() {
      return this.workflow?.total_scenes || 0
    },

    completedScenes() {
      return this.workflow?.completed_scenes || 0
    },

    loading() {
      return false
    }
  }
}
</script>
```

### 场景进度卡片组件

```vue
<!-- frontend/src/components/artworks/SceneProgressCard.vue -->
<template>
  <div class="scene-progress-card bg-base-100 rounded-lg shadow-md overflow-hidden">
    <!-- 场景标题 -->
    <div class="bg-base-200 px-4 py-2">
      <h3 class="font-bold">{{ scene.title }}</h3>
      <p class="text-xs text-gray-600">场景 #{{ scene.sequence_order }}</p>
    </div>

    <!-- 进度区域 -->
    <div class="p-4">
      <div class="flex items-center gap-4 mb-3">
        <!-- 状态图标 -->
        <span class="text-4xl">{{ statusIcon }}</span>

        <!-- 进度条 -->
        <div class="flex-1">
          <div class="flex justify-between text-sm mb-1">
            <span>{{ statusDisplay }}</span>
            <span>{{ progress }}%</span>
          </div>
          <progress
            class="progress progress-primary"
            :value="progress"
            max="100"
          ></progress>
        </div>
      </div>

      <!-- Shot 列表 -->
      <div class="space-y-2">
        <div
          v-for="shot in shots"
          :key="shot.id"
          class="flex items-center gap-2 text-sm bg-base-200 p-2 rounded"
        >
          <span class="w-8 h-8 bg-primary rounded flex items-center justify-center">
            📷
          </span>
          <div class="flex-1">
            <p class="font-medium">Shot #{{ shot.sequence_order }}</p>
            <p class="text-xs text-gray-600">
              {{ shot.is_generated ? '已生成' : '待生成' }}
            </p>
          </div>
          <span v-if="shot.is_generated" class="text-success">✅</span>
          <span v-else class="text-warning">⏳</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SceneProgressCard',

  props: {
    scene: {
      type: Object,
      required: true
    },
    progress: {
      type: Number,
      default: 0
    }
  },

  computed: {
    shots() {
      return this.scene.shots || []
    },

    statusIcon() {
      if (this.progress >= 100) return '✅'
      if (this.progress > 0) return '⚙️'
      return '⏸️'
    },

    statusDisplay() {
      if (this.progress >= 100) return '已完成'
      if (this.progress > 0) return '处理中'
      return '待处理'
    }
  }
}
</script>
```

---

## 📊 依赖关系

**前置 Story:** 12-1.1, 12-1.2, 12-1.3, 12-1.4
**阻塞 Story:** 无

---

## 🎯 成功标准

- [ ] 主页面可正常访问
- [ ] 工作流状态实时更新
- [ ] WebSocket 连接稳定
- [ ] 组件样式符合 daisyUI 规范
