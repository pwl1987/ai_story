// Engines Vuex Store Module - 引擎状态管理

import { enginesService } from "@/services/enginesService";

// 状态
const state = {
  // 引擎配置列表
  engines: [],
  // 当前选中的引擎
  selectedEngine: null,
  // 引擎统计信息
  stats: [],
  // 健康日志
  healthLogs: [],
  // 使用日志
  usageLogs: [],
  // Fallback 事件
  fallbackEvents: [],
  // 加载状态
  loading: false,
  // 错误信息
  error: null,
  // WebSocket 连接状态
  wsConnected: false,
  // WebSocket 实例
  ws: null,
};

// Getters
const getters = {
  // 按 engine_type 索引的引擎 Map
  enginesByType: (state) => {
    const map = {};
    state.engines.forEach((engine) => {
      map[engine.engine_type] = engine;
    });
    return map;
  },

  // 在线引擎列表
  onlineEngines: (state) => {
    return state.engines.filter((e) => e.health_status === "online");
  },

  // 离线引擎列表
  offlineEngines: (state) => {
    return state.engines.filter((e) => e.health_status === "offline");
  },

  // 异常引擎列表
  errorEngines: (state) => {
    return state.engines.filter((e) => e.health_status === "error");
  },

  // LLM 引擎
  llmEngine: (state) => {
    return state.engines.find((e) => e.engine_type === "llm");
  },

  // Image 引擎
  imageEngine: (state) => {
    return state.engines.find((e) => e.engine_type === "image");
  },

  // TTS 引擎
  ttsEngine: (state) => {
    return state.engines.find((e) => e.engine_type === "tts");
  },

  // 总请求数
  totalRequests: (state) => {
    return state.engines.reduce((sum, e) => sum + (e.total_requests || 0), 0);
  },

  // 总成功率
  overallSuccessRate: (state) => {
    const totalSuccess = state.engines.reduce(
      (sum, e) => sum + (e.success_count || 0),
      0
    );
    const totalRequests = state.engines.reduce(
      (sum, e) => sum + (e.total_requests || 0),
      0
    );
    return totalRequests > 0 ? (totalSuccess / totalRequests) * 100 : 0;
  },

  // 总节省金额
  totalSavedCost: (state) => {
    return state.engines.reduce(
      (sum, e) => sum + (parseFloat(e.saved_cost) || 0),
      0
    );
  },

  // 总花费
  totalCost: (state) => {
    return state.engines.reduce(
      (sum, e) => sum + (parseFloat(e.total_cost) || 0),
      0
    );
  },
};

