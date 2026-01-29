#!/bin/bash
# AI Story - 一键启动所有服务
# 让新用户快速启动系统

set -e

echo "🚀 AI Story - 一键启动脚本"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv未安装，请先安装: pip install uv${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm未安装，请先安装Node.js${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 依赖检查通过${NC}"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")"

# 检查Redis
echo -e "${YELLOW}检查Redis...${NC}"
if ! docker ps | grep -q redis; then
    echo "启动Redis容器..."
    docker run -d -p 6379:6379 --name ai-story-redis redis:latest
    echo -e "${GREEN}✓ Redis已启动${NC}"
else
    echo -e "${GREEN}✓ Redis已运行${NC}"
fi
echo ""

# 检查是否需要初始化Demo环境
echo -e "${YELLOW}检查Demo环境...${NC}"
if ! uv run python backend/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(username='demo_user').exists())
" 2>/dev/null | grep -q "True"; then
    echo "Demo用户不存在，开始初始化..."
    cd backend
    uv run python scripts/init_demo_env.py
    cd ..
    echo -e "${GREEN}✓ Demo环境初始化完成${NC}"
else
    echo -e "${GREEN}✓ Demo环境已就绪${NC}"
fi
echo ""

# 启动后端
echo -e "${YELLOW}启动后端服务 (Daphne ASGI)...${NC}"
cd backend
pkill -f "daphne.*config.asgi" || true
nohup uv run daphne -b 0.0.0.0 -p 8010 config.asgi:application > /tmp/daphne.log 2>&1 &
DAEMON_PID=$!
echo "后端PID: $DAEMON_PID"
cd ..

# 等待后端启动
echo "等待后端启动..."
sleep 5

if lsof -i :8010 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端已启动 (端口8010)${NC}"
else
    echo -e "${RED}❌ 后端启动失败，查看日志: /tmp/daphne.log${NC}"
    exit 1
fi
echo ""

# 启动Celery Worker
echo -e "${YELLOW}启动Celery Worker...${NC}"
cd backend
pkill -f "celery.*worker" || true
nohup uv run celery -A config worker -Q llm,image,video -l info > /tmp/celery.log 2>&1 &
CELERY_PID=$!
echo "Celery PID: $CELERY_PID"
cd ..

# 等待Celery启动
echo "等待Celery启动..."
sleep 3

if ps aux | grep -q "[c]elery.*worker"; then
    echo -e "${GREEN}✓ Celery Worker已启动${NC}"
else
    echo -e "${YELLOW}⚠️  Celery启动可能有问题，查看日志: /tmp/celery.log${NC}"
fi
echo ""

# 启动前端
echo -e "${YELLOW}启动前端服务 (Webpack Dev Server)...${NC}"
cd frontend
pkill -f "webpack.*serve" || true
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"
cd ..

# 等待前端启动
echo "等待前端编译..."
sleep 10

if lsof -i :3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端已启动 (端口3000)${NC}"
else
    echo -e "${YELLOW}⚠️  前端编译中，请稍后访问...${NC}"
fi
echo ""

# 打印访问信息
echo "===================="
echo -e "${GREEN}🎉 所有服务启动完成！${NC}"
echo "===================="
echo ""
echo "📱 访问地址:"
echo -e "  前端应用: ${GREEN}http://localhost:3000/${NC}"
echo -e "  后端API:  ${GREEN}http://localhost:8010/api/v1/${NC}"
echo -e "  API文档:  ${GREEN}http://localhost:8010/api/schema/${NC}"
echo ""
echo "👤 Demo账户:"
echo -e "  用户名: ${YELLOW}demo_user${NC}"
echo -e "  密码:   ${YELLOW}demo123456${NC}"
echo ""
echo "📋 日志文件:"
echo "  后端日志:  /tmp/daphne.log"
echo "  Celery日志: /tmp/celery.log"
echo "  前端日志:  /tmp/frontend.log"
echo ""
echo "🛑 停止服务:"
echo "  kill $DAEMON_PID  # 后端"
echo "  kill $CELERY_PID  # Celery"
echo "  kill $FRONTEND_PID # 前端"
echo ""
echo "💡 提示:"
echo "  - 首次访问可能需要等待webpack编译完成"
echo "  - 查看 docs/QUICKSTART.md 了解详细使用指南"
echo "  - Demo项目使用Mock AI，响应快速"
echo ""
echo "===================="

# 保存PID到文件
cat > /tmp/ai_story_pids.sh << EOF
#!/bin/bash
# AI Story进程ID
export DAEMON_PID=$DAEMON_PID
export CELERY_PID=$CELERY_PID
export FRONTEND_PID=$FRONTEND_PID

# 停止所有服务
stop_all() {
    echo "停止所有服务..."
    kill \$DAEMON_PID 2>/dev/null || true
    kill \$CELERY_PID 2>/dev/null || true
    kill \$FRONTEND_PID 2>/dev/null || true
    echo "所有服务已停止"
}

# 查看状态
status() {
    echo "服务状态:"
    ps -p \$DAEMON_PID > /dev/null 2>&1 && echo "  ✓ 后端运行中 (PID: \$DAEMON_PID)" || echo "  ✗ 后端未运行"
    ps -p \$CELERY_PID > /dev/null 2>&1 && echo "  ✓ Celery运行中 (PID: \$CELERY_PID)" || echo "  ✗ Celery未运行"
    ps -p \$FRONTEND_PID > /dev/null 2>&1 && echo "  ✓ 前端运行中 (PID: \$FRONTEND_PID)" || echo "  ✗ 前端未运行"
}

\$1
EOF

chmod +x /tmp/ai_story_pids.sh
echo "进程管理命令: source /tmp/ai_story_pids.sh && status"
echo ""
