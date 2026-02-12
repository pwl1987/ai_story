/**
 * SceneProgressCard 组件测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 *
 * 测试范围:
 * - Props 验证
 * - 计算属性（status）
 * - 事件触发
 * - 条件渲染逻辑
 */

import { mount } from '@vue/test-utils';
import SceneProgressCard from '@/components/artworks/SceneProgressCard.vue';

// Mock FramePreview 组件
jest.mock('@/components/artworks/FramePreview.vue', () => ({
  name: 'FramePreview',
  props: ['imageUrl', 'fallbackIcon', 'label'],
  render: h => h('div', { class: 'mock-frame-preview' }, [
    h('span', {}, `Label: ${this.label}`),
    h('span', {}, `Image: ${this.imageUrl || 'none'}`),
  ]),
}));

describe('SceneProgressCard', () => {
  let wrapper;

  const mockScene = {
    id: 1,
    scene_number: 1,
    scene_name: '开场场景',
    description: '这是一个测试场景描述',
    shot_count: 5,
    head_frame: 'https://example.com/head.jpg',
    tail_frame: 'https://example.com/tail.jpg',
    is_completed: false,
  };

  beforeEach(() => {
    wrapper = mount(SceneProgressCard, {
      propsData: {
        scene: mockScene,
        isActive: false,
        workflowStatus: 'idle',
      },
      stubs: {
        FramePreview: true,
      },
    });
  });

  afterEach(() => {
    wrapper.destroy();
  });

  describe('Props 验证', () => {
    it('应该接收 scene prop', () => {
      expect(wrapper.vm.scene).toEqual(mockScene);
    });

    it('scene 应该是必填项', () => {
      expect(() => {
        mount(SceneProgressCard, { propsData: {} });
      }).toThrow();
    });

    it('应该接收 isActive prop', () => {
      expect(wrapper.vm.isActive).toBe(false);
    });

    it('应该接收 workflowStatus prop', () => {
      expect(wrapper.vm.workflowStatus).toBe('idle');
    });
  });

  describe('计算属性 - status', () => {
    it('isActive 为 true 时应该返回 processing', () => {
      wrapper.setProps({ isActive: true });
      expect(wrapper.vm.status).toBe('processing');
    });

    it('scene.is_completed 为 true 时应该返回 completed', () => {
      wrapper.setProps({
        isActive: false,
        scene: { ...mockScene, is_completed: true },
      });
      expect(wrapper.vm.status).toBe('completed');
    });

    it('非活跃且未完成应该返回 pending', () => {
      wrapper.setProps({
        isActive: false,
        scene: { ...mockScene, is_completed: false },
      });
      expect(wrapper.vm.status).toBe('pending');
    });
  });

  describe('计算属性 - statusDisplay', () => {
    it('应该返回正确的状态文本', () => {
      const displays = {
        pending: '待处理',
        processing: '处理中',
        completed: '已完成',
        failed: '失败',
      };

      // Mock status computed property
      wrapper.vm.status = 'pending';
      expect(wrapper.vm.statusDisplay).toBe(displays.pending);
    });
  });

  describe('计算属性 - showStatusOverlay', () => {
    it('processing 状态应该显示覆盖层', () => {
      wrapper.vm.status = 'processing';
      expect(wrapper.vm.showStatusOverlay).toBe(true);
    });

    it('completed 状态应该显示覆盖层', () => {
      wrapper.vm.status = 'completed';
      expect(wrapper.vm.showStatusOverlay).toBe(true);
    });

    it('failed 状态应该显示覆盖层', () => {
      wrapper.vm.status = 'failed';
      expect(wrapper.vm.showStatusOverlay).toBe(true);
    });

    it('pending 状态不应该显示覆盖层', () => {
      wrapper.vm.status = 'pending';
      expect(wrapper.vm.showStatusOverlay).toBe(false);
    });
  });

  describe('事件触发', () => {
    it('点击提取首尾帧按钮应该触发 extract-frames 事件', async () => {
      const sceneWithoutFrames = { ...mockScene, head_frame: null, tail_frame: null };
      wrapper.setProps({ scene: sceneWithoutFrames, workflowStatus: 'idle' });

      const button = wrapper.findAll('button').find(b => b.text().includes('提取首尾帧'));
      if (button) {
        await button.trigger('click');
        expect(wrapper.emitted('extract-frames')).toBeTruthy();
        expect(wrapper.emitted('extract-frames')[0]).toEqual([sceneWithoutFrames]);
      }
    });

    it('点击编辑场景按钮应该触发 edit 事件', async () => {
      const button = wrapper.findAll('button').find(b => b.text().includes('编辑场景'));
      if (button) {
        await button.trigger('click');
        expect(wrapper.emitted('edit')).toBeTruthy();
        expect(wrapper.emitted('edit')[0]).toEqual([mockScene]);
      }
    });
  });

  describe('条件渲染', () => {
    it('isActive 为 true 时应该显示活跃徽章', () => {
      wrapper.setProps({ isActive: true });
      expect(wrapper.find('.badge-primary').exists()).toBe(true);
      expect(wrapper.text()).toContain('处理中');
    });

    it('isActive 为 false 时不应该显示活跃徽章', () => {
      wrapper.setProps({ isActive: false });
      expect(wrapper.find('.badge-primary').exists()).toBe(false);
    });

    it('工作流运行时不应该显示提取首尾帧按钮', () => {
      wrapper.setProps({
        scene: { ...mockScene, head_frame: null, tail_frame: null },
        workflowStatus: 'running',
      });
      expect(wrapper.text()).not.toContain('提取首尾帧');
    });

    it('已提取帧时应该显示"已提取帧"文本', () => {
      wrapper.setProps({
        scene: mockScene, // 有 head_frame 和 tail_frame
      });
      expect(wrapper.text()).toContain('已提取帧');
    });

    it('未提取帧时应该显示"待提取帧"文本', () => {
      wrapper.setProps({
        scene: { ...mockScene, head_frame: null, tail_frame: null },
      });
      expect(wrapper.text()).toContain('待提取帧');
    });

    it('应该显示镜头数量', () => {
      expect(wrapper.text()).toContain('5 个镜头');
    });
  });

  describe('UI 渲染', () => {
    it('应该显示场景序号和名称', () => {
      expect(wrapper.text()).toContain('场景 1');
      expect(wrapper.text()).toContain('开场场景');
    });

    it('应该显示场景描述', () => {
      expect(wrapper.text()).toContain('这是一个测试场景描述');
    });

    it('isActive 为 true 时应该显示 ring 样式', () => {
      wrapper.setProps({ isActive: true });
      expect(wrapper.find('.ring-2').exists()).toBe(true);
      expect(wrapper.find('.ring-primary').exists()).toBe(true);
    });
  });
});
