<!--
  ErrorBoundary.vue - 错误边界组件

  ① 文件核心作用：捕获子组件中的错误，显示友好的错误提示和降级 UI

  ② 本次改动内容：
     - 创建新组件文件
     - 实现 error 插槽捕获子组件错误
     - 支持自定义错误 UI
     - 支持重试机制
     - 使用 daisyUI 的 alert 组件

  ③ 实现功能：
     - 捕获子组件抛出的错误
     - 显示错误消息堆栈（开发模式）
     - 提供重试按钮
     - 提供"返回"或"刷新"操作
     - 生产环境隐藏技术细节

  使用示例：
  <ErrorBoundary
    @retry="loadData"
    @dismiss="handleDismiss"
  >
    <ChapterStudio :chapter-id="chapterId" />
  </ErrorBoundary>

  Events:
   - @error: 错误发生时触发，传递 Error 对象
   - @retry: 用户点击重试按钮
   - @dismiss: 用户点击忽略或关闭错误提示
-->
<template>
  <div class="error-boundary">
    <!-- 正常渲染子组件 -->
    <div v-if="!hasError">
      <slot />
    </div>

    <!-- 错误状态 -->
    <div
      v-else
      class="alert alert-error shadow-lg"
      role="alert"
    >
      <!-- 错误图标 -->
      <div class="flex items-start gap-4">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6 flex-shrink-0 mt-0.5"
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

        <!-- 错误内容 -->
        <div class="flex-1">
          <h3 class="font-bold text-lg mb-1">
            {{ errorTitle }}
          </h3>

          <p class="text-sm mb-4">
            {{ errorMessage }}
          </p>

          <!-- 错误详情（仅开发模式） -->
          <div
            v-if="isDevelopment && errorDetails"
            class="bg-error/10 rounded p-2 mb-4 text-xs font-mono"
          >
            <div class="font-semibold mb-1">错误详情：</div>
            <pre class="whitespace-pre-wrap break-all">{{ errorDetails }}</pre>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-2">
            <!-- 重试按钮 -->
            <button
              v-if="canRetry"
              class="btn btn-sm btn-primary"
              @click="handleRetry"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-1.664z"
                />
              </svg>
              重试
            </button>

            <!-- 忽略/关闭按钮 -->
            <button
              v-if="canDismiss"
              class="btn btn-sm btn-ghost"
              @click="handleDismiss"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-4 w-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12m-2-2l10-10 10 10m0 0l0 0"
                />
              </svg>
              {{ dismissText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * ErrorBoundary 错误边界组件
 *
 * @component ErrorBoundary
 * @description 捕获子组件错误并提供友好的错误 UI，支持重试和降级方案
 */

/**
 * @typedef {Object} ErrorInfo
 * @property {string} message - 错误消息
 * @property {string} [title] - 错误标题
 * @property {string} [details] - 错误详情堆栈
 * @property {Error} [originalError] - 原始 Error 对象
 * @property {boolean} [canRetry] - 是否允许重试
 * @property {boolean} [canDismiss] - 是否允许忽略
 * @property {string} [dismissText] - 忽略按钮文本
 */

export default {
  name: 'ErrorBoundary',

  props: {
    /**
     * 是否允许重试
     * @type {boolean}
     * @description 是否显示重试按钮
     * @default true
     */
    canRetry: {
      type: Boolean,
      default: true,
    },

    /**
     * 是否允许关闭
     * @type {boolean}
     * @description 是否允许关闭/忽略错误
     * @default true
     */
    canDismiss: {
      type: Boolean,
      default: true,
    },

    /**
     * 忽略按钮文本
     * @type {string}
     * @description 关闭/忽略按钮的文本
     * @default '关闭'
     */
    dismissText: {
      type: String,
      default: '关闭',
    },

    /**
     * 自定义错误标题
     * @type {string}
     * @description 自定义错误标题，null 时使用默认值
     * @default null
     */
    customTitle: {
      type: String,
      default: null,
    },

    /**
     * 自定义错误消息
     * @type {string}
     * @description 自定义错误消息，null 时使用 error.message
     * @default null
     */
    customMessage: {
      type: String,
      default: null,
    },

    /**
     * 是否显示技术详情
     * @type {boolean}
     * @description 是否显示错误堆栈等详情信息（开发模式）
     * @default false
     */
    showDetails: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      /**
       * @type {Error|null}
       * @description 当前捕获的错误对象
       */
      error: null,

      /**
       * @type {string}
       * @description 错误消息
       */
      errorMessage: '',

      /**
       * @type {string}
       * @description 错误详情
       */
      errorDetails: '',

      /**
       * @type {Error|null}
       * @description 导致错误崩溃的组件
       */
      errorComponent: null,

      /**
       * @type {string}
       * @description 错误发生的生命周期钩子
       */
      errorHook: '',
    };
  },

  computed: {
    /**
     * 是否为开发环境
     * @type {boolean}
     * @description 用于判断是否显示错误详情
     */
    isDevelopment() {
      return process.env.NODE_ENV === 'development';
    },

    /**
     * 错误标题
     * @type {string}
     * @description 显示的错误标题，优先使用自定义值
     */
    errorTitle() {
      if (this.customTitle) return this.customTitle;
      if (this.error?.title) return this.error.title;
      return '操作失败';
    },
  },

  methods: {
    /**
     * Vue 错误处理器
     * @param {Error} err - 错误对象
     * @param {Vue} vm - 发生错误的组件实例
     * @param {string} info - 错误类型（render/method等）
     */
    errorHandler(err, vm, info) {
      // 防止重复处理
      if (this.hasError) return;

      console.error('[ErrorBoundary] Captured error:', err, vm, info);

      this.error = err;
      this.errorMessage = this.customMessage || err?.message || '未知错误';
      this.errorDetails = this.formatErrorDetails(err, vm, info);
      this.errorComponent = vm;
      this.errorHook = info;

      // 触发 error 事件
      this.$emit('error', {
        message: this.errorMessage,
        title: this.errorTitle,
        details: this.errorDetails,
        originalError: err,
        component: vm?.$options.name || 'Unknown',
        hook: info,
      });
    },

    /**
     * 格式化错误详情
     * @param {Error} err - 错误对象
     * @param {Vue} vm - 发生错误的组件实例
     * @param {string} info - 错误类型
     * @returns {string} 格式化的错误详情
     */
    formatErrorDetails(err, vm, info) {
      const parts = [];

      if (err?.message) {
        parts.push(`消息: ${err.message}`);
      }

      if (vm?.$options.name) {
        parts.push(`组件: ${vm.$options.name}`);
      }

      if (info) {
        parts.push(`钩子: ${info}`);
      }

      if (err?.stack) {
        parts.push('--- 堆栈 ---');
        parts.push(err.stack);
      }

      return parts.join('\n');
    },

    /**
     * 处理重试操作
     * @description 触发 retry 事件并重置错误状态
     */
    handleRetry() {
      this.$emit('retry', this.error);
      this.resetError();
    },

    /**
     * 处理关闭/忽略操作
     * @description 触发 dismiss 事件并重置错误状态
     */
    handleDismiss() {
      this.$emit('dismiss');
      this.resetError();
    },

    /**
     * 重置错误状态
     * @description 清除错误并允许重新渲染子组件
     */
    resetError() {
      this.error = null;
      this.errorMessage = '';
      this.errorDetails = '';
      this.errorComponent = null;
      this.errorHook = '';
    },
  },

  /**
   * 错误捕获钩子
   * @description Vue 全局错误处理器
   */
  errorCaptured(err, vm, info) {
    this.errorHandler(err, vm, info);

    // 返回 false 阻止默认的错误传播
    return false;
  },

  /**
   * Vue 渲染函数
   * @param {CreateElement} h - 创建元素函数
   * @returns {VNode} 渲染的虚拟 DOM
   */
  render(h) {
    return h('div', { onError: this.errorCaptured }, [
      // 渲染默认插槽（子组件）
      this.$slots.default ? h('div', { class: 'error-boundary-content' }, this.$slots.default) : null,

      // 错误状态插槽（可选自定义错误 UI）
      this.$scopedSlots.fallback ? this.$scopedSlots.fallback({
        error: this.error,
        errorMessage: this.errorMessage,
        errorDetails: this.errorDetails,
        errorComponent: this.errorComponent,
        errorHook: this.errorHook,
        title: this.errorTitle,
        canRetry: this.canRetry,
        canDismiss: this.canDismiss,
        dismissText: this.dismissText,
        handleRetry: this.handleRetry,
        handleDismiss: this.handleDismiss,
      }) : null,
    ]);
  },
};
</script>

<style scoped>
.error-boundary {
  @apply relative;
}

.error-boundary-content {
  @apply transition-opacity duration-300;
}
</style>
