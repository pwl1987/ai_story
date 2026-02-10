/**
 * 角色资产管理 API Service
 *
 * 提供角色、造型、音色配置的CRUD操作
 */

import apiClient from './apiClient';

/**
 * 作品API
 */
export const artworkApi = {
  // 获取作品列表
  list(params) {
    return apiClient.get('/artworks/', { params });
  },

  // 获取作品详情
  get(id) {
    return apiClient.get(`/artworks/${id}/`);
  },

  // 获取作品的角色列表
  getCharacters(id, params) {
    return apiClient.get(`/artworks/${id}/characters/`, { params });
  },

  // 获取作品的物品列表
  getItems(id, params) {
    return apiClient.get(`/artworks/${id}/items/`, { params });
  },
};

/**
 * 角色档案API
 * Epic 11: 修正API路径，使用 /artworks/characters/ 前缀
 */
export const characterApi = {
  // 获取角色列表
  list(params) {
    return apiClient.get('/artworks/characters/', { params });
  },

  // 获取角色详情
  get(id) {
    return apiClient.get(`/artworks/characters/${id}/`);
  },

  // 创建角色
  create(data) {
    return apiClient.post('/artworks/characters/', data);
  },

  // 更新角色
  update(id, data) {
    return apiClient.put(`/artworks/characters/${id}/`, data);
  },

  // 部分更新角色
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/characters/${id}/`, data);
  },

  // 删除角色
  delete(id) {
    return apiClient.delete(`/artworks/characters/${id}/`);
  },

  // 获取角色造型列表
  getPoses(id, params) {
    return apiClient.get(`/artworks/characters/${id}/poses/`, { params });
  },

  // 为角色创建造型
  createPose(id, data) {
    return apiClient.post(`/artworks/characters/${id}/poses/`, data);
  },

  // 获取角色音色配置
  getVoiceConfig(id) {
    return apiClient.get(`/artworks/characters/${id}/voice_config/`);
  },

  // 更新角色音色配置
  updateVoiceConfig(id, data) {
    return apiClient.put(`/artworks/characters/${id}/voice_config/`, data);
  },

  // 部分更新角色音色配置
  partialUpdateVoiceConfig(id, data) {
    return apiClient.patch(`/artworks/characters/${id}/voice_config/`, data);
  },

  // 批量删除角色
  bulkDelete(characterIds) {
    return apiClient.post('/artworks/characters/bulk_delete/', {
      character_ids: characterIds,
    });
  },

  // 批量更新TTS引擎
  bulkUpdateTts(characterIds, ttsEngine) {
    return apiClient.post('/artworks/characters/bulk_update_tts/', {
      character_ids: characterIds,
      tts_engine: ttsEngine,
    });
  },

  // 上传角色立绘
  uploadPortrait(id, file) {
    const formData = new FormData();
    formData.append('default_portrait', file);
    return apiClient.post(`/artworks/characters/${id}/upload_portrait/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

/**
 * 角色造型API
 * Epic 11: 修正API路径，使用 /artworks/poses/ 前缀
 */
export const poseApi = {
  // 获取造型列表
  list(params) {
    return apiClient.get('/artworks/poses/', { params });
  },

  // 获取造型详情
  get(id) {
    return apiClient.get(`/artworks/poses/${id}/`);
  },

  // 创建造型
  create(data) {
    return apiClient.post('/artworks/poses/', data);
  },

  // 更新造型
  update(id, data) {
    return apiClient.put(`/artworks/poses/${id}/`, data);
  },

  // 部分更新造型
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/poses/${id}/`, data);
  },

  // 删除造型
  delete(id) {
    return apiClient.delete(`/artworks/poses/${id}/`);
  },

  // 设为默认造型
  setDefault(id) {
    return apiClient.post(`/artworks/poses/${id}/set_default/`);
  },

  // 增加使用计数
  incrementUsage(id) {
    return apiClient.post(`/artworks/poses/${id}/increment_usage/`);
  },

  // 批量删除造型
  bulkDelete(poseIds) {
    return apiClient.post('/artworks/poses/bulk_delete/', {
      pose_ids: poseIds,
    });
  },

  // 上传造型图片
  uploadImage(id, file) {
    const formData = new FormData();
    formData.append('pose_image', file);
    return apiClient.post(`/artworks/poses/${id}/upload_image/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

/**
 * 角色音色配置API
 * Epic 11: 修正API路径，使用 /artworks/voice-configs/ 前缀
 */
export const voiceConfigApi = {
  // 获取音色配置列表
  list(params) {
    return apiClient.get('/artworks/voice-configs/', { params });
  },

  // 获取音色配置详情
  get(id) {
    return apiClient.get(`/artworks/voice-configs/${id}/`);
  },

  // 创建音色配置
  create(data) {
    return apiClient.post('/artworks/voice-configs/', data);
  },

  // 更新音色配置
  update(id, data) {
    return apiClient.put(`/artworks/voice-configs/${id}/`, data);
  },

  // 部分更新音色配置
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/voice-configs/${id}/`, data);
  },

  // 删除音色配置
  delete(id) {
    return apiClient.delete(`/artworks/voice-configs/${id}/`);
  },

  // 生成试听样本
  preview(id, text) {
    return apiClient.post(`/artworks/voice-configs/${id}/preview/`, { text });
  },
};

/**
 * 物品档案API
 * Epic 11: 修正API路径，使用 /artworks/items/ 前缀
 */
export const itemApi = {
  // 获取物品列表
  list(params) {
    return apiClient.get('/artworks/items/', { params });
  },

  // 获取物品详情
  get(id) {
    return apiClient.get(`/artworks/items/${id}/`);
  },

  // 创建物品
  create(data) {
    return apiClient.post('/artworks/items/', data);
  },

  // 更新物品
  update(id, data) {
    return apiClient.put(`/artworks/items/${id}/`, data);
  },

  // 部分更新物品
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/items/${id}/`, data);
  },

  // 删除物品
  delete(id) {
    return apiClient.delete(`/artworks/items/${id}/`);
  },

  // 增加使用计数
  incrementUsage(id) {
    return apiClient.post(`/artworks/items/${id}/increment_usage/`);
  },
};

