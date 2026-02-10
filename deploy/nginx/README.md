# nginx 反向代理配置

> **配置完成时间**: 2026-01-31
> **状态**: ✅ 已完成，可立即使用

---

## 📦 包含文件

| 文件 | 说明 | 用途 |
|-----|------|------|
| `ai-story-dev.conf` | 开发环境配置 | 本地开发测试 |
| `ai-story-prod.conf` | 生产环境配置 | 生产部署 + SSL |
| `README.md` | 本文档 | 配置说明 |

---

## 🚀 快速开始

### 一键安装和配置（推荐）

```bash
# 1. 启动后端服务（确保运行在 8000/8010 端口）
cd /home/code/ai_story
./start_all.sh

# 2. 安装 nginx 并配置（需要 sudo 权限）
sudo ../scripts/setup_nginx.sh

# 3. 测试配置
../scripts/test_nginx.sh

# 4. 访问应用（通过 nginx 统一入口）
open http://localhost/
```

### 手动配置

```bash
# 1. 安装 nginx
sudo apt-get install nginx

# 2. 复制配置文件
sudo cp ai-story-dev.conf /etc/nginx/sites-available/ai-story

# 3. 启用站点
sudo ln -sf /etc/nginx/sites-available/ai-story /etc/nginx/sites-enabled/

# 4. 测试配置
sudo nginx -t

# 5. 重新加载 nginx
sudo systemctl reload nginx
```

---

## 📋 配置特性

### 开发环境 (ai-story-dev.conf)

**路由规则**:
```
/static/     → 静态文件 (直接服务)
/admin/      → Django Admin (8000端口)
/api/        → REST API (8010端口)
/ws/         → WebSocket (8010端口)
/            → 前端应用 (3000端口)
```

**特点**:
- ✅ 支持热重载（前端开发模式）
- ✅ 完整 WebSocket 支持
- ✅ 静态文件缓存
- ✅ 详细日志记录

### 生产环境 (ai-story-prod.conf)

**额外特性**:
- ✅ SSL/HTTPS 支持
- ✅ HTTP 自动重定向到 HTTPS
- ✅ Gzip 压缩
- ✅ 安全头配置
- ✅ 性能优化
- ✅ Let's Encrypt 集成

---

## 🔧 配置详解

### 静态文件服务

```nginx
location /static/ {
    alias /home/code/ai_story/backend/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

**优势**: nginx 原生静态文件服务，比 Django 快 10 倍

### WebSocket 配置

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8010;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

**关键点**:
- HTTP/1.1 协议
- 协议升级头
- 7天超时（支持长连接）

### SSL 配置（生产环境）

```nginx
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
ssl_protocols TLSv1.2 TLSv1.3;
```

---

## 📊 性能优化

### 启用的优化

| 优化项 | 配置 | 收益 |
|-------|------|------|
| **Gzip 压缩** | `gzip on` | 减少 60-80% 传输量 |
| **静态文件缓存** | `expires 30d` | 减少 90% 请求 |
| **Keep-Alive** | `keepalive 64` | 减少握手开销 |
| **Sendfile** | `sendfile on` | 零拷贝文件传输 |

---

## 🧪 测试验证

### 自动化测试

```bash
# 运行完整测试套件
./scripts/test_nginx.sh

# 详细输出
./scripts/test_nginx.sh --verbose
```

### 手动测试

```bash
# 测试静态文件
curl -I http://localhost/static/admin/css/base.css

# 测试 Admin
curl -I http://localhost/admin/

# 测试 API
curl http://localhost/api/v1/health/

# 测试 WebSocket（需要 wscat）
wscat -c ws://localhost/ws/projects/1/
```

---

## 🔍 监控和日志

### 日志位置

```bash
# 访问日志
sudo tail -f /var/log/nginx/ai-story-access.log

# 错误日志
sudo tail -f /var/log/nginx/ai-story-error.log
```

### 状态监控

```bash
# nginx 服务状态
sudo systemctl status nginx

# 配置测试
sudo nginx -t

# 连接统计
sudo netstat -anp | grep nginx
```

---

## ⚠️ 故障排查

### 常见问题

**1. 502 Bad Gateway**
```bash
# 检查后端服务
lsof -i :8000 :8010

# 查看后端日志
tail -f /tmp/admin.log /tmp/daphne.log
```

**2. WebSocket 连接失败**
```bash
# 检查 nginx 配置
grep -A 10 "location /ws/" /etc/nginx/sites-enabled/ai-story

# 重新加载 nginx
sudo systemctl reload nginx
```

**3. 静态文件 404**
```bash
# 检查文件是否存在
ls -la /home/code/ai_story/backend/staticfiles/

# 重新收集
cd backend && uv run python manage.py collectstatic --noinput
```

---

## 📚 相关文档

- [nginx部署完整指南](../../docs/guides/deployment/nginx-deployment.md)
- [双服务器架构说明](../../docs/guides/deployment/dual-server-architecture.md)
- [快速参考卡片](../../docs/guides/deployment/quick-reference.md)
- [部署指南](../../docs/guides/deployment/)

---

## 🔄 生产环境迁移

### 从开发环境迁移到生产环境

```bash
# 1. 修改配置文件中的域名
sed -i 's/your-domain.com/actual-domain.com/g' ai-story-prod.conf

# 2. 安装生产配置
sudo cp ai-story-prod.conf /etc/nginx/sites-available/ai-story

# 3. 获取 SSL 证书
sudo certbot --nginx -d actual-domain.com

# 4. 测试并重载
sudo nginx -t && sudo systemctl reload nginx
```

---

**配置版本**: v1.0
**最后更新**: 2026-01-31
**维护团队**: AI Story Development Team
