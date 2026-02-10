<template>
  <div v-if="visible" class="modal modal-open">
    <div class="modal-box max-w-2xl" @click.stop>
      <!-- 关闭按钮 -->
      <button
        class="btn btn-sm btn-circle btn-ghost absolute right-4 top-4"
        @click="handleClose"
      >
        ✕
      </button>

      <!-- 标题 -->
      <h3 class="font-bold text-lg mb-4">
        {{ loading ? '正在测试...' : '测试结果' }}
      </h3>

      <!-- 加载状态 -->
      <div v-if="loading" class="py-8 text-center">
        <div class="flex flex-col items-center gap-4">
          <span class="loading loading-spinner loading-lg"></span>
          <div class="text-base-content/70">
            <p>正在连接模型服务器...</p>
            <p class="text-sm mt-2">这可能需要几秒钟时间</p>
          </div>
        </div>
      </div>

      <!-- 测试结果 -->
      <div v-else class="space-y-4">
        <!-- 状态图标 -->
        <div class="flex justify-center mb-4">
          <div
            class="flex items-center justify-center w-16 h-16 rounded-full"
            :class="result?.success ? 'bg-success/10 text-success' : 'bg-error/10 text-error'"
          >
            <svg
              v-if="result?.success"
              xmlns="http://www.w3.org/2000/svg"
              class="w-8 h-8"
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
            <svg
              v-else
              xmlns="http://www.w3.org/2000/svg"
              class="w-8 h-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
        </div>

        <!-- 结果消息 -->
        <div class="text-center mb-4">
          <div
            class="text-lg font-semibold mb-2"
            :class="result?.success ? 'text-success' : 'text-error'"
          >
            {{ result?.success ? '✅ 连接测试成功' : '❌ 连接测试失败' }}
          </div>
          <div class="text-sm text-base-content/70">
            {{ result?.providerName }} - {{ result?.modelName }}
          </div>
        </div>

        <!-- 详细信息 -->
        <div v-if="result?.success" class="bg-base-200 rounded-lg p-4 space-y-3">
          <!-- 延迟 -->
          <div class="flex justify-between items-center">
            <span class="text-base-content/70">响应延迟</span>
            <span class="font-mono font-semibold">{{ result.latency_ms }} ms</span>
          </div>

          <!-- Tokens -->
          <div v-if="result.tokens_used" class="flex justify-between items-center">
            <span class="text-base-content/70">Token 使用</span>
            <span class="font-mono font-semibold">{{ result.tokens_used }}</span>
          </div>

          <!-- AI 回复 -->
          <div class="mt-4">
            <div class="text-sm text-base-content/70 mb-2">AI 回复：</div>
            <div class="bg-base-300 rounded-lg p-3 text-sm max-h-40 overflow-y-auto">
              {{ result.text || '无回复内容' }}
            </div>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-else class="bg-error/10 border border-error/20 rounded-lg p-4">
          <div class="text-sm text-error">
            <div class="font-semibold mb-1">错误详情：</div>
            <div>{{ result.error || '未知错误' }}</div>
          </div>
        </div>

        <!-- 关闭按钮 -->
        <div class="modal-action">
          <button class="btn btn-primary" @click="handleClose">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestResultModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    result: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  methods: {
    handleClose() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
/* 模态框背景遮罩 */
.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

/* 滚动条样式 */
.max-h-40::-webkit-scrollbar {
  width: 6px;
}

.max-h-40::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.max-h-40::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.max-h-40::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