// Actions
const actions = {
  /**
   * 获取所有引擎配置
   */
  async fetchEngines({ commit }) {
    commit("SET_LOADING", true);
    commit("SET_ERROR", null);
    try {
      const data = await enginesService.getEngines();
      commit("SET_ENGINES", data);
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  /**
   * 获取单个引擎配置
   */
  async fetchEngine({ commit }, engineType) {
    commit("SET_LOADING", true);
    commit("SET_ERROR", null);
    try {
      const data = await enginesService.getEngine(engineType);
      commit("SET_SELECTED_ENGINE", data);
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  /**
   * 创建引擎配置
   */
  async createEngine({ commit, dispatch }, engineData) {
    commit("SET_LOADING", true);
    commit("SET_ERROR", null);
    try {
      const data = await enginesService.createEngine(engineData);
      // 重新获取引擎列表
      await dispatch("fetchEngines");
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  /**
   * 更新引擎配置
   */
  async updateEngine({ commit, dispatch }, { engineType, engineData }) {
    commit("SET_LOADING", true);
    commit("SET_ERROR", null);
    try {
      const data = await enginesService.updateEngine(engineType, engineData);
      // 重新获取引擎列表
      await dispatch("fetchEngines");
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  /**
   * 删除引擎配置
   */
  async deleteEngine({ commit, dispatch }, engineType) {
    commit("SET_LOADING", true);
    commit("SET_ERROR", null);
    try {
      await enginesService.deleteEngine(engineType);
      // 重新获取引擎列表
      await dispatch("fetchEngines");
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    } finally {
      commit("SET_LOADING", false);
    }
  },

  /**
   * 获取引擎统计
   */
  async fetchStats({ commit }) {
    try {
      const data = await enginesService.getStats();
      commit("SET_STATS", data);
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    }
  },

  /**
   * 手动触发健康检查
   */
  async checkHealth({ commit }, engineType = null) {
    try {
      const data = await enginesService.checkHealth(engineType);
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    }
  },

  /**
   * 测试引擎连接
   */
  async testConnection({ commit }, engineType) {
    try {
      const data = await enginesService.testConnection(engineType);
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    }
  },

  /**
   * 重置引擎统计
   */
  async resetStats({ commit, dispatch }, engineType) {
    try {
      const data = await enginesService.resetStats(engineType);
      // 重新获取引擎列表
      await dispatch("fetchEngines");
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    }
  },

  /**
   * 手动切换引擎提供商
   */
  async switchProvider({ commit, dispatch }, { engineType, provider }) {
    try {
      const data = await enginesService.switchProvider(engineType, provider);
      // 重新获取引擎列表
      await dispatch("fetchEngines");
      return data;
    } catch (error) {
      commit("SET_ERROR", error.message);
      throw error;
    }
  },

  /**
   * 连接 WebSocket
   */
  connectWebSocket({ commit, dispatch }) {
    // 如果已经连接，先断开
    if (state.ws) {
      state.ws.close();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/engines/health/`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      commit("SET_WS_CONNECTED", true);
      console.log("引擎健康 WebSocket 已连接");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // 处理健康状态更新
        if (data.type === "health_update") {
          // 更新引擎状态
          dispatch("updateEngineHealth", data);
        }
      } catch (error) {
        console.error("解析 WebSocket 消息失败:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket 错误:", error);
      commit("SET_WS_CONNECTED", false);
    };

    ws.onclose = () => {
      commit("SET_WS_CONNECTED", false);
      console.log("引擎健康 WebSocket 已断开");
      // 5秒后重连
      setTimeout(() => {
        dispatch("connectWebSocket");
      }, 5000);
    };

    commit("SET_WS", ws);
  },

  /**
   * 断开 WebSocket
   */
  disconnectWebSocket({ commit, state }) {
    if (state.ws) {
      state.ws.close();
      commit("SET_WS", null);
      commit("SET_WS_CONNECTED", false);
    }
  },

  /**
   * 刷新所有引擎
   */
  async refreshAll({ dispatch }) {
    try {
      await dispatch("fetchEngines");
      await dispatch("fetchStats");
    } catch (error) {
      console.error("刷新引擎数据失败:", error);
    }
  },
};

// Mutations
const mutations = {
  SET_ENGINES(state, engines) {
    state.engines = engines;
  },

  SET_SELECTED_ENGINE(state, engine) {
    state.selectedEngine = engine;
  },

  SET_STATS(state, stats) {
    state.stats = stats;
  },

  SET_HEALTH_LOGS(state, logs) {
    state.healthLogs = logs;
  },

  SET_USAGE_LOGS(state, logs) {
    state.usageLogs = logs;
  },

  SET_FALLBACK_EVENTS(state, events) {
    state.fallbackEvents = events;
  },

  SET_LOADING(state, loading) {
    state.loading = loading;
  },

  SET_ERROR(state, error) {
    state.error = error;
  },

  SET_WS(state, ws) {
    state.ws = ws;
  },

  SET_WS_CONNECTED(state, connected) {
    state.wsConnected = connected;
  },

  /**
   * 更新单个引擎的健康状态
   */
  UPDATE_ENGINE_HEALTH(state, healthData) {
    const engine = state.engines.find(
      (e) => e.engine_type === healthData.engine_type
    );
    if (engine) {
      engine.health_status = healthData.status;
      engine.last_health_check = healthData.checked_at;
      engine.avg_response_time = healthData.response_time;
    }
  },
};

// 导出
export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
};
