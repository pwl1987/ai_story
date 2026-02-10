// Progress Vuex Store Module - 进度状态管理

// 阶段定义
const STAGES = [
  { key: "llm", name: "文案改写", stepCount: 1 },
  { key: "storyboard", name: "分镜生成", stepCount: 10 },
  { key: "image", name: "文生图", stepCount: 10 },
  { key: "camera", name: "运镜生成", stepCount: 5 },
  { key: "video", name: "图生视频", stepCount: 3 },
];

// 状态
const state = {
  // 阶段状态
  stages: STAGES.map((stage) => ({
    ...stage,
    progress: 0,
    status: "pending", // pending, active, completed, error
    currentStep: 0,
    stepName: null,
    error: null,
  })),

  // 当前阶段
  currentStageKey: null,

  // 错误列表
  errors: [],

  // 历史平均耗时（秒）- 从后端获取
  stageDurations: {
    llm: 60,
    storyboard: 120,
    image: 300,
    camera: 180,
    video: 600,
  },

  // 任务开始时间
  taskStartTime: null,
};

// Getters
const getters = {
  // 当前阶段
  currentStage: (state) => {
    if (!state.currentStageKey) return null;
    return state.stages.find((s) => s.key === state.currentStageKey);
  },

  // 已完成阶段
  completedStages: (state) => {
    return state.stages.filter((s) => s.status === "completed");
  },

  // 进行中阶段
  activeStages: (state) => {
    return state.stages.filter((s) => s.status === "active");
  },

  // 有错误的阶段
  errorStages: (state) => {
    return state.stages.filter((s) => s.status === "error");
  },

  // 总体进度百分比
  overallProgress: (state) => {
    if (!state.stages.length) return 0;
    const totalProgress = state.stages.reduce((sum, s) => sum + (s.progress || 0), 0);
    return Math.round(totalProgress / state.stages.length);
  },

  // 是否所有阶段完成
  isAllCompleted: (state, getters) => {
    return getters.overallProgress === 100;
  },

  // 是否有错误
  hasErrors: (state) => {
    return state.errors.length > 0 || state.stages.some((s) => s.status === "error");
  },

  // 当前阶段进度百分比
  currentStageProgress: (state, getters) => {
    const current = getters.currentStage;
    return current ? current.progress : 0;
  },
};

// Actions
const actions = {
  /**
   * 初始化阶段状态
   */
  initStages({ commit }, projectStages = []) {
    commit("SET_STAGES", projectStages.length > 0 ? projectStages : STAGES);
  },

  /**
   * 重置所有阶段
   */
  resetStages({ commit }) {
    commit("RESET_STAGES");
  },

  /**
   * 更新阶段进度
   */
  updateStageProgress({ commit }, payload) {
    commit("UPDATE_STAGE_PROGRESS", payload);
  },

  /**
   * 设置当前阶段
   */
  setCurrentStage({ commit }, stageKey) {
    commit("SET_CURRENT_STAGE", stageKey);
  },

  /**
   * 完成阶段
   */
  completeStage({ commit, dispatch }, stageKey) {
    commit("COMPLETE_STAGE", stageKey);
    // 自动进入下一阶段
    dispatch("moveToNextStage", stageKey);
  },

  /**
   * 移动到下一阶段
   */
  moveToNextStage({ commit, state }, completedStageKey) {
    const completedIndex = state.stages.findIndex((s) => s.key === completedStageKey);
    if (completedIndex >= 0 && completedIndex < state.stages.length - 1) {
      const nextStage = state.stages[completedIndex + 1];
      commit("SET_CURRENT_STAGE", nextStage.key);
      commit("SET_STAGE_STATUS", {
        stageKey: nextStage.key,
        status: "active",
      });
    }
  },

  /**
   * 设置阶段错误
   */
  setStageError({ commit }, payload) {
    commit("SET_STAGE_ERROR", payload);
    commit("ADD_ERROR", payload);
  },

  /**
   * 清除错误
   */
  clearErrors({ commit }) {
    commit("CLEAR_ERRORS");
  },

  /**
   * 启动任务计时
   */
  startTask({ commit }) {
    commit("SET_TASK_START_TIME", new Date());
  },

  /**
   * 停止任务计时
   */
  stopTask({ commit }) {
    commit("SET_TASK_START_TIME", null);
  },

  /**
   * 更新阶段耗时配置
   */
  updateStageDurations({ commit }, durations) {
    commit("SET_STAGE_DURATIONS", durations);
  },
};

// Mutations
const mutations = {
  SET_STAGES(state, stages) {
    state.stages = stages.map((s) => ({
      ...s,
      stepName: s.stepName || null,
    }));
  },

  RESET_STAGES(state) {
    state.stages = STAGES.map((stage) => ({
      ...stage,
      progress: 0,
      status: "pending",
      currentStep: 0,
      stepName: null,
      error: null,
    }));
    state.currentStageKey = null;
    state.errors = [];
  },

  UPDATE_STAGE_PROGRESS(state, payload) {
    const stage = state.stages.find((s) => s.key === payload.stageKey);
    if (stage) {
      stage.progress = payload.progress;
      stage.currentStep = payload.currentStep || 0;
      if (payload.status) {
        stage.status = payload.status;
      }
      if (payload.stepName !== undefined) {
        stage.stepName = payload.stepName;
      }
    }
  },

  SET_CURRENT_STAGE(state, stageKey) {
    state.currentStageKey = stageKey;
    // 更新阶段状态
    state.stages.forEach((s) => {
      if (s.key === stageKey) {
        s.status = "active";
      } else if (s.status === "active") {
        s.status = "pending";
      }
    });
  },

  SET_STAGE_STATUS(state, payload) {
    const stage = state.stages.find((s) => s.key === payload.stageKey);
    if (stage) {
      stage.status = payload.status;
    }
  },

  COMPLETE_STAGE(state, stageKey) {
    const stage = state.stages.find((s) => s.key === stageKey);
    if (stage) {
      stage.status = "completed";
      stage.progress = 100;
    }
  },

  SET_STAGE_ERROR(state, payload) {
    const stage = state.stages.find((s) => s.key === payload.stageKey);
    if (stage) {
      stage.status = "error";
      stage.error = payload.error;
    }
  },

  ADD_ERROR(state, error) {
    state.errors.push({
      ...error,
      id: Date.now(),
    });
  },

  CLEAR_ERRORS(state) {
    state.errors = [];
  },

  SET_TASK_START_TIME(state, time) {
    state.taskStartTime = time;
  },

  SET_STAGE_DURATIONS(state, durations) {
    state.stageDurations = { ...state.stageDurations, ...durations };
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
