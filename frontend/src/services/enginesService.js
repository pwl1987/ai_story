// Engines API Service - 引擎配置 API 服务

import axios from "axios";

const BASE_URL = "/api/v1/engines";

/**
 * 引擎配置 API 服务
 */
export const enginesService = {
  /**
   * 获取所有引擎配置
   */
  async getEngines() {
    const response = await axios.get(BASE_URL);
    return response.data;
  },

  /**
   * 获取单个引擎配置
   */
  async getEngine(engineType) {
    const response = await axios.get(`${BASE_URL}/${engineType}/`);
    return response.data;
  },

  /**
   * 创建引擎配置
   */
  async createEngine(data) {
    const response = await axios.post(BASE_URL, data);
    return response.data;
  },

  /**
   * 更新引擎配置
   */
  async updateEngine(engineType, data) {
    const response = await axios.put(`${BASE_URL}/${engineType}/`, data);
    return response.data;
  },

  /**
   * 部分更新引擎配置
   */
  async patchEngine(engineType, data) {
    const response = await axios.patch(`${BASE_URL}/${engineType}/`, data);
    return response.data;
  },

  /**
   * 删除引擎配置
   */
  async deleteEngine(engineType) {
    const response = await axios.delete(`${BASE_URL}/${engineType}/`);
    return response.data;
  },

  /**
   * 获取引擎统计信息
   */
  async getStats() {
    const response = await axios.get(`${BASE_URL}/stats/`);
    return response.data;
  },

  /**
   * 手动触发健康检查
   */
  async checkHealth(engineType = null) {
    const response = await axios.post(`${BASE_URL}/check_health/`, {
      engine_type: engineType,
    });
    return response.data;
  },

  /**
   * 测试引擎连接
   */
  async testConnection(engineType) {
    const response = await axios.post(`${BASE_URL}/${engineType}/test_connection/`);
    return response.data;
  },

  /**
   * 重置引擎统计
   */
  async resetStats(engineType) {
    const response = await axios.post(`${BASE_URL}/${engineType}/reset_stats/`);
    return response.data;
  },

  /**
   * 手动切换引擎提供商
   */
  async switchProvider(engineType, provider) {
    const response = await axios.post(`${BASE_URL}/${engineType}/switch_provider/`, {
      provider,
    });
    return response.data;
  },

  /**
   * 获取引擎健康历史
   */
  async getHealthHistory(engineType, limit = 10) {
    const response = await axios.get(
      `${BASE_URL}/${engineType}/health_history/?limit=${limit}`
    );
    return response.data;
  },

  /**
   * 获取引擎使用日志
   */
  async getUsageLogs(engineType, limit = 20) {
    const response = await axios.get(
      `${BASE_URL}/${engineType}/usage_logs/?limit=${limit}`
    );
    return response.data;
  },

  /**
   * 获取 Fallback 事件历史
   */
  async getFallbackEvents(engineType, limit = 10) {
    const response = await axios.get(
      `${BASE_URL}/${engineType}/fallback_events/?limit=${limit}`
    );
    return response.data;
  },

  /**
   * 获取所有健康日志
   */
  async getAllHealthLogs(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const url = queryParams ? `/api/v1/health-logs/?${queryParams}` : "/api/v1/health-logs/";
    const response = await axios.get(url);
    return response.data;
  },

  /**
   * 获取所有使用日志
   */
  async getAllUsageLogs(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const url = queryParams ? `/api/v1/usage-logs/?${queryParams}` : "/api/v1/usage-logs/";
    const response = await axios.get(url);
    return response.data;
  },

  /**
   * 获取所有 Fallback 事件
   */
  async getAllFallbackEvents(params = {}) {
    const queryParams = new URLSearchParams(params).toString();
    const url = queryParams
      ? `/api/v1/fallback-events/?${queryParams}`
      : "/api/v1/fallback-events/";
    const response = await axios.get(url);
    return response.data;
  },
};

export default enginesService;
