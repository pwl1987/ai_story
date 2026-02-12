import apiClient from '../apiClient';

/**
 * 章节相关 API 服务
 *
 * 提供章节和场景的 API 调用方法
 */

export default {
  /**
   * 获取章节详情
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Object>} 章节数据
   */
  async get(chapterId) {
    const response = await apiClient.get(`/artworks/chapters/${chapterId}/`);
    return response.data;
  },

  /**
   * 获取章节的所有场景
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Array>} 场景列表
   */
  async getScenes(chapterId) {
    const response = await apiClient.get(`/artworks/chapters/${chapterId}/scenes/`);
    return response.data;
  },

  /**
   * 启动章节工作流
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Object>} 工作流启动响应
   */
  async startWorkflow(chapterId) {
    const response = await apiClient.post(`/artworks/chapters/${chapterId}/start-workflow/`);
    return response.data;
  },

  /**
   * 暂停章节工作流
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Object>} 暂停响应
   */
  async pauseWorkflow(chapterId) {
    const response = await apiClient.post(`/artworks/chapters/${chapterId}/pause-workflow/`);
    return response.data;
  },

  /**
   * 继续章节工作流
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Object>} 继续响应
   */
  async resumeWorkflow(chapterId) {
    const response = await apiClient.post(`/artworks/chapters/${chapterId}/resume-workflow/`);
    return response.data;
  },

  /**
   * 获取工作流状态
   * @param {number} chapterId - 章节 ID
   * @returns {Promise<Object>} 工作流状态数据
   */
  async getWorkflowStatus(chapterId) {
    const response = await apiClient.get(`/artworks/chapters/${chapterId}/workflow-status/`);
    return response.data;
  },
};
