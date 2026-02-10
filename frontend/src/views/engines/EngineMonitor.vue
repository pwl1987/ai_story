<!-- Engine Monitor - 引擎监控主页面 -->
<template>
  <div class="p-6">
    <!-- 页面标题和操作栏 -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold">引擎监控</h1>
        <p class="text-sm text-gray-500 mt-1">
          实时监控 LLM、Image、TTS 引擎健康状态
        </p>
      </div>
      <div class="flex gap-2">
        <button
          class="btn btn-outline btn-sm"
          @click="refreshAll"
          :class="{ 'loading': loading }"
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
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          刷新
        </button>
        <button
          class="btn btn-primary btn-sm"
          @click="checkAllEngines"
          :disabled="loading"
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
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          健康检查
        </button>
      </div>
    </div>

    <!-- WebSocket 连接状态 -->
    <div class="alert mb-4" :class="wsConnected ? 'alert-success' : 'alert-warning'">
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
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>
        {{ wsConnected ? "实时连接已建立" : "实时连接断开，数据可能延迟" }}
      </span>
    </div>

    <!-- 统计概览 -->
    <div class="stats-grid grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="stat-card bg-base-100 shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">总请求数</div>
        <div class="text-2xl font-bold mt-1">{{ totalRequests }}</div>
      </div>
      <div class="stat-card bg-base-100 shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">成功率</div>
        <div class="text-2xl font-bold mt-1">{{ overallSuccessRate.toFixed(1) }}%</div>
      </div>
      <div class="stat-card bg-base-100 shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">总花费</div>
        <div class="text-2xl font-bold mt-1">${{ totalCost.toFixed(2) }}</div>
      </div>
      <div class="stat-card bg-base-100 shadow rounded-lg p-4">
        <div class="text-sm text-gray-500">节省金额</div>
        <div class="text-2xl font-bold mt-1 text-success">
          ${{ totalSavedCost.toFixed(2) }}
        </div>
      </div>
    </div>

    <!-- 引擎卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- LLM 引擎卡片 -->
      <EngineCard
        v-if="llmEngine"
        :engine="llmEngine"
        @test-connection="handleTestConnection"
        @reset-stats="handleResetStats"
        @switch-provider="handleSwitchProvider"
        @view-details="handleViewDetails"
      />
      <div v-else class="alert">
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
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        LLM 引擎未配置
      </div>

      <!-- Image 引擎卡片 -->
      <EngineCard
        v-if="imageEngine"
        :engine="imageEngine"
        @test-connection="handleTestConnection"
        @reset-stats="handleResetStats"
        @switch-provider="handleSwitchProvider"
        @view-details="handleViewDetails"
      />
      <div v-else class="alert">
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
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        Image 引擎未配置
      </div>

      <!-- TTS 引擎卡片 -->
      <EngineCard
        v-if="ttsEngine"
        :engine="ttsEngine"
        @test-connection="handleTestConnection"
        @reset-stats="handleResetStats"
        @switch-provider="handleSwitchProvider"
        @view-details="handleViewDetails"
      />
      <div v-else class="alert">
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
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        TTS 引擎未配置
      </div>
    </div>

    <!-- Fallback 事件日志 -->
    <div class="mt-6">
      <h2 class="text-xl font-bold mb-4">Fallback 事件历史</h2>
      <div class="overflow-x-auto">
        <table class="table table-zebra table-compact w-full">
          <thead>
            <tr>
              <th>时间</th>
              <th>引擎</th>
              <th>从</th>
              <th>到</th>
              <th>原因</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="fallbackEvents.length === 0">
              <td colspan="6" class="text-center text-gray-500">暂无事件</td>
            </tr>
            <tr v-for="event in fallbackEvents" :key="event.id">
              <td>{{ formatDate(event.switched_at) }}</td>
              <td>{{ event.engine_type }}</td>
              <td>{{ event.from_provider }}</td>
              <td>{{ event.to_provider }}</td>
              <td>
                <span
                  class="badge"
                  :class="{
                    'badge-error': event.reason === 'failure',
                    'badge-warning': event.reason === 'timeout',
                    'badge-info': event.reason === 'manual',
                  }"
                >
                  {{ event.reason_display }}
                </span>
              </td>
              <td class="text-sm">{{ event.reason_detail }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 引擎详情模态框 -->
    <EngineDetailModal
      v-if="showDetailModal"
      :engine="selectedEngine"
      @close="showDetailModal = false"
    />
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from "vuex";
import EngineCard from "@/components/engines/EngineCard.vue";
import EngineDetailModal from "@/components/engines/EngineDetailModal.vue";

export default {
  name: "EngineMonitor",
  components: {
    EngineCard,
    EngineDetailModal,
  },
  data() {
    return {
      showDetailModal: false,
      pollingInterval: null,
    };
  },
  computed: {
    ...mapState("engines", [
      "engines",
      "loading",
      "error",
      "wsConnected",
      "fallbackEvents",
    ]),
    ...mapGetters("engines", [
      "llmEngine",
      "imageEngine",
      "ttsEngine",
      "totalRequests",
      "overallSuccessRate",
      "totalSavedCost",
      "totalCost",
    ]),
    selectedEngine() {
      return this.$store.state.engines.selectedEngine;
    },
  },
  mounted() {
    this.loadData();
    this.connectWebSocket();
    // 每 30 秒自动刷新
    this.pollingInterval = setInterval(() => {
      this.refreshAll();
    }, 30000);
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
    }
    this.disconnectWebSocket();
  },
  methods: {
    ...mapActions("engines", [
      "fetchEngines",
      "fetchStats",
      "checkHealth",
      "testConnection",
      "resetStats",
      "switchProvider",
      "connectWebSocket",
      "disconnectWebSocket",
      "fetchEngine",
    ]),

    async loadData() {
      try {
        await Promise.all([this.fetchEngines(), this.fetchStats()]);
      } catch (error) {
        console.error("加载引擎数据失败:", error);
        this.$toast?.error("加载数据失败: " + error.message);
      }
    },

    async refreshAll() {
      await this.loadData();
    },

    async checkAllEngines() {
      try {
        const result = await this.checkHealth(null);
        this.$toast?.success("健康检查已启动");
      } catch (error) {
        this.$toast?.error("健康检查失败: " + error.message);
      }
    },

    async handleTestConnection(engineType) {
      try {
        const result = await this.testConnection(engineType);
        if (result.success) {
          this.$toast?.success(`${engineType} 引擎连接正常`);
        } else {
          this.$toast?.error(
            `${engineType} 引擎连接失败: ${result.error_message || result.error || "未知错误"}`
          );
        }
      } catch (error) {
        this.$toast?.error(`测试连接失败: ${error.message}`);
      }
    },

    async handleResetStats(engineType) {
      if (!confirm(`确定要重置 ${engineType} 引擎的统计数据吗？`)) {
        return;
      }
      try {
        await this.resetStats(engineType);
        this.$toast?.success("统计已重置");
      } catch (error) {
        this.$toast?.error("重置失败: " + error.message);
      }
    },

    async handleSwitchProvider({ engineType, provider }) {
      try {
        await this.switchProvider({ engineType, provider });
        this.$toast?.success(`已切换到 ${provider}`);
      } catch (error) {
        this.$toast?.error("切换失败: " + error.message);
      }
    },

    async handleViewDetails(engineType) {
      try {
        await this.fetchEngine(engineType);
        this.showDetailModal = true;
      } catch (error) {
        this.$toast?.error("加载详情失败: " + error.message);
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return "-";
      const date = new Date(dateStr);
      return date.toLocaleString("zh-CN");
    },
  },
};
</script>

<style scoped>
.stats-grid {
  display: grid;
  gap: 1rem;
}

.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}
</style>
