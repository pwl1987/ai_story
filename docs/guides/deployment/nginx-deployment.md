# nginx 反向代理部署指南

> **创建时间**: 2026-01-31
> **适用环境**: 开发环境 / 生产环境
> **目的**: 统一入口，生产级部署

---

## 概述

### nginx 反向代理架构

```
                    ┌─────────────────┐
                    │   浏览器/客户端   │
                    └────────┬────────┘
                             │ HTTP (80/443)
                             ↓
                    ┌─────────────────┐
                    │  nginx 反向代理  │
                    │  (统一入口)      │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ↓                 ↓                 ↓
    ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
    │ 静态文件     │  │  Django后端   │  │  前端应用    │
    │ (直接服务)   │  │  (反向代理)   │  │  (反向代理)  │
    └─────────────┘  └──────────────┘  └─────────────┘
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
       ┌──────────┐              ┌──────────┐
       │ runserver│              │  Daphne  │
       │  :8000   │              │  :8010   │
       │ (Admin)  │              │ (API/WS) │
       └──────────┘              └──────────┘
```

### 核心优势

| 优势 | 说明 | 收益 |
|-----|------|------|
| **统一入口** | 单一端口 80/443 | 简化部署，用户友好 |
| **高性能** | nginx 原生静态文件服务 | 比 Django 快 10 倍 |
| **负载均衡** | 支持多服务器集群 | 横向扩展能力 |
| **SSL 终止** | HTTPS 加密 | 安全性提升 |
| **WebSocket 支持** | 完整支持 ASGI | 实时通信无障碍 |
| **缓存控制** | 静态资源长期缓存 | 减少带宽消耗 |

---

## 快速开始（开发环境）

### 前置条件

1. ✅ 后端服务运行在 8000 和 8010 端口
2. ✅ 前端服务运行在 3000 端口
3. ✅ 静态文件已收集 (`collectstatic`)
4. ✅ sudo 权限（安装 nginx）

### 一键安装和配置

```bash
# 1. 安装 nginx 并配置
sudo ./scripts/setup_nginx.sh

# 2. 测试配置
./scripts/test_nginx.sh

# 3. 访问应用（通过 nginx）
# 前端: http://localhost/
# Admin: http://localhost/admin/
# API:   http://localhost/api/v1/
```

### 验证安装

```bash
# 检查 nginx 状态
sudo systemctl status nginx

# 检查端口监听
lsof -i :80

# 查看日志
sudo tail -f /var/log/nginx/ai-story-error.log
```

---

## 配置详解

### 开发环境配置

**配置文件**: `deploy/nginx/ai-story-dev.conf`

**关键配置**：

```nginx
# 静态文件（最高优先级）
location /static/ {
    alias /home/code/ai_story/backend/staticfiles/;
    expires 30d;
}

# Admin 后台
location /admin/ {
    proxy_pass http://127.0.0.1:8000;
}

# API + WebSocket
location /api/ {
    proxy_pass http://127.0.0.1:8010;
}

location /ws/ {
    proxy_pass http://127.0.0.1:8010;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# 前端应用
location / {
    proxy_pass http://127.0.0.1:3000;
}
```

### 生产环境配置

**配置文件**: `deploy/nginx/ai-story-prod.conf`

**额外特性**：

```nginx
# SSL 证书
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

# 安全头
add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Frame-Options "SAMEORIGIN" always;

# Gzip 压缩
gzip on;
gzip_types text/plain text/css application/json;

# 前端静态文件（生产构建）
location / {
    root /var/www/ai-story/frontend/dist;
    try_files $uri $uri/ /index.html;
}
```

---

## 路由规则详解

### 优先级顺序（从高到低）

```
1. /static/      → 静态文件（CSS/JS/Images）
2. /media/       → 用户上传媒体文件
3. /storage/     → 系统生成文件（图片/视频）
4. /admin/       → Django Admin 后台
5. /api/         → REST API 端点
6. /ws/          → WebSocket 连接
7. /             → 前端应用（Vue SPA）
```

### WebSocket 特殊配置

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8010;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # 长连接超时（7 天）
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

**关键点**：
- ✅ `proxy_http_version 1.1` - 必须使用 HTTP/1.1
- ✅ `Upgrade` 和 `Connection` 头 - 启用协议升级
- ✅ 超时时间设置为 7 天 - 支持持久连接

---

## SSL/HTTPS 配置（生产环境）

### 使用 Let's Encrypt 免费证书

```bash
# 1. 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. 获取证书（自动配置 nginx）
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 3. 自动续期
sudo certbot renew --dry-run

# 4. 查看证书
sudo certbot certificates
```

### 证书自动续期

```bash
# Certbot 会自动创建 systemd timer
sudo systemctl status certbot.timer

# 手动测试续期
sudo certbot renew
```

---

## 性能优化

### 1. 启用 Gzip 压缩

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript
           application/json application/javascript application/xml+rss
           application/rss+xml font/truetype font/opentype
           application/vnd.ms-fontobject image/svg+xml;
