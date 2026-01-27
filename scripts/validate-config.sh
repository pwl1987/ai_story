#!/bin/bash
# AI Story - 配置验证脚本
# 用途: 在部署前验证所有配置文件的正确性

set -e

echo "=========================================="
echo "AI Story - 配置验证"
echo "=========================================="
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1: $2"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1: $2"
    ((WARNINGS++))
}

# 1. 检查Docker环境
echo "1. Docker环境检查"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}')
    test_pass "Docker已安装 (版本: $DOCKER_VERSION)"
else
    test_fail "Docker未安装" "请先安装Docker"
fi

if command -v docker &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "未安装")
    test_pass "Docker Compose已安装 (版本: $COMPOSE_VERSION)"
else
    test_fail "Docker Compose未安装" "请先安装Docker Compose"
fi

# 2. 检查配置文件存在性
echo ""
echo "2. 配置文件检查"
config_files=(
    "docker-compose.prod.yml"
    ".env"
    "deploy/nginx/nginx.conf"
    "deploy/nginx/conf.d/ai_story.conf"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        test_pass "配置文件存在: $file"
    else
        test_fail "配置文件缺失: $file" "请先创建该文件"
    fi
done

# 3. 检查环境变量配置
echo ""
echo "3. 环境变量检查"
if [ -f ".env" ]; then
    # 检查必需的环境变量
    required_vars=(
        "SECRET_KEY"
        "DEBUG"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            test_pass "环境变量已配置: $var"
        else
            test_fail "环境变量缺失: $var" "请在.env中配置此变量"
        fi
    done
    
    # 检查DEBUG配置
    if grep -q "^DEBUG=False" .env; then
        test_pass "DEBUG正确设置为False"
    else
        test_warn "DEBUG未设置为False" "生产环境应设置为False"
    fi
else
    test_fail ".env文件不存在" "请先创建.env文件"
fi

# 4. 检查Docker Compose配置
echo ""
echo "4. Docker Compose配置验证"
if docker compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    test_pass "docker-compose.prod.yml语法正确"
else
    test_fail "docker-compose.prod.yml语法错误" "请检查配置文件"
fi

# 5. 检查端口占用
echo ""
echo "5. 端口占用检查"
ports=(80 443 8000 5432 6379)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        test_warn "端口${port}已被占用" "可能导致服务启动失败"
    else
        test_pass "端口${port}可用"
    fi
done

# 6. 检查磁盘空间
echo ""
echo "6. 系统资源检查"
available_space=$(df / | tail -1 | awk '{print $4}')
available_mb=$((available_space / 1024 / 1024))

if [ $available_mb -gt 10240 ]; then
    test_pass "磁盘空间充足 (${available_mb}MB可用)"
else
    test_fail "磁盘空间不足" "至少需要10GB可用空间"
fi

total_mem=$(free -m | grep Mem | awk '{print $2}')
available_mem=$(free -m | grep Mem | awk '{print $7}')

if [ $total_mem -gt 4096 ]; then
    test_pass "内存充足 (${total_mem}MB总计, ${available_mem}MB可用)"
else
    test_warn "内存可能不足" "建议至少4GB内存"
fi

# 7. 检查文件权限
echo ""
echo "7. 文件权限检查"
if [ -f ".env" ]; then
    env_perms=$(stat -c %a .env)
    if [ "$env_perms" = "600" ]; then
        test_pass ".env文件权限正确 (600)"
    else
        test_warn ".env文件权限不安全 (当前${env_perms})" "建议设置为600"
    fi
fi

# 8. 总结
echo ""
echo "=========================================="
echo "验证总结"
echo "=========================================="
TOTAL=$((PASSED + FAILED))
echo "总计: $TOTAL"
echo -e "${GREEN}通过: $PASSED${NC}"
echo -e "${RED}失败: $FAILED${NC}"
echo -e "${YELLOW}警告: $WARNINGS${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 所有必需检查通过，可以开始部署${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ 发现${FAILED}个错误，请修复后重试${NC}"
    exit 1
fi
