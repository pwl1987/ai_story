#!/bin/bash
# Django Admin服务器启动脚本
# 提供静态文件服务和Django Admin后台

cd "$(dirname "$0")"

echo "🔧 启动Django Admin服务器 (runserver)..."
echo "📦 支持静态文件服务"
echo "🌐 Admin地址: http://localhost:8000/admin/"
echo ""

# 使用runserver提供静态文件服务
uv run python manage.py runserver 0.0.0.0:8000
