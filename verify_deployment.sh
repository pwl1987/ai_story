#!/bin/bash
# 部署验证脚本（简化版）

echo "=========================================="
echo "AI Story - 部署验证"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# 测试函数
test_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✓ $name"
        ((PASSED++))
    else
        echo "✗ $name - 服务不可访问"
        ((FAILED++))
    fi
}

# 测试后端API
echo "1. 测试后端API..."
test_service "健康检查" "http://localhost:8000/api/v1/health/"
test_service "API根路径" "http://localhost:8000/api/v1/"

# 测试前端
echo ""
echo "2. 测试前端..."
test_service "前端首页" "http://localhost/"

# 测试数据库
echo ""
echo "3. 测试数据库连接..."
if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ai_story > /dev/null 2>&1; then
    echo "✓ 数据库连接"
    ((PASSED++))
else
    echo "✗ 数据库连接失败"
    ((FAILED++))
fi

# 测试Redis
echo ""
echo "4. 测试Redis连接..."
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis连接"
    ((PASSED++))
else
    echo "✗ Redis连接失败"
    ((FAILED++))
fi

# 总结
echo ""
echo "=========================================="
echo "测试总结"
echo "=========================================="
TOTAL=$((PASSED + FAILED))
echo "总计: $TOTAL"
echo "通过: $PASSED"
echo "失败: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "✓ 所有验证通过"
    exit 0
else
    echo ""
    echo "✗ 部分验证失败"
    exit 1
fi
