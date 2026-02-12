<!--
  WorkflowEventLog.vue - 工作流事件日志组件

  ① 文件核心作用：显示工作流事件日志列表，支持时间排序和清空操作

  ② 本次改动内容：
     - 实现 props：events（事件列表）
     - 实现计算属性：sortedEvents（按时间戳排序）
     - 实现方法：eventTitle（事件标题映射）、formatTime（时间格式化）、handleClear（清空日志）
     - 使用 daisyUI 的 card、badge 组件样式
     - **P2-2 修复**：添加标准文件头注释

  ③ 实现功能：
     - 显示事件列表（最新在前）
     - 支持空状态提示
     - 事件类型图标映射
     - 时间友好显示（刚刚/X分钟前/X小时前/日期时间）
     - 场景 ID 和进度徽章显示
     - 清空日志按钮

  使用示例：
  <WorkflowEventLog
    :events="workflowEvents"
    @clear="handleClearEvents"
  />
-->
<template>
  <div class="card bg-base-100 shadow-xl">
    <div class="card-body">
      <h2 class="card-title mb-4">
        工作流事件日志
      </h2>

      <!-- 空状态 -->
      <div
        v-if="events.length === 0"
        class="text-center py-8 text-gray-500"
      >
        <p>暂无事件</p>
      </div>

      <!-- 事件列表 -->
      <div
        v-else
        class="space-y-2 max-h-96 overflow-y-auto"
      >
        <div
          v-for="event in sortedEvents"
          :key="event.id || event.timestamp"
          class="flex items-start gap-3 p-3 bg-base-200 rounded-lg"
        >
          <!-- 状态图标 -->
          <div class="flex-shrink-0 mt-1">
            <span
              v-if="event.type === 'workflow_started'"
              class="text-info"
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
            </span>
            <span
              v-else-if="event.type === 'workflow_completed'"
              class="text-success"
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
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </span>
            <span
              v-else-if="event.type === 'workflow_failed'"
              class="text-error"
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
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </span>
            <span
              v-else-if="event.type === 'scene_started'"
              class="text-primary"
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
                  d="M7 4V2m0 2v2m0-2H5m2 0h2M7 8h10M7 12h10m-7 4h7"
                />
              </svg>
            </span>
            <span
              v-else-if="event.type === 'scene_completed'"
              class="text-success"
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
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </span>
            <span
              v-else
              class="text-gray-500"
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
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </span>
          </div>

          <!-- 事件内容 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <p class="font-medium text-sm truncate">
                {{ eventTitle(event) }}
              </p>
              <span class="text-xs text-gray-500 flex-shrink-0 ml-2">{{ formatTime(event.timestamp) }}</span>
            </div>
            <p
              v-if="event.message"
              class="text-sm text-gray-600 mt-1"
            >
              {{ event.message }}
            </p>
            <div
              v-if="event.metadata"
              class="text-xs text-gray-500 mt-1"
            >
              <span
                v-if="event.metadata.scene_id"
                class="badge badge-sm badge-ghost"
              >场景 #{{ event.metadata.scene_id }}</span>
              <span
                v-if="event.metadata.progress !== undefined"
                class="badge badge-sm badge-ghost ml-1"
              >{{ event.metadata.progress }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 清空按钮 -->
      <div
        v-if="events.length > 0"
        class="card-actions justify-end mt-4"
      >
        <button
          class="btn btn-sm btn-ghost"
          @click="handleClear"
        >
          清空日志
        </button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * WorkflowEventLog 工作流事件日志组件
 *
 * @component WorkflowEventLog
 * @description 显示工作流事件日志列表，支持按时间排序和清空操作
 *
 * Events 文档:
 * @description 组件支持以下事件类型和数据格式
 * @property {string} clear - 清空日志事件，无 payload
 *
 * 事件数据结构：
 * @description events 数组中每个事件对象的格式
 * @property {number|string} id - 事件唯一标识符
 * @property {string} type - 事件类型
 * @property {string} timestamp - ISO 8601 格式的时间戳
 * @property {string} [message] - 事件消息描述
 * @property {Object} [metadata] - 事件元数据
 * @property {number} [metadata.scene_id] - 关联的场景 ID
 * @property {number} [metadata.progress] - 进度百分比 (0-100)
 *
 * @example
 * <WorkflowEventLog
 *   :events="workflowEvents"
 *   @clear="handleClearEvents"
 * />
 */

/**
 * @typedef {Object} WorkflowEvent
 * @property {string|number} id - 事件唯一标识
 * @property {string} type - 事件类型
 * @property {string} timestamp - ISO 8601 时间戳
 * @property {string} [message] - 事件消息
 * @property {Object} [metadata] - 事件元数据
 * @property {number} [metadata.scene_id] - 场景 ID
 * @property {number} [metadata.progress] - 进度百分比
 */

export default {
  name: 'WorkflowEventLog',

  props: {
    /**
     * 工作流事件列表
     * @type {WorkflowEvent[]}
     * @description 工作流事件数组，按时间戳排序后显示
     * @default []
     * @validator (value) => Array.isArray(value)
     */
    events: {
      type: Array,
      default: () => [],
      validator: (value) => {
        return Array.isArray(value);
      },
    },
  },

  /**
   * Events
   * @description 组件触发的自定义事件
   * @property {string} clear - 清空日志事件，无 payload
   */
  emits: ['clear'],

  computed: {
    /**
     * 按时间戳排序的事件列表（最新在前）
     */
    sortedEvents() {
      return [...this.events].sort((a, b) => {
        return new Date(b.timestamp) - new Date(a.timestamp);
      });
    },
  },

  methods: {
    /**
     * 获取事件标题
     */
    eventTitle(event) {
      const titles = {
        workflow_started: '工作流已启动',
        workflow_completed: '工作流已完成',
        workflow_failed: '工作流失败',
        workflow_paused: '工作流已暂停',
        workflow_resumed: '工作流已继续',
        scene_started: '场景处理开始',
        scene_completed: '场景处理完成',
        scene_failed: '场景处理失败',
        frames_extracted: '首尾帧已提取',
        error: '错误',
      };

      return titles[event.type] || event.type;
    },

    /**
     * 格式化时间戳
     */
    formatTime(timestamp) {
      if (!timestamp) return '';

      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;

      // 小于1分钟
      if (diff < 60000) {
        return '刚刚';
      }

      // 小于1小时
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
      }

      // 小于24小时
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
      }

      // 格式化为日期时间
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');

      return `${year}-${month}-${day} ${hours}:${minutes}`;
    },

    /**
     * 清空事件日志
     */
    handleClear() {
      this.$emit('clear');
    },
  },
};
</script>

<style scoped>
/* 事件日志特定样式 */
.space-y-2 > * + * {
  margin-top: 0.5rem;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>

<!--
  使用示例：

  1. 基本用法：
  <WorkflowEventLog :events="events" @clear="handleClear" />

  2. 带空状态提示：
  <WorkflowEventLog :events="[]" />
  <!-- 自动显示"暂无事件" -->

  3. 与 ChapterStudio 集成：
  <WorkflowEventLog
    :events="workflowEvents"
    v-if="showEventLog"
    @clear="clearEventLog"
    class="mt-6"
  />

  Events 数据结构：
  events: [
    {
      id: 1,
      type: 'workflow_started',
      timestamp: '2026-02-12T10:00:00Z',
      message: '工作流已启动',
      metadata: { scene_id: 1, progress: 50 }
    },
    // ... 更多事件
  ]
-->
