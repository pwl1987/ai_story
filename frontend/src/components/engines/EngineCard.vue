<!-- Engine Card - 引擎状态卡片组件 -->
<template>
  <div class="card bg-base-100 shadow-xl">
    <!-- 卡片头部 -->
    <div class="card-body">
      <div class="flex justify-between items-start mb-4">
        <div class="flex items-center gap-3">
          <!-- 引擎图标 -->
          <div class="avatar placeholder" :class="engineIconClass">
            <span>{{ engineIcon }}</span>
          </div>
          <div>
            <h2 class="card-title">{{ engineName }}</h2>
            <p class="text-sm text-gray-500">{{ engineDescription }}</p>
          </div>
        </div>

        <!-- 状态徽章 -->
        <div class="badge" :class="statusBadgeClass">
          {{ statusText }}
        </div>
      </div>

      <!-- 当前提供商 -->
      <div class="space-y-2">
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-500">主引擎</span>
          <span class="font-medium">{{ engine.primary_provider }}</span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-500">备份引擎</span>
          <span class="font-medium">
            {{ engine.fallback_provider || "未配置" }}
          </span>
        </div>
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-500">当前使用</span>
          <span class="font-medium badge badge-ghost">
            {{ engine.current_provider || engine.primary_provider }}
          </span>
        </div>
      </div>

      <!-- 统计数据 -->
      <div class="stats stats-vertical mt-4 bg-base-200 rounded-lg p-3">
        <div class="stat">
          <div class="stat-title">请求数</div>
          <div class="stat-value text-lg">{{ engine.total_requests || 0 }}</div>
        </div>
        <div class="stat">
          <div class="stat-title">成功率</div>
          <div class="stat-value text-lg">
            {{ successRate }}%
          </div>
        </div>
        <div class="stat">
          <div class="stat-title">平均响应</div>
          <div class="stat-value text-lg">
            {{ formatResponseTime(engine.avg_response_time) }}
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions justify-end mt-4">
        <button
          class="btn btn-outline btn-sm"
          @click="handleTestConnection"
          :disabled="testing"
        >
          <svg
            v-if="testing"
            class="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span v-else>测试连接</span>
        </button>

        <button class="btn btn-ghost btn-sm" @click="handleResetStats">
          重置统计
        </button>

        <div class="dropdown dropdown-end">
          <label tabindex="0" class="btn btn-ghost btn-sm">
            切换引擎
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
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </label>
          <ul
            tabindex="0"
            class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52"
          >
            <li>
              <a @click="handleSwitchProvider(engine.primary_provider)">
                主引擎 ({{ engine.primary_provider }})
              </a>
            </li>
            <li v-if="engine.fallback_provider">
              <a @click="handleSwitchProvider(engine.fallback_provider)">
                备份引擎 ({{ engine.fallback_provider }})
              </a>
            </li>
          </ul>
        </div>

        <button class="btn btn-primary btn-sm" @click="handleViewDetails">
          详情
        </button>
      </div>

      <!-- Fallback 配置信息 -->
      <div v-if="engine.auto_fallback" class="mt-3 pt-3 border-t border-base-300">
        <div class="flex justify-between items-center text-sm">
          <span class="text-gray-500">自动切换</span>
          <span class="badge badge-success">已启用</span>
        </div>
        <div class="flex justify-between items-center text-sm mt-1">
          <span class="text-gray-500">失败阈值</span>
          <span>{{ engine.fallback_threshold }} 次</span>
        </div>
        <div class="flex justify-between items-center text-sm">
          <span class="text-gray-500">超时</span>
          <span>{{ engine.fallback_timeout }} 秒</span>
        </div>
        <div class="flex justify-between items-center text-sm">
          <span class="text-gray-500">当前失败</span>
          <span
            class="font-medium"
            :class="{
              'text-error': engine.failure_count >= engine.fallback_threshold,
            }"
          >
            {{ engine.failure_count }} 次
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "EngineCard",
  props: {
    engine: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      testing: false,
    };
  },
  computed: {
    engineName() {
      const names = {
        llm: "LLM 文本生成",
        image: "图像生成",
        tts: "语音合成",
      };
      return names[this.engine.engine_type] || this.engine.name;
    },
    engineDescription() {
      const descriptions = {
        llm: "文本生成与对话引擎",
        image: "AI 图像生成引擎",
        tts: "文本转语音引擎",
      };
      return descriptions[this.engine.engine_type] || this.engine.description || "";
    },
    engineIcon() {
      const icons = {
        llm: "📝",
        image: "🎨",
        tts: "🔊",
      };
      return icons[this.engine.engine_type] || "⚙️";
    },
    engineIconClass() {
      const classes = {
        llm: "bg-info text-info-content",
        image: "bg-warning text-warning-content",
        tts: "bg-success text-success-content",
      };
      return classes[this.engine.engine_type] || "bg-neutral text-neutral-content";
    },
    statusText() {
      const status = this.engine.health_status || "unknown";
      const texts = {
        online: "在线",
        offline: "离线",
        error: "异常",
        unknown: "未知",
      };
      return texts[status] || status;
    },
    statusBadgeClass() {
      const status = this.engine.health_status || "unknown";
      const classes = {
        online: "badge-success",
        offline: "badge-error",
        error: "badge-warning",
        unknown: "badge-ghost",
      };
      return classes[status] || "badge-ghost";
    },
    successRate() {
      if (!this.engine.total_requests || this.engine.total_requests === 0) {
        return 0;
      }
      return this.engine.success_rate?.toFixed(1) || "0.0";
    },
  },
  methods: {
    async handleTestConnection() {
      this.testing = true;
      try {
        await this.$emit("test-connection", this.engine.engine_type);
      } finally {
        this.testing = false;
      }
    },
    handleResetStats() {
      this.$emit("reset-stats", this.engine.engine_type);
    },
    handleSwitchProvider(provider) {
      this.$emit("switch-provider", {
        engineType: this.engine.engine_type,
        provider,
      });
    },
    handleViewDetails() {
      this.$emit("view-details", this.engine.engine_type);
    },
    formatResponseTime(ms) {
      if (!ms) return "-";
      if (ms < 1000) {
        return `${Math.round(ms)}ms`;
      }
      return `${(ms / 1000).toFixed(1)}s`;
    },
  },
};
</script>

<style scoped>
.stats {
  padding: 0.75rem;
}

.stat {
  padding: 0.25rem 0;
}

.stat-title {
  font-size: 0.75rem;
  color: #6b7280;
}

.stat-value {
  font-weight: 600;
  font-size: 1.125rem;
  line-height: 1.75rem;
}
</style>
