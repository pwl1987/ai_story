<!--
  WorkflowControlPanel.vue - 工作流控制面板组件

  ① 文件核心作用：章节工作流的控制中心，显示状态、进度、当前场景和控制按钮

  ② 本次改动内容：
     - 创建新组件文件
     - 实现 props：status（工作流状态）、progress（进度百分比）、currentScene（当前场景）、totalScenes（总场景数）、completedScenes（已完成数）、isLoading（加载中）
     - 实现操作按钮：启动、暂停、继续、重新启动
     - 根据状态动态显示不同按钮和徽章样式
     - 集成 daisyUI 的 card、progress、badge 组件

  ③ 实现功能：
     - 显示工作流状态徽章（待处理/运行中/已暂停/已完成/失败）
     - 显示进度条（0-100%）和进度百分比文字
     - 显示当前正在处理的场景信息
     - 显示已完成场景数统计
     - 根据状态显示对应操作按钮：
       * 待处理/已完成/失败 → 显示"启动"按钮
       * 运行中 → 显示"暂停"按钮
       * 已暂停 → 显示"继续"按钮
     - 加载中状态禁用所有按钮
-->
<template>
  <div class="workflow-control-panel card bg-base-100 shadow-xl">
    <div class="card-body">
      <!-- 状态行 -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div
            class="badge"
            :class="statusBadgeClass"
          >
            {{ statusDisplay }}
          </div>
          <h2 class="card-title">
            章节工作流控制
          </h2>
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
        />
        <div class="text-xs text-center mt-1">
          {{ progress }}%
        </div>
      </div>

      <!-- 当前场景 -->
      <div
        v-if="currentScene"
        class="mb-4"
      >
        <div class="text-sm text-base-content/60 mb-1">
          当前处理:
        </div>
        <div class="font-medium">
          {{ currentScene.title || `场景 ${currentScene.id}` }}
        </div>
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
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          启动工作流
        </button>

        <button
          v-if="canPause"
          class="btn btn-warning"
          :disabled="isLoading"
          @click="$emit('pause')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          暂停
        </button>

        <button
          v-if="canResume"
          class="btn btn-success"
          :disabled="isLoading"
          @click="$emit('resume')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
          </svg>
          继续
        </button>

        <button
          v-if="canRetry"
          class="btn btn-error"
          :disabled="isLoading"
          @click="$emit('retry')"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          重新启动
        </button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * WorkflowControlPanel 工作流控制面板组件
 *
 * @component WorkflowControlPanel
 * @description 章节工作流的控制中心，显示状态、进度、当前场景和控制按钮
 * @example
 * <WorkflowControlPanel
 *   :status="'running'"
 *   :progress="50"
 *   :current-scene="{ id: 1, title: '场景1' }"
 *   :total-scenes="10"
 *   :completed-scenes="5"
 *   :is-loading="false"
 *   @start="handleStart"
 *   @pause="handlePause"
 * />
 */

/**
 * @typedef {Object} WorkflowStatus
 * @property {string} idle - 待处理
 * @property {string} running - 运行中
 * @property {string} paused - 已暂停
 * @property {string} completed - 已完成
 * @property {string} failed - 失败
 */

/**
 * @typedef {Object} CurrentScene
 * @property {number} id - 场景 ID
 * @property {string} title - 场景标题
 */

export default {
  name: 'WorkflowControlPanel',

  props: {
    /**
     * 工作流状态
     * @type {WorkflowStatus}
     * @description 当前工作流的运行状态
     * @default 'idle'
     * @validator (value) => ['idle', 'running', 'paused', 'completed', 'failed'].includes(value)
     */
    status: {
      type: String,
      default: 'idle',
      validator: (value) => ['idle', 'running', 'paused', 'completed', 'failed'].includes(value),
    },

    /**
     * 进度百分比
     * @type {number}
     * @description 工作流整体进度（0-100）
     * @default 0
     * @min 0
     * @max 100
     */
    progress: {
      type: Number,
      default: 0,
    },

    /**
     * 当前正在处理的场景对象
     * @type {CurrentScene|null}
     * @description 当前正在处理的场景信息，null 表示无活跃场景
     * @default null
     */
    currentScene: {
      type: Object,
      default: null,
    },

    /**
     * 总场景数
     * @type {number}
     * @description 章节包含的总场景数量
     * @required true
     */
    totalScenes: {
      type: Number,
      required: true,
    },

    /**
     * 已完成场景数
     * @type {number}
     * @description 已处理完成的场景数量
     * @default 0
     */
    completedScenes: {
      type: Number,
      default: 0,
    },

    /**
     * 是否正在加载
     * @type {boolean}
     * @description 按钮禁用状态，true 时禁用所有操作按钮
     * @default false
     */
    isLoading: {
      type: Boolean,
      default: false,
    },
  },

  /**
   * Events
   * @description 组件触发的自定义事件
   * @property {string} start - 启动工作流事件，无 payload
   * @property {string} pause - 暂停工作流事件，无 payload
   * @property {string} resume - 继续工作流事件，无 payload
   * @property {string} retry - 重新启动工作流事件，无 payload
   */
  emits: ['start', 'pause', 'resume', 'retry'],

  computed: {
    /**
     * 状态显示文本映射
     */
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

    /**
     * 状态徽章样式类映射
     */
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

    /**
     * 是否可以启动工作流（待处理、已完成、失败状态）
     */
    canStart() {
      return ['idle', 'completed', 'failed'].includes(this.status);
    },

    /**
     * 是否可以暂停工作流（仅运行中状态）
     */
    canPause() {
      return this.status === 'running';
    },

    /**
     * 是否可以继续工作流（仅已暂停状态）
     */
    canResume() {
      return this.status === 'paused';
    },

    /**
     * 是否可以重试（仅失败状态）
     */
    canRetry() {
      return this.status === 'failed';
    },

    /**
     * 计算已完成场景数，默认为0
     */
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
