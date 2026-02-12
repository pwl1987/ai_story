/**
 * Babel 配置文件
 *
 * Epic: Story 12-6, Task #26
 * 创建日期: 2026-02-12
 * 修复日期: 2026-02-12
 *
 * 为 Jest 和 webpack 提供统一的 Babel 配置
 */

module.exports = function (api) {
  const isTest = api.caller(caller => caller?.name === 'babel-jest');

  const presets = [
    [
      '@babel/preset-env',
      {
        modules: isTest ? 'auto' : false,
        targets: {
          node: isTest ? 'current' : '16',
          browsers: isTest ? undefined : ['>1%', 'last 2 versions', 'not ie <= 8'],
        },
      },
    ],
  ];

  return {
    presets,
  };
};
