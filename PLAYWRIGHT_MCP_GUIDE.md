# Playwright MCP 使用指南

## 安装状态

✅ `@playwright/mcp@0.0.64` 已全局安装
- 可执行文件: `/root/.nvm/versions/node/v24.13.0/bin/playwright-mcp`
- Playwright 版本: 1.59.0-alpha

---

## 基本启动命令

### 推荐配置（无沙箱模式）

```bash
# 基本启动（无沙箱，headless 模式）
playwright-mcp --no-sandbox --headless

# 带调试信息的启动
playwright-mcp --no-sandbox --headless --console-level debug

# 指定浏览器和视口大小
playwright-mcp --no-sandbox --browser chrome --viewport-size 1920x1080
```

### 完整启动配置

```bash
# 生产环境配置（推荐）
playwright-mcp \
  --no-sandbox \
  --browser chrome \
  --viewport-size 1920x1080 \
  --console-level info \
  --timeout-action 10000 \
  --timeout-navigation 30000 \
  --save-trace \
  --output-dir /tmp/playwright-output
```

---

## 常用选项说明

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--no-sandbox` | **禁用沙箱（root 用户必需）** | - |
| `--headless` | 无头模式（后台运行） | false |
| `--browser` | 浏览器类型: chrome, firefox, webkit, msedge | chrome |
| `--viewport-size` | 视口大小，如 1920x1080 | - |
| `--console-level` | 控制台日志级别: error, warning, info, debug | info |
| `--timeout-action` | 操作超时（毫秒） | 5000 |
| `--timeout-navigation` | 导航超时（毫秒） | 60000 |
| `--output-dir` | 输出目录 | - |
| `--save-trace` | 保存 Playwright Trace | false |
| `--save-video` | 保存视频，如 800x600 | - |
| `--host` | 绑定主机地址 | localhost |
| `--port` | SSE 传输端口 | - |

---

## 使用场景

### 场景 1: 前端 E2E 测试

```bash
playwright-mcp --no-sandbox --headless --console-level debug
```

### 场景 2: 视觉回归测试

```bash
playwright-mcp --no-sandbox --viewport-size 1920x1080 --save-video 1920x1080
```

### 场景 3: 调试模式

```bash
playwright-mcp --no-sandbox --console-level debug --save-trace
```

### 场景 4: 生产环境测试

```bash
playwright-mcp \
  --no-sandbox \
  --browser chrome \
  --viewport-size 1920x1080 \
  --timeout-action 15000 \
  --timeout-navigation 60000 \
  --output-dir /tmp/playwright-results \
  --save-trace
```

---

## 快捷启动脚本

创建快捷启动脚本 `start-playwright-mcp.sh`:

```bash
#!/bin/bash
# Playwright MCP 启动脚本

playwright-mcp \
  --no-sandbox \
  --browser chrome \
  --viewport-size 1920x1080 \
  --console-level info \
  --timeout-action 10000 \
  --timeout-navigation 30000 \
  --save-trace \
  --output-dir /tmp/playwright-output
```

使用方法：
```bash
chmod +x start-playwright-mcp.sh
./start-playwright-mcp.sh
```

---

## Claude Desktop MCP 配置

如果需要在 Claude Desktop 中配置 Playwright MCP，编辑配置文件：

**Linux**: `~/.config/claude/claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "playwright-mcp",
      "args": [
        "--no-sandbox",
        "--browser", "chrome",
        "--viewport-size", "1920x1080"
      ]
    }
  }
}
```

---

## 测试命令

### 验证安装

```bash
# 检查版本
playwright-mcp --version

# 查看帮助
playwright-mcp --help

# 列出已安装的浏览器
npx playwright list
```

### 测试运行

```bash
# 启动 MCP 服务器并测试
playwright-mcp --no-sandbox --headless
```

---

## 常见问题

### Q: 为什么必须使用 --no-sandbox？
A: 在 Linux root 用户环境下运行 Chrome 需要禁用沙箱，否则会报错 "Running as root without --no-sandbox is not supported"。

### Q: 如何查看详细日志？
A: 使用 `--console-level debug` 选项。

### Q: 如何保存测试结果？
A: 使用 `--output-dir` 指定输出目录，配合 `--save-trace` 或 `--save-video` 保存测试记录。

### Q: 如何测试不同设备？
A: 使用 `--device` 选项，例如 `--device "iPhone 15"`。

---

## 更新日志

- **2026-02-10**: 安装 @playwright/mcp@0.0.64，创建使用指南
