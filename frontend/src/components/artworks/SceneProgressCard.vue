<!--
  SceneProgressCard.vue - 场景进度卡片组件

  ① 文件核心作用：显示单个场景的状态信息，包含首尾帧预览、场景描述、镜头数量和操作按钮

  ② 本次改动内容：
     - 创建新组件文件
     - 实现 props：scene（场景数据）、isActive（是否正在处理）、showExtractFramesButton（按钮显示状态）
     - 集成 FramePreview 组件显示首尾帧
     - 根据场景状态计算显示状态（pending/processing/completed）
     - 实现两种操作按钮：提取首尾帧、编辑场景
     - 使用 daisyUI 的 card、figure、badge 组件样式
     - **P0-6 修复**：将业务逻辑判断移到父组件，子组件只负责显示（SRP 单一职责原则）

  ③ 实现功能：
     - 显示场景序号和名称
     - 水平分割显示首帧和尾帧
     - 状态覆盖层：处理中显示加载动画，完成显示绿色勾选图标，失败显示红色警告
     - 显示场景描述（限制2行）
     - 显示镜头数量和首尾帧提取状态
     - 活跃场景显示蓝色边框和"处理中"徽章
     - 按钮显示由父组件通过 prop 控制（无业务逻辑）

  使用示例：
  <SceneProgressCard
    :scene="sceneData"
    :is-active="true"
    :show-extract-frames-button="true"
    @extract-frames="handleExtractFrames"
    @edit="handleEdit"
  />
-->
<template>
  <div
    class="scene-progress-card card bg-base-100 shadow-md"
    :class="{ 'active-card': isActive }"
  >
    <figure class="px-4 pt-4">
      <!-- 首尾帧预览区域 -->
      <div class="relative aspect-video bg-base-200 rounded-lg overflow-hidden">
        <!-- 首帧 -->
        <FramePreview
          :image-url="scene.head_frame"
          :fallback-icon="'🎬'"
          label="首帧"
          class="flex-1"
        />
        <!-- 尾帧 -->
        <FramePreview
          :image-url="scene.tail_frame"
          :fallback-icon="'🎞'"
          label="尾帧"
          class="flex-1 border-l border-base-300"
        />

        <!-- 状态覆盖层 -->
        <div
          v-if="showStatusOverlay"
          class="absolute inset-0 bg-black/60 flex items-center justify-center"
        >
          <div class="text-white text-center">
            <!-- 处理中 - 加载动画 -->
            <svg
              v-if="status === 'processing'"
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 animate-spin mx-auto mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357 2m15.357 2H15"
              />
            </svg>
            <!-- 已完成 - 绿色勾选 -->
            <svg
              v-else-if="status === 'completed'"
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 mx-auto mb-2 text-green-400"
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
            <!-- 失败 - 红色警告 -->
            <svg
              v-else-if="status === 'failed'"
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 mx-auto mb-2 text-red-400"
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
            <div class="text-sm">
              {{ statusDisplay }}
            </div>
          </div>
        </div>

        <!-- 活跃指示器 -->
        <div
          v-if="isActive"
          class="absolute top-2 left-2 badge badge-primary"
        >
          处理中
        </div>
      </div>
    </figure>

    <!-- 卡片内容 -->
    <div class="card-body p-4">
      <!-- 场景标题 -->
      <h3 class="card-title text-base">
        场景 {{ scene.scene_number }}: {{ scene.scene_name }}
      </h3>

      <!-- 场景描述 -->
      <p class="text-xs text-base-content/60 line-clamp-2 mb-3">
        {{ scene.description }}
      </p>

      <!-- 场景统计 -->
      <div class="flex gap-4 text-xs text-base-content/60 mb-3">
        <span>{{ scene.shot_count || 0 }} 个镜头</span>
        <span
          v-if="scene.head_frame || scene.tail_frame"
          class="text-success"
        >已提取帧</span>
        <span
          v-else
          class="text-warning"
        >待提取帧</span>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions justify-end">
        <!-- 提取首尾帧按钮 -->
        <button
          v-if="showExtractFramesButton"
          class="btn btn-sm btn-ghost"
          @click="$emit('extract-frames', scene)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16l4.586-4.586a2 2 0 12.828 0L16 16m-2-2l1.586-1.586a2 2 0 000-1.664z"
            />
          </svg>
          提取首尾帧
        </button>

        <!-- 编辑场景按钮 -->
        <button
          class="btn btn-sm btn-primary"
          @click="$emit('edit', scene)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002 2v5m-1.414-9.414a2 2 0 000-1.664z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 3h6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002 2v5m-1.414-9.414a2 2 0 000-1.664z"
            />
          </svg>
          编辑场景
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import FramePreview from './FramePreview.vue';