```

**收益**：传输数据量减少 60-80%

### 2. 静态文件缓存

```nginx
location /static/ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}
```

**收益**：减少 90% 的静态文件请求

### 3. Keep-Alive 连接

```nginx
upstream daphne_asgi {
    server 127.0.0.1:8010;
    keepalive 64;
}
```

**收益**：减少 TCP 握手开销

### 4. 调整 Worker 进程数

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 1024;
```

**推荐配置**：
- 开发环境: `worker_processes 2`
- 生产环境: `worker_processes auto` (CPU 核心数)

---

## 监控和日志

### 日志位置

```bash
# 访问日志
/var/log/nginx/ai-story-access.log

# 错误日志
/var/log/nginx/ai-story-error.log

# 实时查看
sudo tail -f /var/log/nginx/ai-story-error.log
```

### 日志分析

```bash
# 统计访问量最高的 IP
awk '{print $1}' /var/log/nginx/ai-story-access.log | sort | uniq -c | sort -nr | head -10

# 统计 HTTP 状态码
awk '{print $9}' /var/log/nginx/ai-story-access.log | sort | uniq -c | sort -nr

# 统计访问最多的 URL
awk '{print $7}' /var/log/nginx/ai-story-access.log | sort | uniq -c | sort -nr | head -10
```

### 性能监控

```bash
# 安装 nginx status 模块
sudo apt-get install nginx-extras

# 配置 status 端点
location /nginx_status {
    stub_status on;
    access_log off;
}

# 访问状态
curl http://localhost/nginx_status
```

---

## 故障排查

### 问题 1: 502 Bad Gateway

**症状**: nginx 返回 502 错误

**原因**: 后端服务未运行或无法连接

**解决**:
```bash
# 1. 检查后端服务
lsof -i :8000 :8010

# 2. 查看后端日志
tail -f /tmp/admin.log /tmp/daphne.log

# 3. 重启后端服务
cd /home/code/ai_story
./start_all.sh
```

### 问题 2: WebSocket 连接失败

**症状**: 前端进度不实时更新

**原因**: nginx WebSocket 配置错误

**解决**:
```bash
# 1. 检查 nginx 配置
sudo nginx -t

# 2. 确认包含 WebSocket 配置
grep -A 10 "location /ws/" /etc/nginx/sites-enabled/ai-story

# 3. 重新加载 nginx
sudo systemctl reload nginx
```

### 问题 3: 静态文件 404

**症状**: CSS/JS 文件返回 404

**原因**: 静态文件路径错误或未收集

**解决**:
```bash
# 1. 检查静态文件是否存在
ls -la /home/code/ai_story/backend/staticfiles/

# 2. 重新收集静态文件
cd backend
uv run python manage.py collectstatic --noinput

# 3. 检查 nginx 配置中的路径
grep "alias.*staticfiles" /etc/nginx/sites-enabled/ai-story
```

### 问题 4: 权限拒绝

**症状**: 403 Forbidden

**原因**: 文件权限问题

**解决**:
```bash
# 修正静态文件权限
sudo chown -R www-data:www-data /home/code/ai_story/backend/staticfiles/
sudo chmod -R 755 /home/code/ai_story/backend/staticfiles/

# 检查 nginx 运行用户
ps aux | grep nginx | grep worker
```

---

## 部署流程

### 完整部署步骤

```bash
# 1. 启动后端服务（双服务器架构）
cd /home/code/ai_story
./start_all.sh

# 2. 收集静态文件
cd backend
uv run python manage.py collectstatic --noinput

# 3. 安装和配置 nginx
sudo ./scripts/setup_nginx.sh

# 4. 测试配置
./scripts/test_nginx.sh

# 5. 验证应用访问
curl http://localhost/api/v1/health/
```

### 零停机部署

```bash
# 1. 备份当前版本
cp -r backend backend.backup.$(date +%Y%m%d)

# 2. 更新代码
git pull

# 3. 更新依赖
cd backend
uv sync

# 4. 数据库迁移
uv run python manage.py migrate

# 5. 收集静态文件
uv run python manage.py collectstatic --noinput

# 6. 重新加载后端（使用热重载）
kill -HUP $(cat /tmp/admin.pid)
kill -HUP $(cat /tmp/daphne.pid)

# 7. 重新加载 nginx
sudo systemctl reload nginx
```

---

## 安全加固

### 1. 隐藏 nginx 版本号

```nginx
# /etc/nginx/nginx.conf
server_tokens off;
```

### 2. 限制请求大小

```nginx
client_max_body_size 100M;
```

### 3. 限流配置

```nginx
# 限制每个 IP 每秒 10 个请求
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://daphne_asgi;
}
```

### 4. 禁止访问敏感文件

```nginx
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}

location ~ ~$ {
    deny all;
}
```

---

## 相关文档

- [双服务器架构说明](./dual-server-architecture.md)
- [部署指南](./deployment.md)
- [快速开始](../../QUICKSTART.md)
- [nginx 官方文档](https://nginx.org/en/docs/)

---

**文档版本**: v1.0
**最后更新**: 2026-01-31
**维护团队**: AI Story Development Team
