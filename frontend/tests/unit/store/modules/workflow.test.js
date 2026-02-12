/**
 * Workflow Vuex 模块单元测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 *
 * 测试范围:
 * - State 初始化
 * - Mutations 状态变更
 * - Actions 异步操作
 * - Getters 派生状态
 */

import workflow from '@/store/modules/workflow';
import chaptersApi from '@/services/api/chapters';

// Mock API
jest.mock('@/services/api/chapters', () => ({
  startWorkflow: jest.fn(),
  pauseWorkflow: jest.fn(),
  resumeWorkflow: jest.fn(),
  getWorkflowStatus: jest.fn(),
  get: jest.fn(),
  getScenes: jest.fn(),
}));

describe('Workflow Vuex Module', () => {
  let state;

  beforeEach(() => {
    // 重置状态
    state = {
      currentWorkflow: null,
      status: 'idle',
      progress: 0,
      currentScene: null,
      events: [],
      isConnected: false,
      chapter: null,
      scenes: [],
    };
    jest.clearAllMocks();
  });

  describe('State', () => {
    it('应该初始化为空状态', () => {
      const newState = workflow.state;
      expect(newState.currentWorkflow).toBeNull();
      expect(newState.status).toBe('idle');
      expect(newState.progress).toBe(0);
      expect(newState.currentScene).toBeNull();
      expect(newState.events).toEqual([]);
      expect(newState.isConnected).toBe(false);
      expect(newState.chapter).toBeNull();
      expect(newState.scenes).toEqual([]);
    });
  });

  describe('Mutations', () => {
    it('SET_WORKFLOW 应该设置当前工作流', () => {
      const workflowData = { workflow_id: 'wf-123', status: 'running' };
      workflow.mutations.SET_WORKFLOW(state, workflowData);

      expect(state.currentWorkflow).toEqual(workflowData);
    });

    it('SET_STATUS 应该设置状态', () => {
      workflow.mutations.SET_STATUS(state, 'running');

      expect(state.status).toBe('running');
    });

    it('SET_PROGRESS 应该设置进度', () => {
      workflow.mutations.SET_PROGRESS(state, 75);

      expect(state.progress).toBe(75);
    });

    it('SET_CURRENT_SCENE 应该设置当前场景', () => {
      const sceneData = { id: 1, title: '场景1' };
      workflow.mutations.SET_CURRENT_SCENE(state, sceneData);

      expect(state.currentScene).toEqual(sceneData);
    });

    it('ADD_EVENT 应该添加事件到开头', () => {
      const event1 = { type: 'test1' };
      const event2 = { type: 'test2' };

      workflow.mutations.ADD_EVENT(state, event1);
      workflow.mutations.ADD_EVENT(state, event2);

      expect(state.events).toHaveLength(2);
      expect(state.events[0]).toMatchObject(event2);
      expect(state.events[1]).toMatchObject(event1);
      expect(state.events[0]).toHaveProperty('timestamp');
    });

    it('SET_CONNECTED 应该设置连接状态', () => {
      workflow.mutations.SET_CONNECTED(state, true);

      expect(state.isConnected).toBe(true);
    });

    it('SET_CHAPTER 应该设置章节数据', () => {
      const chapterData = { id: 1, title: '第一章' };
      workflow.mutations.SET_CHAPTER(state, chapterData);

      expect(state.chapter).toEqual(chapterData);
    });

    it('SET_SCENES 应该设置场景列表', () => {
      const scenesData = [
        { id: 1, title: '场景1' },
        { id: 2, title: '场景2' },
      ];
      workflow.mutations.SET_SCENES(state, scenesData);

      expect(state.scenes).toEqual(scenesData);
    });

    it('RESET_STATE 应该重置所有状态', () => {
      // 先设置一些值
      state.currentWorkflow = { workflow_id: 'test' };
      state.status = 'running';
      state.progress = 50;
      state.currentScene = { id: 1 };
      state.events = [{ type: 'test' }];
      state.isConnected = true;
      state.chapter = { id: 1 };
      state.scenes = [{ id: 1 }];

      // 重置
      workflow.mutations.RESET_STATE(state);

      expect(state.currentWorkflow).toBeNull();
      expect(state.status).toBe('idle');
      expect(state.progress).toBe(0);
      expect(state.currentScene).toBeNull();
      expect(state.events).toEqual([]);
      expect(state.isConnected).toBe(false);
      expect(state.chapter).toBeNull();
      expect(state.scenes).toEqual([]);
    });
  });

  describe('Actions', () => {
    let commit;

    beforeEach(() => {
      commit = jest.fn();
    });

    it('startWorkflow 应该启动工作流', async () => {
      const workflowData = { workflow_id: 'wf-123' };
      chaptersApi.startWorkflow.mockResolvedValue(workflowData);

      await workflow.actions.startWorkflow({ commit }, 123);

      expect(commit).toHaveBeenCalledWith('SET_STATUS', 'starting');
      expect(chaptersApi.startWorkflow).toHaveBeenCalledWith(123);
      expect(commit).toHaveBeenCalledWith('SET_WORKFLOW', workflowData);
      expect(commit).toHaveBeenCalledWith('SET_STATUS', 'running');
    });

    it('pauseWorkflow 应该暂停工作流', async () => {
      const stateWithWorkflow = { currentWorkflow: { workflow_id: 'wf-123' } };
      chaptersApi.pauseWorkflow.mockResolvedValue({});

      await workflow.actions.pauseWorkflow({ commit, state: stateWithWorkflow });

      expect(chaptersApi.pauseWorkflow).toHaveBeenCalledWith('wf-123');
      expect(commit).toHaveBeenCalledWith('SET_STATUS', 'paused');
    });

    it('pauseWorkflow 在无工作流时应该不执行', async () => {
      const stateWithoutWorkflow = { currentWorkflow: null };
      chaptersApi.pauseWorkflow.mockResolvedValue({});

      await workflow.actions.pauseWorkflow({ commit, state: stateWithoutWorkflow });

      expect(chaptersApi.pauseWorkflow).not.toHaveBeenCalled();
    });

    it('resumeWorkflow 应该继续工作流', async () => {
      const stateWithWorkflow = { currentWorkflow: { workflow_id: 'wf-123' } };
      chaptersApi.resumeWorkflow.mockResolvedValue({});

      await workflow.actions.resumeWorkflow({ commit, state: stateWithWorkflow });

      expect(chaptersApi.resumeWorkflow).toHaveBeenCalledWith('wf-123');
      expect(commit).toHaveBeenCalledWith('SET_STATUS', 'running');
    });

    it('fetchWorkflowStatus 应该获取工作流状态', async () => {
      const workflowData = { workflow_id: 'wf-123', status: 'running' };
      chaptersApi.getWorkflowStatus.mockResolvedValue(workflowData);

      await workflow.actions.fetchWorkflowStatus({ commit }, 123);

      expect(chaptersApi.getWorkflowStatus).toHaveBeenCalledWith(123);
      expect(commit).toHaveBeenCalledWith('SET_WORKFLOW', workflowData);
    });

    it('addEvent 应该添加事件', () => {
      const event = { type: 'test_event', data: 'test' };

      workflow.actions.addEvent({ commit }, event);

      expect(commit).toHaveBeenCalledWith('ADD_EVENT', event);
    });

    it('updateProgress 应该更新进度', () => {
      workflow.actions.updateProgress({ commit }, 80);

      expect(commit).toHaveBeenCalledWith('SET_PROGRESS', 80);
    });

    it('setConnected 应该设置连接状态', () => {
      workflow.actions.setConnected({ commit }, true);

      expect(commit).toHaveBeenCalledWith('SET_CONNECTED', true);
    });

    it('resetState 应该重置状态', () => {
      workflow.actions.resetState({ commit });

      expect(commit).toHaveBeenCalledWith('RESET_STATE');
    });
  });

  describe('Namespaced', () => {
    it('应该启用命名空间', () => {
      expect(workflow.namespaced).toBe(true);
    });
  });
});
