/**
 * WorkflowControlPanel 组件测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 *
 * 测试范围:
 * - Props 验证
 * - 计算属性逻辑
 * - 事件触发
 * - 按钮显示逻辑
 */

import { mount } from '@vue/test-utils';
import WorkflowControlPanel from '@/components/artworks/WorkflowControlPanel.vue';

describe('WorkflowControlPanel', () => {
  let wrapper;

  const defaultProps = {
    totalScenes: 10,
    completedScenes: 5,
    progress: 50,
    status: 'running',
    currentScene: { id: 1, title: '场景1' },
    isLoading: false,
  };

  beforeEach(() => {
    wrapper = mount(WorkflowControlPanel, {
      propsData: defaultProps,
    });
  });

  afterEach(() => {
    wrapper.destroy();
  });

  describe('Props 验证', () => {
    it('应该接收 status prop', () => {
      expect(wrapper.vm.status).toBe('running');
    });

    it('应该接收 progress prop', () => {
      expect(wrapper.vm.progress).toBe(50);
    });

    it('应该接收 currentScene prop', () => {
      expect(wrapper.vm.currentScene).toEqual({ id: 1, title: '场景1' });
    });

    it('应该接收 totalScenes prop', () => {
      expect(wrapper.vm.totalScenes).toBe(10);
    });

    it('应该接收 completedScenes prop', () => {
      expect(wrapper.vm.completedScenes).toBe(5);
    });

    it('应该接收 isLoading prop', () => {
      expect(wrapper.vm.isLoading).toBe(false);
    });

    it('应该验证 status prop 的值', () => {
      const validator = WorkflowControlPanel.props.status.validator;
      expect(validator('idle')).toBe(true);
      expect(validator('running')).toBe(true);
      expect(validator('paused')).toBe(true);
      expect(validator('completed')).toBe(true);
      expect(validator('failed')).toBe(true);
      expect(validator('invalid')).toBe(false);
    });
  });

  describe('计算属性', () => {
    it('statusDisplay 应该返回正确的状态文本', () => {
      const displays = {
        idle: '待处理',
        running: '运行中',
        paused: '已暂停',
        completed: '已完成',
        failed: '失败',
      };

      Object.entries(displays).forEach(([status, display]) => {
        wrapper.setProps({ status });
        expect(wrapper.vm.statusDisplay).toBe(display);
      });
    });

    it('statusBadgeClass 应该返回正确的样式类', () => {
      const classes = {
        idle: 'badge-ghost',
        running: 'badge-primary',
        paused: 'badge-warning',
        completed: 'badge-success',
        failed: 'badge-error',
      };

      Object.entries(classes).forEach(([status, className]) => {
        wrapper.setProps({ status });
        expect(wrapper.vm.statusBadgeClass).toBe(className);
      });
    });

    it('canStart 应该在 idle/completed/failed 状态时为 true', () => {
      ['idle', 'completed', 'failed'].forEach(status => {
        wrapper.setProps({ status });
        expect(wrapper.vm.canStart).toBe(true);
      });
    });

    it('canStart 应该在 running/paused 状态时为 false', () => {
      ['running', 'paused'].forEach(status => {
        wrapper.setProps({ status });
        expect(wrapper.vm.canStart).toBe(false);
      });
    });

    it('canPause 应该仅在 running 状态时为 true', () => {
      wrapper.setProps({ status: 'running' });
      expect(wrapper.vm.canPause).toBe(true);

      wrapper.setProps({ status: 'idle' });
      expect(wrapper.vm.canPause).toBe(false);
    });

    it('canResume 应该仅在 paused 状态时为 true', () => {
      wrapper.setProps({ status: 'paused' });
      expect(wrapper.vm.canResume).toBe(true);

      wrapper.setProps({ status: 'running' });
      expect(wrapper.vm.canResume).toBe(false);
    });

    it('canRetry 应该仅在 failed 状态时为 true', () => {
      wrapper.setProps({ status: 'failed' });
      expect(wrapper.vm.canRetry).toBe(true);

      wrapper.setProps({ status: 'idle' });
      expect(wrapper.vm.canRetry).toBe(false);
    });

    it('completedCount 应该返回 completedScenes 或 0', () => {
      wrapper.setProps({ completedScenes: 5 });
      expect(wrapper.vm.completedCount).toBe(5);

      wrapper.setProps({ completedScenes: undefined });
      expect(wrapper.vm.completedCount).toBe(0);
    });
  });

  describe('事件触发', () => {
    it('点击启动按钮应该触发 start 事件', async () => {
      wrapper.setProps({ status: 'idle' });
      await wrapper.find('.btn-primary').trigger('click');
      expect(wrapper.emitted('start')).toBeTruthy();
    });

    it('点击暂停按钮应该触发 pause 事件', async () => {
      wrapper.setProps({ status: 'running' });
      await wrapper.find('.btn-warning').trigger('click');
      expect(wrapper.emitted('pause')).toBeTruthy();
    });

    it('点击继续按钮应该触发 resume 事件', async () => {
      wrapper.setProps({ status: 'paused' });
      await wrapper.find('.btn-success').trigger('click');
      expect(wrapper.emitted('resume')).toBeTruthy();
    });

    it('点击重试按钮应该触发 retry 事件', async () => {
      wrapper.setProps({ status: 'failed' });
      await wrapper.find('.btn-error').trigger('click');
      expect(wrapper.emitted('retry')).toBeTruthy();
    });
  });

  describe('按钮禁用状态', () => {
    it('isLoading 为 true 时应该禁用启动按钮', async () => {
      wrapper.setProps({ status: 'idle', isLoading: true });
      const button = wrapper.find('.btn-primary');
      expect(button.attributes('disabled')).toBeDefined();
    });

    it('isLoading 为 true 时应该禁用暂停按钮', async () => {
      wrapper.setProps({ status: 'running', isLoading: true });
      const button = wrapper.find('.btn-warning');
      expect(button.attributes('disabled')).toBeDefined();
    });

    it('isLoading 为 true 时应该显示加载动画', async () => {
      wrapper.setProps({ status: 'idle', isLoading: true });
      const button = wrapper.find('.btn-primary');
      expect(button.classes()).toContain('loading');
    });
  });

  describe('UI 渲染', () => {
    it('应该显示进度条和进度百分比', () => {
      wrapper.setProps({ progress: 75 });
      expect(wrapper.find('.progress').attributes('value')).toBe('75');
      expect(wrapper.text()).toContain('75%');
    });

    it('应该显示已完成场景统计', () => {
      wrapper.setProps({ totalScenes: 20, completedScenes: 10 });
      expect(wrapper.text()).toContain('10 / 20 场景已完成');
    });

    it('应该在有 currentScene 时显示场景信息', () => {
      wrapper.setProps({ currentScene: { id: 1, title: '测试场景' } });
      expect(wrapper.text()).toContain('测试场景');
    });

    it('应该在无 currentScene 时不显示场景信息', () => {
      wrapper.setProps({ currentScene: null });
      const sceneSection = wrapper.findAll('[class*="mb-4"]').filter(
        w => w.text().includes('当前处理')
      );
      expect(sceneSection).toHaveLength(0);
    });
  });
});
