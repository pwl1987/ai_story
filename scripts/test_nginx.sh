#!/bin/bash
# AI Story - nginx 配置测试脚本
# 验证 nginx 反向代理是否正常工作

set -e

echo "🧪 AI Story - nginx 配置测试"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local description="$4"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "测试 $TOTAL_TESTS: $name ... "

    actual_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [ "$actual_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $actual_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (期望: HTTP $expected_code, 实际: HTTP $actual_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 1. 检查 nginx 服务
echo -e "${YELLOW}检查 nginx 服务状态...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ nginx 运行中${NC}"
else
    echo -e "${RED}❌ nginx 未运行${NC}"
    echo "请先启动: sudo systemctl start nginx"
    exit 1
fi

if lsof -i :80 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ nginx 监听端口 80${NC}"
else
    echo -e "${RED}❌ nginx 未监听端口 80${NC}"
    exit 1
fi
echo ""

# 2. 检查后端服务
echo -e "${YELLOW}检查后端服务状态...${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Admin 服务器运行中 (端口 8000)${NC}"
else
    echo -e "${RED}❌ Admin 服务器未运行 (端口 8000)${NC}"
    exit 1
fi

if lsof -i :8010 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ASGI 服务器运行中 (端口 8010)${NC}"
else
    echo -e "${RED}❌ ASGI 服务器未运行 (端口 8010)${NC}"
    exit 1
fi
echo ""

# 3. 测试各个端点
echo -e "${YELLOW}测试端点响应...${NC}"
echo ""

# 静态文件测试
test_endpoint "静态文件 (CSS)" "http://localhost/static/admin/css/base.css" "200" "Django Admin CSS 文件"

# Admin 后台测试
test_endpoint "Admin 后台首页" "http://localhost/admin/" "302" "重定向到登录页"

# API 测试
test_endpoint "API 健康检查" "http://localhost/api/v1/health/" "200" "系统健康状态"
test_endpoint "API 根路径" "http://localhost/api/v1/" "200" "API 根路径"

# API 文档测试
test_endpoint "API Schema" "http://localhost/api/schema/" "200" "OpenAPI Schema"

# 前端应用测试
if lsof -i :3000 > /dev/null 2>&1; then
    test_endpoint "前端应用" "http://localhost/" "200" "Vue 前端应用"
else
    echo -e "${YELLOW}⚠️  跳过: 前端应用未运行 (端口 3000)${NC}"
fi
echo ""

# 4. 详细测试（可选）
if [ "$1" = "--verbose" ]; then
    echo -e "${YELLOW}详细响应信息...${NC}"
    echo ""

    echo "=== 健康检查 API ==="
    curl -s http://localhost/api/v1/health/ | python3 -m json.tool || echo "解析失败"
    echo ""

    echo "=== 静态文件头信息 ==="
    curl -I http://localhost/static/admin/css/base.css 2>&1 | head -10
    echo ""

    echo "=== Admin 重定向信息 ==="
    curl -I http://localhost/admin/ 2>&1 | head -10
    echo ""
fi

# 5. 测试结果汇总
echo "=================================="
echo -e "${YELLOW}测试结果汇总${NC}"
echo "=================================="
echo "总测试数: $TOTAL_TESTS"
echo -e "通过:     ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败:     ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    echo ""
    echo "✅ nginx 配置正确，可以正常使用"
    echo ""
    echo "📱 访问地址:"
    echo -e "  前端:    ${GREEN}http://localhost/${NC}"
    echo -e "  Admin:   ${GREEN}http://localhost/admin/${NC}"
    echo -e "  API:     ${GREEN}http://localhost/api/v1/${NC}"
    echo -e "  文档:    ${GREEN}http://localhost/api/schema/${NC}"
    exit 0
else
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试失败${NC}"
    echo ""
    echo "🔍 故障排查:"
    echo "  1. 检查 nginx 错误日志: sudo tail -f /var/log/nginx/ai-story-error.log"
    echo "  2. 检查后端日志: tail -f /tmp/admin.log /tmp/daphne.log"
    echo "  3. 验证后端服务: lsof -i :8000 :8010"
    echo "  4. 测试 nginx 配置: sudo nginx -t"
    exit 1
fi
