import { apiClient } from '@/services/apiClient';
import chaptersApi from '@/services/api/chapters';

/**
 * Workflow Vuex 模块
 *
 * 职责管理章节工作流的状态：
 * - currentWorkflow: 当前工作流对象
 * - status: 工作流状态 (idle/running/paused/completed/failed)
 * - progress: 进度百分比 (0-100)
 * - currentScene: 当前处理的场景
 * - events: 工作流事件日志
 * - isConnected: WebSocket 连接状态
 * - chapter: 章节数据
 * - scenes: 场景列表
 */
const state = {
  currentWorkflow: null,      // 当前工作流对象
  status: 'idle',            // idle/running/paused/completed/failed
  progress: 0,               // 进度百分比 (0-100)
  currentScene: null,         // 当前处理的场景
  events: [],                 // 工作流事件日志
  isConnected: false,         // WebSocket 连接状态

  // 章节数据和场景列表
  chapter: null,
  scenes: [],
};

const actions = {
  /**
   * 启动工作流
   */
  async startWorkflow({ commit }, chapterId) {
    commit('SET_STATUS', 'starting');
    const workflow = await chaptersApi.startWorkflow(chapterId);
    commit('SET_WORKFLOW', workflow);
    commit('SET_STATUS', 'running');
  },

  /**
   * 暂停工作流
   */
  async pauseWorkflow({ commit, state }) {
    const workflowId = state.currentWorkflow?.workflow_id;
    if (!workflowId) return;

    await chaptersApi.pauseWorkflow(workflowId);
    commit('SET_STATUS', 'paused');
  },

  /**
   * 继续工作流
   */
  async resumeWorkflow({ commit, state }) {
    const workflowId = state.currentWorkflow?.workflow_id;
    if (!workflowId) return;

    await chaptersApi.resumeWorkflow(workflowId);
    commit('SET_STATUS', 'running');
  },

  /**
   * 获取工作流状态
   */
  async fetchWorkflowStatus({ commit }, chapterId) {
    const workflow = await chaptersApi.getWorkflowStatus(chapterId);
    commit('SET_WORKFLOW', workflow);
  },

  /**
   * 添加工作流事件
   */
  addEvent({ commit }, event) {
    commit('ADD_EVENT', event);
  },

  /**
   * 更新进度
   */
  updateProgress({ commit }, progress) {
    commit('SET_PROGRESS', progress);
  },

  /**
   * 设置 WebSocket 连接状态
   */
  setConnected({ commit }, isConnected) {
    commit('SET_CONNECTED', isConnected);
  },

  /**
   * 重置状态
   */
  resetState({ commit }) {
    commit('RESET_STATE');
  },
};

const mutations = {
  SET_WORKFLOW(state, workflow) {
    state.currentWorkflow = workflow;
  },

  SET_STATUS(state, status) {
    state.status = status;
  },

  SET_PROGRESS(state, progress) {
    state.progress = progress;
  },

  SET_CURRENT_SCENE(state, scene) {
    state.currentScene = scene;
  },

  ADD_EVENT(state, event) {
    state.events.unshift({
      ...event,
      timestamp: new Date().toISOString(),
    });
  },

  SET_CONNECTED(state, isConnected) {
    state.isConnected = isConnected;
  },

  /**
   * 设置章节数据
   */
  SET_CHAPTER(state, chapter) {
    state.chapter = chapter;
  },

  /**
   * 设置场景列表
   */
  SET_SCENES(state, scenes) {
    state.scenes = scenes;
  },

  /**
   * 重置状态
   */
  RESET_STATE(state) {
    Object.assign(state, {
      currentWorkflow: null,
      status: 'idle',
      progress: 0,
      currentScene: null,
      events: [],
      isConnected: false,

      // 重置章节数据和场景列表
      chapter: null,
      scenes: [],
    });
  },
};

export default {
  namespaced: true,
  state,
  actions,
  mutations,
};
