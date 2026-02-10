/**
 * 批量操作 API 服务 (Story 11.5.1)
 *
 * 提供批量操作的 API 接口
 */

import apiClient from '@/services/apiClient'

// Base URL
const BASE_URL = '/api/v1/artworks'

/**
 * 批量操作 API
 */
export const batchApi = {
  // ========== 镜头批量操作 ==========
  shots: {
    /**
     * 批量更新角色造型
     * @param {number[]} shotIds - 镜头ID列表
     * @param {number|null} characterPoseId - 角色造型ID (null表示清除)
     * @returns {Promise}
     */
    updateCharacter(shotIds, characterPoseId) {
      return apiClient({
        url: `${BASE_URL}/shots/bulk_update_character/`,
        method: 'post',
        data: {
          shot_ids: shotIds,
          character_pose_id: characterPoseId,
        },
      })
    },

    /**
     * 批量移动镜头
     * @param {number[]} shotIds - 镜头ID列表
     * @param {number} targetSceneId - 目标场景ID
     * @param {boolean} updateSortOrder - 是否更新排序
     * @returns {Promise}
     */
    move(shotIds, targetSceneId, updateSortOrder = true) {
      return apiClient({
        url: `${BASE_URL}/shots/bulk_move/`,
        method: 'post',
        data: {
          shot_ids: shotIds,
          target_scene_id: targetSceneId,
          update_sort_order: updateSortOrder,
        },
      })
    },

    /**
     * 批量删除镜头 (增强版)
     * @param {number[]} shotIds - 镜头ID列表
     * @returns {Promise}
     */
    delete(shotIds) {
      return apiClient({
        url: `${BASE_URL}/shots/bulk_delete_enhanced/`,
        method: 'post',
        data: {
          shot_ids: shotIds,
        },
      })
    },

    /**
     * 批量重新生成镜头
     * @param {number[]} shotIds - 镜头ID列表
     * @param {boolean} regenerateImage - 是否重新生成图像
     * @param {boolean} regenerateAudio - 是否重新生成音频
     * @param {object} overrideParams - 覆盖参数
     * @returns {Promise}
     */
    regenerate(shotIds, regenerateImage = true, regenerateAudio = true, overrideParams = {}) {
      return apiClient({
        url: `${BASE_URL}/shots/bulk_regenerate/`,
        method: 'post',
        data: {
          shot_ids: shotIds,
          regenerate_image: regenerateImage,
          regenerate_audio: regenerateAudio,
          override_params: overrideParams,
        },
      })
    },
  },

  // ========== 场景批量操作 ==========
  scenes: {
    /**
     * 批量删除场景 (增强版)
     * @param {number[]} sceneIds - 场景ID列表
     * @returns {Promise}
     */
    delete(sceneIds) {
      return apiClient({
        url: `${BASE_URL}/script-scenes/bulk_delete_enhanced/`,
        method: 'post',
        data: {
          scene_ids: sceneIds,
        },
      })
    },

    /**
     * 批量更新转场配置
     * @param {number[]} sceneIds - 场景ID列表
     * @param {string} transitionType - 转场类型
     * @param {number} transitionDuration - 转场时长
     * @returns {Promise}
     */
    updateTransition(sceneIds, transitionType, transitionDuration) {
      return apiClient({
        url: `${BASE_URL}/script-scenes/bulk_update_transition/`,
        method: 'post',
        data: {
          scene_ids: sceneIds,
          transition_type: transitionType,
          transition_duration: transitionDuration,
        },
      })
    },
  },

  // ========== 进度追踪 ==========
  progress: {
    /**
     * 获取进度列表
     * @param {object} params - 查询参数
     * @returns {Promise}
     */
    list(params = {}) {
      return apiClient({
        url: `${BASE_URL}/progress/`,
        method: 'get',
        params,
      })
    },

    /**
     * 获取进度详情
     * @param {number} progressId - 进度ID
     * @returns {Promise}
     */
    getDetail(progressId) {
      return apiClient({
        url: `${BASE_URL}/progress/${progressId}/`,
        method: 'get',
      })
    },
  },
}

export default batchApi
