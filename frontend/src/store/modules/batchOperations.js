/**
 * 批量操作 Vuex Store 模块 (Story 11.5.1)
 *
 * 职责:
 * - 管理批量选择状态
 * - 批量操作 API 调用
 * - 进度追踪
 * - 错误报告
 */

import { batchApi } from '@/api/batch'

// State
const state = {
  // 批量选择的项目ID列表
  selectedShots: [],
  selectedScenes: [],
  // 当前批量操作类型
  currentOperation: null,
  // 操作进度
  operationProgress: null,
  // 操作结果
  operationResult: null,
  // 加载状态
  loading: false,
  // 错误信息
  error: null,
}

// Getters
const getters = {
  // 是否有选中的镜头
  hasSelectedShots: (state) => state.selectedShots.length > 0,

  // 是否有选中的场景
  hasSelectedScenes: (state) => state.selectedScenes.length > 0,

  // 选中的项目数量
  selectedCount: (state) => state.selectedShots.length + state.selectedScenes.length,

  // 是否有正在进行的操作
  hasActiveOperation: (state) => state.currentOperation !== null,

  // 操作进度百分比
  progressPercentage: (state) => {
    if (!state.operationProgress) return 0
    return state.operationProgress.progress_percentage || 0
  },

  // 操作状态文本
  operationStatusText: (state) => {
    if (!state.operationProgress) return ''
    const statusMap = {
      pending: '等待中',
      processing: '处理中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消',
    }
    return statusMap[state.operationProgress.status] || state.operationProgress.status
  },
}

// Mutations
const mutations = {
  // 添加选中的镜头
  ADD_SELECTED_SHOT(state, shotId) {
    if (!state.selectedShots.includes(shotId)) {
      state.selectedShots.push(shotId)
    }
  },

  // 移除选中的镜头
  REMOVE_SELECTED_SHOT(state, shotId) {
    const index = state.selectedShots.indexOf(shotId)
    if (index > -1) {
      state.selectedShots.splice(index, 1)
    }
  },

  // 切换镜头选中状态
  TOGGLE_SELECTED_SHOT(state, shotId) {
    const index = state.selectedShots.indexOf(shotId)
    if (index > -1) {
      state.selectedShots.splice(index, 1)
    } else {
      state.selectedShots.push(shotId)
    }
  },

  // 设置选中的镜头列表
  SET_SELECTED_SHOTS(state, shotIds) {
    state.selectedShots = [...shotIds]
  },

  // 清空选中的镜头
  CLEAR_SELECTED_SHOTS(state) {
    state.selectedShots = []
  },

  // 全选镜头
  SELECT_ALL_SHOTS(state, shotIds) {
    state.selectedShots = [...shotIds]
  },

  // 添加选中的场景
  ADD_SELECTED_SCENE(state, sceneId) {
    if (!state.selectedScenes.includes(sceneId)) {
      state.selectedScenes.push(sceneId)
    }
  },

  // 移除选中的场景
  REMOVE_SELECTED_SCENE(state, sceneId) {
    const index = state.selectedScenes.indexOf(sceneId)
    if (index > -1) {
      state.selectedScenes.splice(index, 1)
    }
  },

  // 切换场景选中状态
  TOGGLE_SELECTED_SCENE(state, sceneId) {
    const index = state.selectedScenes.indexOf(sceneId)
    if (index > -1) {
      state.selectedScenes.splice(index, 1)
    } else {
      state.selectedScenes.push(sceneId)
    }
  },

  // 清空选中的场景
  CLEAR_SELECTED_SCENES(state) {
    state.selectedScenes = []
  },

  // 清空所有选择
  CLEAR_ALL_SELECTIONS(state) {
    state.selectedShots = []
    state.selectedScenes = []
  },

  // 设置当前操作
  SET_CURRENT_OPERATION(state, operation) {
    state.currentOperation = operation
  },

  // 设置操作进度
  SET_OPERATION_PROGRESS(state, progress) {
    state.operationProgress = progress
  },

  // 设置操作结果
  SET_OPERATION_RESULT(state, result) {
    state.operationResult = result
  },

  // 设置加载状态
  SET_LOADING(state, loading) {
    state.loading = loading
  },

  // 设置错误信息
  SET_ERROR(state, error) {
    state.error = error
  },

  // 清除操作状态
  CLEAR_OPERATION_STATE(state) {
    state.currentOperation = null
    state.operationProgress = null
    state.operationResult = null
    state.error = null
  },
}

// Actions
const actions = {
  // 批量更新角色造型
  async batchUpdateCharacter({ commit }, { shotIds, characterPoseId }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)

    try {
      const response = await batchApi.shots.updateCharacter(shotIds, characterPoseId)
      commit('SET_OPERATION_RESULT', response.data)
      commit('SET_OPERATION_PROGRESS', response.data.progress_id)
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 批量移动镜头
  async batchMoveShots({ commit }, { shotIds, targetSceneId, updateSortOrder = true }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_CURRENT_OPERATION', 'bulk_move')

    try {
      const response = await batchApi.shots.move(shotIds, targetSceneId, updateSortOrder)
      commit('SET_OPERATION_RESULT', response.data)
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 批量删除镜头
  async batchDeleteShots({ commit }, shotIds) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_CURRENT_OPERATION', 'bulk_delete')

    try {
      const response = await batchApi.shots.delete(shotIds)
      commit('SET_OPERATION_RESULT', response.data)
      commit('CLEAR_SELECTED_SHOTS')
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 批量重新生成镜头
  async batchRegenerateShots(
    { commit },
    { shotIds, regenerateImage = true, regenerateAudio = true, overrideParams }
  ) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_CURRENT_OPERATION', 'bulk_regenerate')

    try {
      const response = await batchApi.shots.regenerate(
        shotIds,
        regenerateImage,
        regenerateAudio,
        overrideParams
      )
      commit('SET_OPERATION_RESULT', response.data)
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 批量删除场景
  async batchDeleteScenes({ commit }, sceneIds) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_CURRENT_OPERATION', 'bulk_delete_scenes')

    try {
      const response = await batchApi.scenes.delete(sceneIds)
      commit('SET_OPERATION_RESULT', response.data)
      commit('CLEAR_SELECTED_SCENES')
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取操作进度
  async fetchOperationProgress({ commit }, progressId) {
    try {
      const response = await batchApi.progress.getDetail(progressId)
      commit('SET_OPERATION_PROGRESS', response.data)
      return response.data
    } catch (error) {
      commit('SET_ERROR', error.response?.data || error.message)
      throw error
    }
  },

  // 轮询操作进度直到完成
  async pollOperationProgress({ dispatch }, { progressId, onProgress, onComplete }) {
    const poll = async () => {
      const progress = await dispatch('fetchOperationProgress', progressId)

      if (onProgress) {
        onProgress(progress)
      }

      // 如果操作完成或失败，停止轮询
      if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
        if (onComplete) {
          onComplete(progress)
        }
        return progress
      }

      // 继续轮询 (1秒间隔)
      await new Promise((resolve) => setTimeout(resolve, 1000))
      return poll()
    }

    return poll()
  },

  // 清除所有状态
  clearAll({ commit }) {
    commit('CLEAR_ALL_SELECTIONS')
    commit('CLEAR_OPERATION_STATE')
  },

  // 清除操作状态但保留选择
  clearOperation({ commit }) {
    commit('CLEAR_OPERATION_STATE')
  },
}

// Export
export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions,
}
