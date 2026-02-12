/**
 * Jest 配置文件
 *
 * Epic: Story 12-6, Task #26
 * 创建日期: 2026-02-12
 * 修复日期: 2026-02-12
 *
 * 用于单元测试和组件测试
 */

module.exports = {
  // 测试环境
  testEnvironment: 'jsdom',

  // 模块路径映射
  moduleFileExtensions: ['js', 'json', 'vue'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^~/(.*)$': '<rootDir>/node_modules/$1',
  },

  // 转换器配置
  transform: {
    '^.+\\.vue$': 'vue-jest',
    '^.+\\.js$': ['babel-jest', {
      babelrc: false,
      configFile: false,
      presets: [
        [
          '@babel/preset-env',
          {
            modules: 'auto',
            targets: {
              node: 'current',
            },
          },
        ],
      ],
    }],
  },

  // 忽略转换的文件（src Vue 组件由 vue-jest 处理）
  transformIgnorePatterns: [
    '<rootDir>/node_modules/',
  ],

  // 测试文件匹配模式
  testMatch: [
    '**/tests/unit/**/*.test.js',
    '**/__tests__/**/*.test.js',
  ],

  // 设置文件
  setupFiles: ['<rootDir>/tests/setup.js'],

  // 测试环境文件
  testEnvironmentOptions: {
    customExportConditions: ['node', 'node-addons'],
  },

  // 覆盖率收集
  collectCoverageFrom: [
    'src/**/*.{js,vue}',
    '!src/main.js',
    '!src/router/index.js',
    '!**/node_modules/**',
  ],

  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },

  // 覆盖率报告格式
  coverageReporters: ['text', 'html', 'lcov'],

  // 测试超时时间
  testTimeout: 10000,

  // 清除模拟
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
};