/**
 * SceneProgressCard 场景进度卡片组件
 *
 * @component SceneProgressCard
 * @description 显示单个场景的状态信息，包含首尾帧预览、场景描述、镜头数量和操作按钮
 * @example
 * <SceneProgressCard
 *   :scene="sceneData"
 *   :is-active="true"
 *   :workflow-status="'running'"
 *   @extract-frames="handleExtractFrames"
 *   @edit="handleEdit"
 * />
 */

/**
 * @typedef {Object} ScriptScene
 * @property {number} id - 场景 ID
 * @property {number} scene_number - 场景编号
 * @property {string} scene_name - 场景名称
 * @property {string} description - 场景描述
 * @property {number} shot_count - 镜头数量
 * @property {string|null} head_frame - 首帧 URL
 * @property {string|null} tail_frame - 尾帧 URL
 * @property {boolean} is_completed - 是否已完成
 */

export default {
  name: 'SceneProgressCard',

  components: {
    FramePreview,
  },

  props: {
    /**
     * 场景数据对象
     * @type {ScriptScene}
     * @description 来自 ScriptScene 模型的场景数据
     * @required true
     */
    scene: {
      type: Object,
      required: true,
    },

    /**
     * 是否正在被处理
     * @type {boolean}
     * @description 当前是否为活跃场景（正在处理中）
     * @default false
     */
    isActive: {
      type: Boolean,
      default: false,
    },

    /**
     * 是否显示提取首尾帧按钮
     * @type {boolean}
     * @description 由父组件计算好的按钮显示状态（SRP：业务逻辑应在父组件）
     * @default false
     */
    showExtractFramesButton: {
      type: Boolean,
      default: false,
    },
  },

  /**
   * Events
   * @description 组件触发的自定义事件
   * @property {string} extract-frames - 提取首尾帧事件
   * @property {ScriptScene} extract-frames.payload - 场景对象
   * @property {string} edit - 编辑场景事件
   * @property {ScriptScene} edit.payload - 场景对象
   */
  emits: ['extract-frames', 'edit'],

  computed: {
    /**
     * 计算场景状态
     * - 如果 isActive 为 true → processing（处理中）
     * - 如果 scene.is_completed 为 true → completed（已完成）
     * - 其他 → pending（待处理）
     */
    status() {
      if (this.isActive) return 'processing';
      if (this.scene.is_completed) return 'completed';
      return 'pending';
    },

    /**
     * 状态显示文本
     */
    statusDisplay() {
      const displays = {
        pending: '待处理',
        processing: '处理中',
        completed: '已完成',
        failed: '失败',
      };
      return displays[this.status];
    },

    /**
     * 是否显示状态覆盖层
     */
    showStatusOverlay() {
      return ['processing', 'completed', 'failed'].includes(this.status);
    },
  },
};
</script>

<style scoped>
.scene-progress-card {
  @apply transition-all duration-200;
}

.scene-progress-card:hover {
  @apply -translate-y-1;
  @apply shadow-lg;
}

/* 活跃状态样式 - 避免循环依赖，直接使用 CSS 属性 */
.scene-progress-card.active-card {
  transform: translateY(-0.25rem);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  outline: 2px solid hsl(var(--p));
  outline-offset: 2px;
}
</style>
