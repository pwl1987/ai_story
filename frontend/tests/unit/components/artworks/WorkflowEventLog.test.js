/**
 * WorkflowEventLog 组件测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 *
 * 测试范围:
 * - Props 验证
 * - 事件排序
 * - 时间格式化
 * - 清空事件触发
 */

import { mount } from '@vue/test-utils';
import WorkflowEventLog from '@/components/artworks/WorkflowEventLog.vue';

describe('WorkflowEventLog', () => {
  let wrapper;

  const mockEvents = [
    {
      id: 1,
      type: 'workflow_started',
      timestamp: '2026-02-12T10:00:00Z',
      message: '工作流已启动',
    },
    {
      id: 2,
      type: 'scene_started',
      timestamp: '2026-02-12T10:05:00Z',
      message: '开始处理场景1',
      metadata: { scene_id: 1 },
    },
    {
      id: 3,
      type: 'scene_completed',
      timestamp: '2026-02-12T10:10:00Z',
      message: '场景1处理完成',
      metadata: { scene_id: 1, progress: 50 },
    },
  ];

  beforeEach(() => {
    wrapper = mount(WorkflowEventLog, {
      propsData: {
        events: [...mockEvents],
      },
    });
  });

  afterEach(() => {
    wrapper.destroy();
  });

  describe('Props 验证', () => {
    it('应该接收 events prop', () => {
      expect(wrapper.vm.events).toEqual(mockEvents);
    });

    it('events 默认值应该是空数组', () => {
      const defaultWrapper = mount(WorkflowEventLog);
      expect(defaultWrapper.vm.events).toEqual([]);
      defaultWrapper.destroy();
    });

    it('应该验证 events 是否为数组', () => {
      const validator = WorkflowEventLog.props.events.validator;
      expect(validator([])).toBe(true);
      expect(validator({})).toBe(false);
      expect(validator('string')).toBe(false);
      expect(validator(null)).toBe(false);
    });
  });

  describe('计算属性 - sortedEvents', () => {
    it('应该按时间戳降序排序事件', () => {
      const sorted = wrapper.vm.sortedEvents;
      expect(sorted[0].id).toBe(3); // 最新的在前
      expect(sorted[1].id).toBe(2);
      expect(sorted[2].id).toBe(1); // 最旧的在后
    });

    it('空事件列表应该返回空数组', () => {
      wrapper.setProps({ events: [] });
      expect(wrapper.vm.sortedEvents).toEqual([]);
    });
  });

  describe('方法 - eventTitle', () => {
    it('应该返回正确的事件标题', () => {
      const titles = {
        workflow_started: '工作流已启动',
        workflow_completed: '工作流已完成',
        workflow_failed: '工作流失败',
        workflow_paused: '工作流已暂停',
        workflow_resumed: '工作流已继续',
        scene_started: '场景处理开始',
        scene_completed: '场景处理完成',
        scene_failed: '场景处理失败',
        frames_extracted: '首尾帧已提取',
        error: '错误',
      };

      Object.entries(titles).forEach(([type, title]) => {
        expect(wrapper.vm.eventTitle({ type })).toBe(title);
      });
    });

    it('未知事件类型应该返回原始类型', () => {
      const unknownEvent = { type: 'unknown_type' };
      expect(wrapper.vm.eventTitle(unknownEvent)).toBe('unknown_type');
    });
  });

  describe('方法 - formatTime', () => {
    beforeEach(() => {
      jest.useFakeTimers().setSystemTime(new Date('2026-02-12T10:30:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('应该显示"刚刚"（小于1分钟）', () => {
      const timestamp = '2026-02-12T10:29:30Z';
      expect(wrapper.vm.formatTime(timestamp)).toBe('刚刚');
    });

    it('应该显示"X分钟前"（小于1小时）', () => {
      const timestamp = '2026-02-12T10:00:00Z';
      expect(wrapper.vm.formatTime(timestamp)).toBe('30分钟前');
    });

    it('应该显示"X小时前"（小于24小时）', () => {
      const timestamp = '2026-02-12T08:00:00Z';
      expect(wrapper.vm.formatTime(timestamp)).toBe('2小时前');
    });

    it('应该显示完整日期时间（超过24小时）', () => {
      const timestamp = '2026-02-10T10:00:00Z';
      expect(wrapper.vm.formatTime(timestamp)).toBe('2026-02-10 10:00');
    });

    it('空时间戳应该返回空字符串', () => {
      expect(wrapper.vm.formatTime(null)).toBe('');
      expect(wrapper.vm.formatTime('')).toBe('');
    });
  });

  describe('方法 - handleClear', () => {
    it('应该触发 clear 事件', async () => {
      wrapper.setProps({ events: mockEvents });
      const clearButton = wrapper.find('button');
      await clearButton.trigger('click');

      expect(wrapper.emitted('clear')).toBeTruthy();
    });
  });

  describe('UI 渲染', () => {
    it('空事件列表应该显示"暂无事件"', () => {
      wrapper.setProps({ events: [] });
      expect(wrapper.text()).toContain('暂无事件');
    });

    it('有事件时不应该显示"暂无事件"', () => {
      expect(wrapper.text()).not.toContain('暂无事件');
    });

    it('应该渲染所有事件', () => {
      const eventElements = wrapper.findAll('[class*="p-3"]');
      expect(eventElements.length).toBeGreaterThan(0);
    });

    it('应该显示事件消息', () => {
      expect(wrapper.text()).toContain('工作流已启动');
      expect(wrapper.text()).toContain('开始处理场景1');
    });

    it('应该显示场景 ID 徽章', () => {
      expect(wrapper.text()).toContain('场景 #1');
    });

    it('应该显示进度徽章', () => {
      expect(wrapper.text()).toContain('50%');
    });

    it('有事件时应该显示清空按钮', () => {
      expect(wrapper.find('button').exists()).toBe(true);
    });

    it('空事件时不应该显示清空按钮', () => {
      wrapper.setProps({ events: [] });
      expect(wrapper.find('button').exists()).toBe(false);
    });
  });

  describe('事件图标', () => {
    it('workflow_started 事件应该显示播放图标', () => {
      const event = { type: 'workflow_started' };
      expect(wrapper.vm.eventTitle(event)).toBe('工作流已启动');
    });

    it('workflow_completed 事件应该显示成功图标', () => {
      const event = { type: 'workflow_completed' };
      expect(wrapper.vm.eventTitle(event)).toBe('工作流已完成');
    });

    it('workflow_failed 事件应该显示错误图标', () => {
      const event = { type: 'workflow_failed' };
      expect(wrapper.vm.eventTitle(event)).toBe('工作流失败');
    });

    it('scene_started 事件应该显示场景图标', () => {
      const event = { type: 'scene_started' };
      expect(wrapper.vm.eventTitle(event)).toBe('场景处理开始');
    });

    it('scene_completed 事件应该显示勾选图标', () => {
      const event = { type: 'scene_completed' };
      expect(wrapper.vm.eventTitle(event)).toBe('场景处理完成');
    });
  });
});
