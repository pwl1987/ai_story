/**
 * API 配置单元测试
 *
 * Epic: Story 12-6
 * 创建日期: 2026-02-12
 * 修复日期: 2026-02-12
 *
 * 测试范围:
 * - API URL 生成
 * - WebSocket URL 生成
 * - 环境变量覆盖
 */

import { API_CONFIG, getAPIUrl, getWebSocketURL } from '@/config/api';

describe('API Configuration', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    // 重置环境变量
    process.env = { ...originalEnv };
    delete process.env.VUE_APP_API_URL;
    delete process.env.VUE_APP_WS_URL;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('API_CONFIG', () => {
    it('应该有默认的 baseURL', () => {
      expect(API_CONFIG.baseURL).toBe('/api/v1');
    });

    it('应该有默认的 wsURL', () => {
      expect(API_CONFIG.wsURL).toBe('ws://localhost:8000');
    });

    it('应该定义所有必要的端点', () => {
      expect(API_CONFIG.endpoints.chapters).toBeDefined();
      expect(API_CONFIG.endpoints.scenes).toBeDefined();
      expect(API_CONFIG.endpoints.workflow).toBeDefined();
      expect(API_CONFIG.endpoints.frames).toBeDefined();
    });

    it('应该支持环境变量覆盖 baseURL', () => {
      process.env.VUE_APP_API_URL = 'https://api.example.com';
      jest.resetModules();
      const { API_CONFIG: overriddenConfig } = require('@/config/api');

      expect(overriddenConfig.baseURL).toBe('https://api.example.com');
    });

    it('应该支持环境变量覆盖 wsURL', () => {
      process.env.VUE_APP_WS_URL = 'wss://api.example.com';
      jest.resetModules();
      const { API_CONFIG: overriddenConfig } = require('@/config/api');

      expect(overriddenConfig.wsURL).toBe('wss://api.example.com');
    });
  });

  describe('getAPIUrl', () => {
    it('应该正确拼接完整 URL', () => {
      const result = getAPIUrl('/artworks/chapters');
      expect(result).toBe('/api/v1/artworks/chapters');
    });

    it('应该处理无前导斜杠的端点', () => {
      const result = getAPIUrl('/artworks/chapters');
      expect(result).toBe('/api/v1/artworks/chapters');
      expect(result).toContain('artworks/chapters');
    });
  });
});
