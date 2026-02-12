/**
 * Jest 测试环境设置文件
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 * 修复日期: 2026-02-12
 *
 * 完整的 Jest 测试环境配置，包含：
 * - Vue Test Utils 全局配置和 mock
 * - 环境变量设置
 * - WebSocket mock
 * - 位置和 window mock
 */

// Vue Test Utils 全局配置
const { config } = require('@vue/test-utils');

// 配置全局 stubs
config.stubs.transition = true;
config.stubs.transitionGroup = true;

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    protocol: 'http:',
    host: 'localhost:3000',
    href: 'http://localhost:3000/',
  },
  writable: true,
});

// Mock WebSocket 类
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
  }

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  send() {}

  close() {
    this.readyState = MockWebSocket.CLOSING;
  }

  addEventListener() {}
  removeEventListener() {}
}

// 将 WebSocket 挂载到全局
global.WebSocket = MockWebSocket;

// 全局 window 对象补充
global.window = global.window || {
  location: {
    protocol: 'http:',
    host: 'localhost:3000',
  },
  WebSocket: MockWebSocket,
};

// Mock console 方法避免测试输出污染
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn(),
  log: console.log,
};

// Mock daisyUI 的 $message 全局对象
global.$message = {
  success: jest.fn(),
  error: jest.fn(),
  warning: jest.fn(),
  info: jest.fn(),
};

// 全局测试工具函数
global.flushPromises = () => new Promise((resolve) => setImmediate(resolve));
