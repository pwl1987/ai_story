/**
 * 角色资产管理 Vuex Store Module
 *
 * 管理角色、造型、音色配置的状态
 */

import api from '@/services/artworkService';

const state = {
  // 作品列表
  artworks: [],
  currentArtwork: null,

  // 角色列表
  characters: [],
  currentCharacter: null,

  // 造型列表
  poses: [],
  currentPose: null,

  // 音色配置
  voiceConfigs: [],
  currentVoiceConfig: null,

  // 物品列表
  items: [],
  currentItem: null,

  // 分页信息
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },

  // 加载状态
  loading: {
    artworks: false,
    characters: false,
    poses: false,
    voiceConfigs: false,
    items: false,
  },

  // 错误信息
  error: null,
};

const getters = {
  // 作品相关
  artworkById: (state) => (id) => {
    return state.artworks.find((a) => a.id === id);
  },
  currentArtworkCharacters: (state) => {
    if (!state.currentArtwork) return [];
    return state.characters.filter(
      (c) => c.artwork === state.currentArtwork.id
    );
  },

  // 角色相关
  characterById: (state) => (id) => {
    return state.characters.find((c) => c.id === id);
  },
  charactersByArtwork: (state) => (artworkId) => {
    return state.characters.filter((c) => c.artwork === artworkId);
  },
  mainCharacters: (state) => {
    return state.characters
      .filter((c) => c.importance_rank <= 3)
      .sort((a, b) => a.importance_rank - b.importance_rank);
  },

  // 造型相关
  poseById: (state) => (id) => {
    return state.poses.find((p) => p.id === id);
  },
  posesByCharacter: (state) => (characterId) => {
    return state.poses.filter((p) => p.character === characterId);
  },
  defaultPose: (state) => (characterId) => {
    return state.poses.find(
      (p) => p.character === characterId && p.is_default
    );
  },

  // 音色配置相关
  voiceConfigById: (state) => (id) => {
    return state.voiceConfigs.find((v) => v.id === id);
  },
  voiceConfigByCharacter: (state) => (characterId) => {
    return state.voiceConfigs.find((v) => v.character === characterId);
  },

  // 加载状态
  isLoading: (state) => (key) => {
    return state.loading[key] || false;
  },
  anyLoading: (state) => {
    return Object.values(state.loading).some((v) => v);
  },

  // 分页信息
  totalPages: (state) => {
    return Math.ceil(state.pagination.total / state.pagination.pageSize);
  },
};

const mutations = {
  // 设置作品列表
  SET_ARTWORKS(state, artworks) {
    state.artworks = artworks;
  },

  // 设置当前作品
  SET_CURRENT_ARTWORK(state, artwork) {
    state.currentArtwork = artwork;
  },

  // 设置角色列表
  SET_CHARACTERS(state, characters) {
    state.characters = characters;
  },

  // 添加角色
  ADD_CHARACTER(state, character) {
    state.characters.unshift(character);
  },

  // 更新角色
  UPDATE_CHARACTER(state, character) {
    const index = state.characters.findIndex((c) => c.id === character.id);
    if (index !== -1) {
      state.characters.splice(index, 1, character);
    }
    if (state.currentCharacter && state.currentCharacter.id === character.id) {
      state.currentCharacter = { ...state.currentCharacter, ...character };
    }
  },

  // 删除角色
  REMOVE_CHARACTER(state, id) {
    state.characters = state.characters.filter((c) => c.id !== id);
    if (state.currentCharacter && state.currentCharacter.id === id) {
      state.currentCharacter = null;
    }
  },

  // 设置当前角色
  SET_CURRENT_CHARACTER(state, character) {
    state.currentCharacter = character;
  },

  // 设置造型列表
  SET_POSES(state, poses) {
    state.poses = poses;
  },

  // 添加造型
  ADD_POSE(state, pose) {
    state.poses.unshift(pose);
  },

  // 更新造型
  UPDATE_POSE(state, pose) {
    const index = state.poses.findIndex((p) => p.id === pose.id);
    if (index !== -1) {
      state.poses.splice(index, 1, pose);
    }
    if (state.currentPose && state.currentPose.id === pose.id) {
      state.currentPose = { ...state.currentPose, ...pose };
    }
  },

  // 删除造型
  REMOVE_POSE(state, id) {
    state.poses = state.poses.filter((p) => p.id !== id);
    if (state.currentPose && state.currentPose.id === id) {
      state.currentPose = null;
    }
  },

  // 设置当前造型
  SET_CURRENT_POSE(state, pose) {
    state.currentPose = pose;
  },

  // 设置音色配置列表
  SET_VOICE_CONFIGS(state, configs) {
    state.voiceConfigs = configs;
  },

  // 设置当前音色配置
  SET_CURRENT_VOICE_CONFIG(state, config) {
    state.currentVoiceConfig = config;
  },

  // 更新音色配置
  UPDATE_VOICE_CONFIG(state, config) {
    const index = state.voiceConfigs.findIndex((v) => v.id === config.id);
    if (index !== -1) {
      state.voiceConfigs.splice(index, 1, config);
    }
    if (
      state.currentVoiceConfig &&
      state.currentVoiceConfig.id === config.id
    ) {
      state.currentVoiceConfig = { ...state.currentVoiceConfig, ...config };
    }
  },

  // 设置物品列表
  SET_ITEMS(state, items) {
    state.items = items;
  },

  // 设置分页信息
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination };
  },

  // 设置加载状态
  SET_LOADING(state, { key, value }) {
    state.loading[key] = value;
  },

  // 设置错误信息
  SET_ERROR(state, error) {
    state.error = error;
  },

  // 清除错误
  CLEAR_ERROR(state) {
    state.error = null;
  },
};

