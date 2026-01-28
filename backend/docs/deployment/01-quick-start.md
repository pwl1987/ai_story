# 快速启动指南

> 本指南帮助您在5分钟内启动AI Story生成系统

---

## 环境要求

- Python 3.11+
- Node.js 16+
- Redis 6+
- SQLite 3（开发）或 PostgreSQL 14（生产）

---

## 快速启动

### 1. 启动Redis

```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. 启动后端服务

```bash
cd backend

# 安装依赖
uv sync

# 运行迁移
uv run python manage.py migrate

# 启动ASGI服务器（支持WebSocket）
./run_asgi.sh
```

### 3. 启动Celery Worker

```bash
cd backend

# 新终端窗口
uv run celery -A config worker -Q llm,image,video -l info
```

### 4. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 访问地址

- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin

---

## 验证启动

```bash
# 检查Redis
redis-cli ping  # 应返回 PONG

# 检查后端API
curl http://localhost:8000/api/v1/

# 检查Celery Worker
# 应看到 "celery@xxx ready"
```

---

## 常见问题

### Q: Redis连接失败？

A: 确保Redis运行中：
```bash
docker ps | grep redis
```

### Q: Celery Worker无法启动？

A: 检查Redis是否运行，然后重启Celery：
```bash
pkill -f celery
uv run celery -A config worker -Q llm,image,video -l info
```

### Q: WebSocket连接失败？

A: 确保使用ASGI服务器而非runserver：
```bash
./run_asgi.sh  # 正确
uv run python manage.py runserver  # 错误 - 不支持WebSocket
```

---

## 下一步

- 配置Mock环境: [Mock环境配置指南](./02-mock-environment.md)
- 生产部署: [生产环境部署指南](./03-production-setup.md)
- 故障排查: [常见问题排查](../troubleshooting/01-common-issues.md)
