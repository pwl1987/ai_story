#!/bin/bash
# Playwright MCP 快捷启动脚本
# 使用方法: ./start-playwright-mcp.sh [options]
#
# 常用选项:
#   --debug        启用调试模式
#   --headed       使用有头模式（显示浏览器窗口）
#   --video        启用视频录制
#   --trace        启用 trace 记录

# 默认配置
BROWSER="chrome"
VIEWPORT="1920x1080"
CONSOLE_LEVEL="info"
HEADLESS="--headless"
VIDEO=""
TRACE=""
OUTPUT_DIR="/tmp/playwright-output"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug)
      CONSOLE_LEVEL="debug"
      shift
      ;;
    --headed)
      HEADLESS=""
      shift
      ;;
    --video)
      VIDEO="--save-video 1920x1080"
      shift
      ;;
    --trace)
      TRACE="--save-trace"
      shift
      ;;
    *)
      echo "未知选项: $1"
      echo "可用选项: --debug, --headed, --video, --trace"
      exit 1
      ;;
  esac
done

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 显示配置信息
echo "=== Playwright MCP 启动配置 ==="
echo "浏览器: $BROWSER"
echo "视口大小: $VIEWPORT"
echo "控制台级别: $CONSOLE_LEVEL"
echo "无头模式: ${HEADLESS:+是}"
echo "视频录制: ${VIDEO:+是}"
echo "Trace 记录: ${TRACE:+是}"
echo "输出目录: $OUTPUT_DIR"
echo "==============================="
echo ""

# 启动 Playwright MCP
exec playwright-mcp \
  --no-sandbox \
  --browser "$BROWSER" \
  --viewport-size "$VIEWPORT" \
  --console-level "$CONSOLE_LEVEL" \
  --timeout-action 10000 \
  --timeout-navigation 30000 \
  $HEADLESS \
  $VIDEO \
  $TRACE \
  --output-dir "$OUTPUT_DIR"
