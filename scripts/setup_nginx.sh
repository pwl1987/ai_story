#!/bin/bash
# AI Story - nginx 开发环境安装和配置脚本

set -e

echo "🚀 AI Story - nginx 开发环境设置"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用 sudo 运行此脚本${NC}"
    echo "命令: sudo ./scripts/setup_nginx.sh"
    exit 1
fi

# 项目根目录
PROJECT_ROOT="/home/code/ai_story"
NGINX_CONF_SOURCE="$PROJECT_ROOT/deploy/nginx/ai-story-dev.conf"
NGINX_CONF_TARGET="/etc/nginx/sites-available/ai-story"
NGINX_CONF_ENABLED="/etc/nginx/sites-enabled/ai-story"

# 1. 检查并安装 nginx
echo -e "${YELLOW}检查 nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    echo "安装 nginx..."
    apt-get update
    apt-get install -y nginx
    echo -e "${GREEN}✓ nginx 安装完成${NC}"
else
    echo -e "${GREEN}✓ nginx 已安装${NC}"
    nginx -v
fi
echo ""

# 2. 检查后端静态文件
echo -e "${YELLOW}检查后端静态文件...${NC}"
if [ ! -d "$PROJECT_ROOT/backend/staticfiles" ]; then
    echo "静态文件不存在，开始收集..."
    cd "$PROJECT_ROOT/backend"
    sudo -u root uv run python manage.py collectstatic --noinput
    echo -e "${GREEN}✓ 静态文件收集完成${NC}"
else
    echo -e "${GREEN}✓ 静态文件已存在${NC}"
fi
echo ""

# 3. 创建必要的目录
echo -e "${YELLOW}创建日志目录...${NC}"
mkdir -p /var/log/nginx
chown -R www-data:www-data /var/log/nginx
echo -e "${GREEN}✓ 日志目录已准备${NC}"
echo ""

# 4. 备份现有配置（如果存在）
if [ -f "$NGINX_CONF_TARGET" ]; then
    BACKUP_FILE="$NGINX_CONF_TARGET.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}备份现有配置...${NC}"
    cp "$NGINX_CONF_TARGET" "$BACKUP_FILE"
    echo -e "${GREEN}✓ 配置已备份到: $BACKUP_FILE${NC}"
fi

# 5. 复制 nginx 配置
echo -e "${YELLOW}安装 nginx 配置...${NC}"
cp "$NGINX_CONF_SOURCE" "$NGINX_CONF_TARGET"
echo -e "${GREEN}✓ 配置文件已复制${NC}"
echo ""

# 6. 创建符号链接
echo -e "${YELLOW}启用站点配置...${NC}"
if [ ! -L "$NGINX_CONF_ENABLED" ]; then
    ln -sf "$NGINX_CONF_TARGET" "$NGINX_CONF_ENABLED"
    echo -e "${GREEN}✓ 符号链接已创建${NC}"
else
    echo -e "${GREEN}✓ 符号链接已存在${NC}"
fi
echo ""

# 7. 删除默认站点配置（可选）
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    echo -e "${YELLOW}禁用默认站点...${NC}"
    rm /etc/nginx/sites-enabled/default
    echo -e "${GREEN}✓ 默认站点已禁用${NC}"
    echo ""
fi

# 8. 测试 nginx 配置
echo -e "${YELLOW}测试 nginx 配置...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ nginx 配置测试通过${NC}"
else
    echo -e "${RED}❌ nginx 配置测试失败${NC}"
    echo "请检查配置文件: $NGINX_CONF_TARGET"
    exit 1
fi
echo ""

# 9. 检查后端服务状态
echo -e "${YELLOW}检查后端服务...${NC}"
if lsof -i :8000 > /dev/null 2>&1 && lsof -i :8010 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务正在运行${NC}"
    echo "  - Admin 服务器: 端口 8000 ✓"
    echo "  - ASGI 服务器:  端口 8010 ✓"
else
    echo -e "${YELLOW}⚠️  后端服务未运行${NC}"
    echo "请先启动后端服务:"
    echo "  cd $PROJECT_ROOT"
    echo "  ./start_all.sh"
    echo ""
    read -p "是否继续启动 nginx? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "设置已取消，请先启动后端服务"
        exit 0
    fi
fi
echo ""

# 10. 重启 nginx
echo -e "${YELLOW}启动 nginx 服务...${NC}"
if systemctl is-active --quiet nginx; then
    systemctl reload nginx
    echo -e "${GREEN}✓ nginx 已重新加载${NC}"
else
    systemctl enable nginx
    systemctl start nginx
    echo -e "${GREEN}✓ nginx 已启动并设置为开机自启${NC}"
fi
echo ""

# 11. 验证 nginx 状态
echo -e "${YELLOW}验证 nginx 状态...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ nginx 运行中${NC}"
else
    echo -e "${RED}❌ nginx 未运行${NC}"
    echo "请检查日志: journalctl -u nginx -n 50"
    exit 1
fi

if lsof -i :80 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ nginx 监听端口 80${NC}"
else
    echo -e "${RED}❌ nginx 未监听端口 80${NC}"
    exit 1
fi
echo ""

# 完成
echo "=================================="
echo -e "${GREEN}🎉 nginx 设置完成！${NC}"
echo "=================================="
echo ""
echo "📱 访问地址（通过 nginx）:"
echo -e "  前端应用:    ${GREEN}http://localhost/${NC}"
echo -e "  Admin后台:   ${GREEN}http://localhost/admin/${NC}"
echo -e "  后端API:     ${GREEN}http://localhost/api/v1/${NC}"
echo -e "  API文档:     ${GREEN}http://localhost/api/schema/${NC}"
echo ""
echo "📊 nginx 状态管理:"
echo "  查看状态:  systemctl status nginx"
echo "  重启服务:  sudo systemctl restart nginx"
echo "  重新加载:  sudo systemctl reload nginx"
echo "  停止服务:  sudo systemctl stop nginx"
echo "  查看日志:  sudo tail -f /var/log/nginx/ai-story-error.log"
echo ""
echo "🔧 配置文件:"
echo "  配置位置:  $NGINX_CONF_TARGET"
echo "  日志位置:  /var/log/nginx/ai-story-*.log"
echo ""
echo "💡 提示:"
echo "  - 开发环境使用端口 80，无需指定端口号"
echo "  - 原始端口仍可访问: 8000 (Admin), 8010 (API), 3000 (前端)"
echo "  - 查看 docs/guides/deployment/nginx-deployment.md 了解详情"
echo ""
echo "=================================="
