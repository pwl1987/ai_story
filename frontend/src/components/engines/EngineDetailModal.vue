<!-- Engine Detail Modal - 引擎详情模态框 -->
<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-4xl" @click.self="$emit('close')">
      <!-- 标题栏 -->
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-bold">{{ engineName }}</h2>
        <button class="btn btn-sm btn-circle btn-ghost" @click="$emit('close')">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
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

      <div v-if="engine" class="space-y-6">
        <!-- 健康状态 -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h3 class="card-title text-base mb-4">健康状态</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <div class="text-sm text-gray-500">状态</div>
                <div class="badge mt-1" :class="statusBadgeClass">
                  {{ statusText }}
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">最后检查</div>
                <div class="mt-1">{{ formatDate(engine.last_health_check) }}</div>
              </div>
              <div>
                <div class="text-sm text-gray-500">响应时间</div>
                <div class="mt-1">{{ formatResponseTime(engine.avg_response_time) }}</div>
              </div>
              <div>
                <div class="text-sm text-gray-500">当前提供商</div>
                <div class="mt-1 font-medium">
                  {{ engine.current_provider || engine.primary_provider }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h3 class="card-title text-base mb-4">使用统计</h3>
            <div class="stats stats-horizontal">
              <div class="stat">
                <div class="stat-title">总请求</div>
                <div class="stat-value text-primary">{{ engine.total_requests || 0 }}</div>
              </div>
              <div class="stat">
                <div class="stat-title">成功</div>
                <div class="stat-value text-success">{{ engine.success_count || 0 }}</div>
              </div>
              <div class="stat">
                <div class="stat-title">失败</div>
                <div class="stat-value text-error">{{ engine.failure_count || 0 }}</div>
              </div>
              <div class="stat">
                <div class="stat-title">成功率</div>
                <div class="stat-value">{{ successRate }}%</div>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4 mt-4">
              <div>
                <div class="text-sm text-gray-500">总花费</div>
                <div class="text-lg font-bold mt-1">
                  ${{ parseFloat(engine.total_cost || 0).toFixed(2) }}
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">节省金额</div>
                <div class="text-lg font-bold mt-1 text-success">
                  ${{ parseFloat(engine.saved_cost || 0).toFixed(2) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 配置信息 -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h3 class="card-title text-base mb-4">引擎配置</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <div class="text-sm text-gray-500">主引擎</div>
                <div class="mt-1">
                  <span class="badge badge-lg">{{ engine.primary_provider }}</span>
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">备份引擎</div>
                <div class="mt-1">
                  <span
                    v-if="engine.fallback_provider"
                    class="badge badge-lg badge-ghost"
                  >
                    {{ engine.fallback_provider }}
                  </span>
                  <span v-else class="text-gray-400">未配置</span>
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">自动切换</div>
                <div class="mt-1">
                  <span
                    class="badge"
                    :class="engine.auto_fallback ? 'badge-success' : 'badge-ghost'"
                  >
                    {{ engine.auto_fallback ? "已启用" : "已禁用" }}
                  </span>
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">活跃状态</div>
                <div class="mt-1">
                  <span
                    class="badge"
                    :class="engine.is_active ? 'badge-success' : 'badge-error'"
                  >
                    {{ engine.is_active ? "活跃" : "禁用" }}
                  </span>
                </div>
              </div>
              <div>
                <div class="text-sm text-gray-500">失败阈值</div>
                <div class="mt-1">{{ engine.fallback_threshold }} 次</div>
              </div>
              <div>
                <div class="text-sm text-gray-500">超时设置</div>
                <div class="mt-1">{{ engine.fallback_timeout }} 秒</div>
              </div>
            </div>

            <!-- 主引擎配置 JSON -->
            <div class="mt-4">
              <div class="text-sm text-gray-500 mb-2">主引擎配置</div>
              <pre class="bg-base-300 p-3 rounded-lg text-xs overflow-x-auto">{{ JSON.stringify(engine.primary_config, null, 2) }}</pre>
            </div>

            <!-- 备份引擎配置 JSON -->
            <div v-if="engine.fallback_config" class="mt-4">
              <div class="text-sm text-gray-500 mb-2">备份引擎配置</div>
              <pre class="bg-base-300 p-3 rounded-lg text-xs overflow-x-auto">{{ JSON.stringify(engine.fallback_config, null, 2) }}</pre>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex justify-end gap-2">
          <button class="btn btn-outline" @click="$emit('close')">
            关闭
          </button>
        </div>
      </div>

      <div v-else class="text-center py-8">
        <span class="loading loading-spinner"></span>
        <div class="mt-2">加载中...</div>
      </div>
    </div>
    <!-- 背景遮罩 -->
    <div class="modal-backdrop" @click="$emit('close')"></div>
  </div>
</template>

<script>
export default {
  name: "EngineDetailModal",
  props: {
    engine: {
      type: Object,
      default: null,
    },
  },
  computed: {
    engineName() {
      if (!this.engine) return "";
      const names = {
        llm: "LLM 文本生成",
        image: "图像生成",
        tts: "语音合成",
      };
      return names[this.engine.engine_type] || this.engine.name;
    },
    statusText() {
      if (!this.engine) return "";
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
      if (!this.engine) return "";
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
      if (!this.engine) return 0;
      if (!this.engine.total_requests || this.engine.total_requests === 0) {
        return 0;
      }
      return this.engine.success_rate?.toFixed(1) || "0.0";
    },
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return "未检查";
      const date = new Date(dateStr);
      return date.toLocaleString("zh-CN");
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
