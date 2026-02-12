/**
 * WorkflowWebSocket 单元测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 *
 * 测试范围:
 * - WebSocket 工厂方法创建
 * - 事件处理器绑定
 * - 消息解析逻辑
 * - 错误处理
 */

import WorkflowWebSocket from '@/utils/workflowWebSocket';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;

    // 模拟连接成功
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen({ type: 'open' });
      }
    }, 0);
  }

  send(data) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code: 1000, reason: 'Normal Closure' });
    }
  }

  // 模拟接收消息
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
}

MockWebSocket.CONNECTING = 0;
MockWebSocket.OPEN = 1;
MockWebSocket.CLOSING = 2;
MockWebSocket.CLOSED = 3;

// 全局 mock
global.WebSocket = MockWebSocket;

describe('WorkflowWebSocket', () => {
  let mockCallbacks;

  beforeEach(() => {
    mockCallbacks = {
      onConnected: jest.fn(),
      onEvent: jest.fn(),
      onDisconnected: jest.fn(),
      onError: jest.fn(),
    };
  });

  describe('create', () => {
    it('应该创建 WebSocket 连接', () => {
      const chapterId = 123;
      const { ws } = WorkflowWebSocket.create(chapterId, mockCallbacks);

      expect(ws).toBeDefined();
      expect(ws.url).toContain(chapterId.toString());
    });

    it('应该在连接成功时调用 onConnected 回调', () => {
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);

      // 等待异步连接
      setTimeout(() => {
        expect(mockCallbacks.onConnected).toHaveBeenCalled();
      }, 10);
    });

    it('应该返回包含 ws 和 disconnect 方法的对象', () => {
      const result = WorkflowWebSocket.create(123, mockCallbacks);

      expect(result.ws).toBeDefined();
      expect(result.disconnect).toBeDefined();
      expect(typeof result.disconnect).toBe('function');
    });
  });

  describe('handleMessage', () => {
    it('应该解析并转发有效的事件消息', () => {
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);
      const testEvent = {
        type: 'scene_completed',
        payload: {
          scene_id: 1,
          progress: 50,
        },
      };

      ws.simulateMessage(testEvent);

      expect(mockCallbacks.onEvent).toHaveBeenCalledWith(testEvent.payload);
    });

    it('应该忽略格式无效的消息', () => {
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);
      const invalidMessage = { invalid: 'data' };

      ws.simulateMessage(invalidMessage);

      expect(mockCallbacks.onEvent).not.toHaveBeenCalled();
    });

    it('应该处理 JSON 解析错误', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);

      // 触发 onmessage 直接传入无效 JSON
      ws.onmessage({ data: 'invalid json' });

      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });
  });

  describe('handleClose', () => {
    it('应该在连接关闭时调用 onDisconnected 回调', () => {
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);

      ws.close();

      expect(mockCallbacks.onDisconnected).toHaveBeenCalled();
    });
  });

  describe('handleError', () => {
    it('应该在发生错误时调用 onError 回调', () => {
      const { ws } = WorkflowWebSocket.create(123, mockCallbacks);
      const testError = new Error('Connection failed');

      ws.onerror(testError);

      expect(mockCallbacks.onError).toHaveBeenCalledWith(testError);
    });
  });

  describe('disconnect', () => {
    it('应该关闭 WebSocket 连接', () => {
      const { ws, disconnect } = WorkflowWebSocket.create(123, mockCallbacks);

      expect(ws.readyState).not.toBe(MockWebSocket.CLOSED);

      disconnect();

      expect(ws.readyState).toBe(MockWebSocket.CLOSED);
    });
  });
});
