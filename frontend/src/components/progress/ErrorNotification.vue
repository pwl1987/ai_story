<!-- Error Notification - 错误提示组件 -->
<template>
  <div
    v-if="visible"
    class="alert alert-error shadow-lg mb-4"
    :class="{ 'alert-outline': !closable }"
  >
    <div class="flex items-start gap-3">
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
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>

      <div class="flex-1">
        <h3 class="font-bold">{{ title }}</h3>

        <div class="text-sm mt-1">
          <div class="font-mono bg-error bg-opacity-10 p-2 rounded">
            {{ error.message }}
          </div>

          <div v-if="error.details" class="mt-2 text-xs">
            <details class="collapse">
              <summary class="cursor-pointer underline">详细信息</summary>
              <pre class="mt-2 text-xs overflow-x-auto">{{ error.details }}</pre>
            </details>
          </div>

          <div v-if="error.type" class="mt-1 text-xs text-error-content">
            类型: {{ error.type }}
          </div>
        </div>

        <div class="text-xs text-gray-400 mt-2">
          {{ formattedTime }}
        </div>
      </div>

      <!-- 关闭按钮 -->
      <button
        v-if="closable"
        class="btn btn-sm btn-ghost btn-circle"
        @click="close"
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "ErrorNotification",
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    title: {
      type: String,
      default: "错误",
    },
    error: {
      type: Object,
      default: () => ({}),
    },
    closable: {
      type: Boolean,
      default: true,
    },
    autoClose: {
      type: Boolean,
      default: false,
    },
    autoCloseDelay: {
      type: Number,
      default: 5000, // 5秒后自动关闭
    },
  },
  data() {
    return {
      timeoutId: null,
    };
  },
  computed: {
    formattedTime() {
      if (!this.error.timestamp) return "";
      const date = new Date(this.error.timestamp);
      return date.toLocaleString("zh-CN");
    },
  },
  watch: {
    visible(newVal) {
      if (newVal && this.autoClose) {
        this.startAutoClose();
      } else {
        this.stopAutoClose();
      }
    },
  },
  methods: {
    close() {
      this.$emit("close");
    },
    startAutoClose() {
      this.stopAutoClose();
      this.timeoutId = setTimeout(() => {
        this.close();
      }, this.autoCloseDelay);
    },
    stopAutoClose() {
      if (this.timeoutId) {
        clearTimeout(this.timeoutId);
        this.timeoutId = null;
      }
    },
  },
};
</script>

<style scoped>
.error-notification {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
