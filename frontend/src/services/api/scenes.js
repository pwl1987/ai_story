import apiClient from '../apiClient';

/**
 * 场景相关 API 服务
 *
 * 提供场景的 API 调用方法
 */

export default {
  /**
   * 获取场景详情
   * @param {number} sceneId - 场景 ID
   * @returns {Promise<Object>} 场景数据
   */
  async get(sceneId) {
    const response = await apiClient.get(`/artworks/scenes/${sceneId}/`);
    return response.data;
  },

  /**
   * 提取场景的首尾帧
   * @param {number} sceneId - 场景 ID
   * @returns {Promise<Object>} 提取任务响应
   */
  async extractFrames(sceneId) {
    const response = await apiClient.post(`/artworks/scenes/${sceneId}/extract-frames/`);
    return response.data;
  },
};