const actions = {
  // ========== 作品操作 ==========

  // 获取作品列表
  async fetchArtworks({ commit }, params) {
    commit('SET_LOADING', { key: 'artworks', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.artwork.list(params);
      commit('SET_ARTWORKS', response.results || response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'artworks', value: false });
    }
  },

  // 获取作品详情
  async fetchArtwork({ commit }, id) {
    commit('SET_LOADING', { key: 'artworks', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.artwork.get(id);
      commit('SET_CURRENT_ARTWORK', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'artworks', value: false });
    }
  },

  // ========== 角色操作 ==========

  // 获取角色列表
  async fetchCharacters({ commit }, params) {
    commit('SET_LOADING', { key: 'characters', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.list(params);
      commit('SET_CHARACTERS', response.results || response);
      if (response.count) {
        commit('SET_PAGINATION', {
          total: response.count,
          page: params.page || 1,
        });
      }
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'characters', value: false });
    }
  },

  // 获取角色详情
  async fetchCharacter({ commit }, id) {
    commit('SET_LOADING', { key: 'characters', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.get(id);
      commit('SET_CURRENT_CHARACTER', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'characters', value: false });
    }
  },

  // 创建角色
  async createCharacter({ commit }, data) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.create(data);
      commit('ADD_CHARACTER', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 更新角色
  async updateCharacter({ commit }, { id, data }) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.update(id, data);
      commit('UPDATE_CHARACTER', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 删除角色
  async deleteCharacter({ commit }, id) {
    commit('CLEAR_ERROR');
    try {
      await api.character.delete(id);
      commit('REMOVE_CHARACTER', id);
      return true;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 批量删除角色
  async bulkDeleteCharacters({ commit }, characterIds) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.bulkDelete(characterIds);
      // 删除本地状态
      characterIds.forEach((id) => {
        commit('REMOVE_CHARACTER', id);
      });
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 批量更新TTS引擎
  async bulkUpdateTts({ commit }, { characterIds, ttsEngine }) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.bulkUpdateTts(
        characterIds,
        ttsEngine
      );
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // ========== 造型操作 ==========

  // 获取造型列表
  async fetchPoses({ commit }, params) {
    commit('SET_LOADING', { key: 'poses', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.pose.list(params);
      commit('SET_POSES', response.results || response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'poses', value: false });
    }
  },

  // 创建造型
  async createPose({ commit }, data) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.pose.create(data);
      commit('ADD_POSE', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 更新造型
  async updatePose({ commit }, { id, data }) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.pose.update(id, data);
      commit('UPDATE_POSE', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 删除造型
  async deletePose({ commit }, id) {
    commit('CLEAR_ERROR');
    try {
      await api.pose.delete(id);
      commit('REMOVE_POSE', id);
      return true;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 设为默认造型
  async setDefaultPose({ commit }, id) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.pose.setDefault(id);
      commit('UPDATE_POSE', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 增加造型使用计数
  async incrementPoseUsage({ commit }, id) {
    try {
      const response = await api.pose.incrementUsage(id);
      commit('UPDATE_POSE', response);
      return response;
    } catch (error) {
      // 使用计数更新失败不影响主流程
      console.error('Failed to increment pose usage:', error);
    }
  },

  // ========== 音色配置操作 ==========

  // 获取角色音色配置
  async fetchVoiceConfig({ commit }, characterId) {
    commit('SET_LOADING', { key: 'voiceConfigs', value: true });
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.getVoiceConfig(characterId);
      commit('SET_CURRENT_VOICE_CONFIG', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    } finally {
      commit('SET_LOADING', { key: 'voiceConfigs', value: false });
    }
  },

  // 更新角色音色配置
  async updateVoiceConfig({ commit }, { characterId, data }) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.character.updateVoiceConfig(
        characterId,
        data
      );
      commit('UPDATE_VOICE_CONFIG', response);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },

  // 生成试听样本
  async generateVoicePreview({ commit }, { id, text }) {
    commit('CLEAR_ERROR');
    try {
      const response = await api.voiceConfig.preview(id, text);
      return response;
    } catch (error) {
      commit('SET_ERROR', error.message);
      throw error;
    }
  },
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions,
};
