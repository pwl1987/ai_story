#!/bin/bash
# 端到端测试运行脚本

set -e

echo "=========================================="
echo "AI Story - 端到端部署测试"
echo "=========================================="
echo ""

# 检查后端服务是否运行
echo "1. 检查后端服务..."
if curl -sf http://localhost:8000/api/v1/health/ > /dev/null; then
    echo "✓ 后端服务运行正常"
else
    echo "✗ 后端服务未运行，请先启动服务"
    echo "  运行: docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# 检查前端服务是否运行
echo "2. 检查前端服务..."
if curl -sf http://localhost/ > /dev/null; then
    echo "✓ 前端服务运行正常"
else
    echo "✗ 前端服务未运行"
fi

# 安装测试依赖
echo "3. 安装测试依赖..."
pip install requests psycopg2-binary websocket-client -q

# 运行端到端测试
echo ""
echo "4. 运行端到端测试..."
echo "=========================================="
cd /home/code/ai_story
python backend/tests/e2e/test_deployment.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "✓ 所有测试通过"
    echo "=========================================="
else
    echo "=========================================="
    echo "✗ 部分测试失败，请检查日志"
    echo "=========================================="
fi

exit $EXIT_CODE
