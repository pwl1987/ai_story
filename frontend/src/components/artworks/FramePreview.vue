<!--
  FramePreview.vue - 首尾帧预览组件

  ① 文件核心作用：显示场景的首帧或尾帧图片，支持加载状态、错误处理和占位符fallback

  ② 本次改动内容：
     - 创建新组件文件
     - 实现 props：imageUrl（图片URL）、fallbackIcon（占位图标）、label（标签文本）
     - 实现三种状态：加载中、加载成功、加载失败
     - 使用 daisyUI 的 figure 和 image 组件样式
     - 添加完整的 JSDoc 类型注释（P0-5 修复）

  ③ 实现功能：
     - 显示首尾帧图片（来自 Story 12-5 提取服务）
     - 图片加载时显示加载动画
     - 图片加载失败时显示占位图标和错误提示
     - 支持自定义标签（"首帧"/"尾帧"）

  使用示例：
  <FramePreview
    :image-url="scene.head_frame"
    :fallback-icon="'🎬'"
    label="首帧"
  />
-->
<template>
  <figure
    class="frame-preview"
    :class="{ 'frame-preview--loading': isLoading }"
  >
    <!-- 加载状态 -->
    <div
      v-if="isLoading"
      class="aspect-video bg-base-200 flex items-center justify-center"
    >
      <span class="loading loading-spinner loading-sm" />
    </div>

    <!-- 加载成功 - 显示图片 -->
    <img
      v-else-if="imageUrl"
      :src="imageUrl"
      :alt="label"
      class="w-full h-full object-cover rounded-lg"
      @load="handleLoadSuccess"
      @error="handleLoadError"
    />

    <!-- 加载失败或无图片 - 显示占位符 -->
    <div
      v-else
      class="aspect-video bg-base-200 flex items-center justify-center rounded-lg"
    >
      <div class="text-center">
        <div class="text-4xl mb-2">
          {{ fallbackIcon || '🖼️' }}
        </div>
        <div class="text-xs text-base-content/60">
          {{ label }}
        </div>
        <div
          v-if="hasError"
          class="text-xs text-error mt-1"
        >
          加载失败
        </div>
      </div>
    </div>
  </figure>
</template>

<script>
/**
 * @typedef {Object} FramePreviewProps
 * @property {string} imageUrl - 图片 URL
 * @property {string} fallbackIcon - 占位图标（emoji）
 * @property {string} label - 标签文本
 */

/**
 * FramePreview 首尾帧预览组件
 *
 * @component FramePreview
 * @example
 * <FramePreview
 *   :image-url="'https://example.com/frame.jpg'"
 *   :fallback-icon="'🎬'"
 *   label="首帧"
 * />
 */
export default {
  name: 'FramePreview',

  props: {
    /**
     * 图片 URL
     * @type {string}
     * @description 来自 scene.head_frame 或 scene.tail_frame 的图片地址
     * @default ''
     */
    imageUrl: {
      type: String,
      default: '',
    },

    /**
     * 占位图标
     * @type {string}
     * @description 图片不存在时显示的 emoji 或图标
     * @default '🖼️'
     * @example '🎬' 或 '🎞'
     */
    fallbackIcon: {
      type: String,
      default: '🖼️',
    },

    /**
     * 标签文本
     * @type {string}
     * @description 显示在占位符下方的标签文字
     * @default '帧'
     * @example '首帧' 或 '尾帧'
     */
    label: {
      type: String,
      default: '帧',
    },
  },

  data() {
    return {
      /**
       * @type {boolean}
       * @description 图片是否正在加载
       * @default true
       */
      isLoading: true,

      /**
       * @type {boolean}
       * @description 图片加载是否失败
       * @default false
       */
      hasError: false,
    };
  },

  watch: {
    /**
     * 当 imageUrl 变化时重置加载状态
     * @param {string} newUrl - 新的图片 URL
     * @listens imageUrl
     */
    imageUrl(newUrl) {
      if (newUrl) {
        this.isLoading = true;
        this.hasError = false;
      }
    },
  },

  methods: {
    /**
     * 处理图片加载成功事件
     * @description 图片加载完成时调用，设置加载状态为 false，错误状态为 false
     * @returns {void}
     */
    handleLoadSuccess() {
      this.isLoading = false;
      this.hasError = false;
    },

    /**
     * 处理图片加载失败事件
     * @description 图片加载失败时调用，设置加载状态为 false，错误状态为 true
     * @returns {void}
     */
    handleLoadError() {
      this.isLoading = false;
      this.hasError = true;
    },
  },
};
</script>

<style scoped>
.frame-preview {
  @apply min-h-0;
  @apply overflow-hidden;
  @apply rounded-lg;
  @apply transition-all duration-200;
}

.frame-preview:hover {
  @apply transform scale-105;
}

.frame-preview--loading {
  @apply bg-base-200;
}
</style>
