#!/bin/bash
# AI Story - 一键完整部署脚本
# 用途: 自动化完成所有服务的启动和初始化

set -e

echo "=========================================="
echo "AI Story - 一键完整部署"
echo "=========================================="
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 步骤1：检查环境
echo "【1/7】检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "✗ Docker未安装"
    exit 1
fi
echo "✓ Docker已安装"

# 步骤2：验证配置
echo ""
echo "【2/7】验证配置文件..."
if [ ! -f ".env" ]; then
    echo "✗ .env文件不存在"
    exit 1
fi
echo "✓ 配置文件检查通过"

# 步骤3：启动后端服务
echo ""
echo "【3/7】启动后端服务（backend + celery）..."
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat

echo "等待服务启动（30秒）..."
for i in {30..1}; do
    echo -ne "\r剩余 $i 秒..."
    sleep 1
done
echo -ne "\r"

echo "✓ 后端服务已启动"

# 步骤4：检查后端健康状态
echo ""
echo "【4/7】检查后端健康状态..."
BACKEND_HEALTH=false
for i in {1..10}; do
    if docker compose -f docker-compose.prod.yml ps | grep backend | grep -q "healthy"; then
        BACKEND_HEALTH=true
        break
    fi
    echo "等待backend健康... ($i/10)"
    sleep 3
done

if [ "$BACKEND_HEALTH" = true ]; then
    echo "✓ Backend服务健康"
else
    echo "⚠ Backend服务未通过健康检查，继续部署..."
fi

# 步骤5：构建前端
echo ""
echo "【5/7】构建前端静态文件..."
if [ ! -d "frontend/node_modules" ]; then
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
fi

echo "构建前端..."
cd frontend
npm run build
cd ..

echo "✓ 前端构建完成"

# 步骤6：启动前端服务
echo ""
echo "【6/7】启动前端服务..."
docker compose -f docker-compose.prod.yml up -d frontend
echo "✓ Frontend服务已启动"

# 步骤7：数据库初始化
echo ""
echo "【7/7】数据库初始化..."
echo "运行数据库迁移..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

echo ""
echo "=========================================="
echo "✓ 部署完成！"
echo "=========================================="

# 计算总耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "总耗时: ${MINUTES}分${SECONDS}秒"
echo ""
echo "服务状态："
docker compose -f docker-compose.prod.yml ps
echo ""
echo "访问地址："
echo "  前端：     http://localhost"
echo "  后端API：  http://localhost:8000/api/v1/"
echo "  Django Admin: http://localhost:8000/admin/"
echo ""
echo "下一步操作："
echo "  1. 创建超级用户："
echo "     docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"
echo ""
echo "  2. 访问前端创建测试项目"
echo ""
echo "  3. 查看日志："
echo "     docker compose -f docker-compose.prod.yml logs -f"