/**
 * 场景API (Story 11.2.1)
 * Epic 11: 使用 /artworks/scenes/ 前缀
 */
export const sceneApi = {
  // 获取场景列表
  list(params) {
    return apiClient.get('/artworks/scenes/', { params });
  },

  // 获取场景详情
  get(id) {
    return apiClient.get(`/artworks/scenes/${id}/`);
  },

  // 更新场景
  update(id, data) {
    return apiClient.put(`/artworks/scenes/${id}/`, data);
  },

  // 部分更新场景
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/scenes/${id}/`, data);
  },
};

/**
 * 镜头API (Story 11.2.4)
 * Epic 11: 使用 /artworks/shots/ 前缀
 */
export const shotApi = {
  // 获取镜头列表
  list(params) {
    return apiClient.get('/artworks/shots/', { params });
  },

  // 获取镜头详情
  get(id) {
    return apiClient.get(`/artworks/shots/${id}/`);
  },

  // 创建镜头
  create(data) {
    return apiClient.post('/artworks/shots/', data);
  },

  // 更新镜头
  update(id, data) {
    return apiClient.put(`/artworks/shots/${id}/`, data);
  },

  // 部分更新镜头
  partialUpdate(id, data) {
    return apiClient.patch(`/artworks/shots/${id}/`, data);
  },

  // 删除镜头
  delete(id) {
    return apiClient.delete(`/artworks/shots/${id}/`);
  },

  // 重新生成镜头内容 (Story 11.2.4)
  regenerate(id, options) {
    return apiClient.post(`/artworks/shots/${id}/regenerate/`, options);
  },

  // 批量更新镜头排序
  bulkUpdateSort(shotOrders) {
    return apiClient.post('/artworks/shots/bulk_update_sort/', {
      shot_orders: shotOrders,
    });
  },

  // 批量删除镜头
  bulkDelete(shotIds) {
    return apiClient.post('/artworks/shots/bulk_delete/', {
      shot_ids: shotIds,
    });
  },

  // 批量更新角色造型
  bulkUpdatePose(shotIds, poseId) {
    return apiClient.post('/artworks/shots/bulk_update_pose/', {
      shot_ids: shotIds,
      pose_id: poseId,
    });
  },
};

export default {
  artwork: artworkApi,
  character: characterApi,
  pose: poseApi,
  voiceConfig: voiceConfigApi,
  item: itemApi,
  scene: sceneApi,
  shot: shotApi,
};
