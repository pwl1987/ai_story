# 代理管理系统 - 部署清单

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档提供代理管理系统生产环境部署的完整检查清单。

---

## 🚀 部署前检查

### 1. 环境准备

- [ ] Python 3.11+ 已安装
- [ ] PostgreSQL 数据库已安装并运行
- [ ] Redis 服务已安装并运行
- [ ] Nginx/Caddy 等 Web 服务器已安装

### 2. 依赖检查

```bash
# 进入项目目录
cd /path/to/ai_story/backend

# 安装依赖
uv sync

# 验证关键依赖
uv run python -c "import httpx; import cryptography; import celery; print('✅ 依赖安装成功')"
```

### 3. 配置文件检查

- [ ] `.env` 文件已创建
- [ ] `PROXY_ENCRYPTION_KEY` 已设置（生产环境使用强密钥）
- [ ] 数据库连接配置正确
- [ ] Redis连接配置正确
- [ ] Celery配置正确

---

## 🗄️ 数据库部署

### 1. 创建数据库（PostgreSQL）

```bash
# 创建数据库
sudo -u postgres psql
CREATE DATABASE ai_story_prod;
CREATE USER ai_story_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_story_prod TO ai_story_user;
\q
```

### 2. 运行迁移

```bash
cd /path/to/ai_story/backend

# 设置Django环境变量
export DJANGO_SETTINGS_MODULE=config.settings.production

# 运行迁移
uv run python manage.py migrate

# 验证代理表已创建
uv run python manage.py showmigrations proxy
```

**预期输出:**
```
proxy
 [X] 0001_initial
 [X] 0002_initial
 [X] 0003_proxyusagelog
 [X] 0004_proxyconfig_consecutive_failures_and_more
```

### 3. 创建超级用户

```bash
uv run python manage.py createsuperuser
```

---

## ⚙️ 应用部署

### 1. 收集静态文件

```bash
cd /path/to/ai_story/backend

# 收集静态文件
uv run python manage.py collectstatic --noinput
```

### 2. 配置 Gunicorn

**创建配置文件:** `/etc/gunicorn.d/proxy_config.py`

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = True
user = "www-data"
group = "www-data"
tmp_upload_dir = None
loglevel = "info"
accesslog = "/var/log/gunicorn/proxy_access.log"
errorlog = "/var/log/gunicorn/proxy_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
```

**创建 Systemd 服务:** `/etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=Gunicorn daemon for AI Story
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/ai_story/backend
ExecStart=/path/to/uv run gunicorn config.wsgi:application --config /etc/gunicorn.d/proxy_config.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl status gunicorn
```

---

## 🔄 Celery 部署

### 1. 配置 Celery Worker

**创建 Systemd 服务:** `/etc/systemd/system/celery.service`

```ini
[Unit]
Description=Celery Worker for AI Story
After=network.target redis.service

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/path/to/ai_story/backend
EnvironmentFile=/path/to/ai_story/backend/.env
ExecStart=/path/to/uv run celery -A config worker \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log \
    --loglevel=INFO \
    -Q llm,image,video
ExecStop=/path/to/uv run celery multi stopwait \
    --pidfile=/var/run/celery/worker.pid
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**创建日志目录:**
```bash
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown celery:celery /var/log/celery
sudo chown celery:celery /var/run/celery
```

**启动服务:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

### 2. 配置 Celery Beat

**创建 Systemd 服务:** `/etc/systemd/system/celerybeat.service`

```ini
[Unit]
Description=Celery Beat for AI Story
After=network.target redis.service

[Service]
Type=simple
User=celery
Group=celery
WorkingDirectory=/path/to/ai_story/backend
EnvironmentFile=/path/to/ai_story/backend/.env
ExecStart=/path/to/uv run celery -A config beat \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log \
    --loglevel=INFO
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**启动服务:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable celerybeat
sudo systemctl start celerybeat
sudo systemctl status celerybeat
```

### 3. 验证 Celery Beat 任务

```bash
# 检查任务是否注册
uv run celery -A config inspect registered | grep check-proxy-health

# 查看Beat日志
tail -f /var/log/celery/beat.log

# 预期输出（每5分钟）
# [2026-01-31 10:00:00,123: INFO/MainProcess] Scheduler: Sending due task check-proxy-health
```

---

## 🌐 Nginx 配置

**创建配置文件:** `/etc/nginx/sites-available/ai-story`

```nginx
upstream django {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /path/to/ai_story/backend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/ai_story/backend/media/;
        expires 30d;
    }
}
```

**启用配置:**
```bash
sudo ln -s /etc/nginx/sites-available/ai-story /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 安全配置

### 1. 防火墙规则

```bash
# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许SSH
sudo ufw allow 22/tcp

# 启用防火墙
sudo ufw enable
```

### 2. SSL/TLS 配置（推荐）

**使用 Certbot 获取 Let's Encrypt 证书:**

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d example.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 密钥管理

- [ ] `PROXY_ENCRYPTION_KEY` 已使用强密钥（44字节）
- [ ] `.env` 文件权限设置为 `600`
- [ ] `.env` 文件已添加到 `.gitignore`

```bash
chmod 600 /path/to/ai_story/backend/.env
```

---

## ✅ 部署验证

### 1. 基础功能检查

```bash
# 检查 Django Admin
curl -I http://localhost:8000/admin/

# 预期输出: HTTP/1.1 200 OK

# 检查 API 端点
curl -I http://localhost:8000/api/v1/proxy/select/

# 预期输出: HTTP/1.1 401 Unauthorized (需要认证)
```

### 2. Celery 检查

```bash
# 检查 Celery Worker
sudo systemctl status celery

# 检查 Celery Beat
sudo systemctl status celerybeat

# 查看日志
tail -n 50 /var/log/celery/worker.log
tail -n 50 /var/log/celery/beat.log
```

### 3. 数据库检查

```bash
# 连接数据库
uv run python manage.py dbshell

# 检查代理表
SELECT COUNT(*) FROM proxy_proxyconfig;

# 预期输出: 0 (初始状态)
```

### 4. 代理功能测试

1. 登录 Django Admin: `http://example.com/admin`
2. 创建测试代理
3. 测试连接功能
4. 验证健康检查任务运行（5分钟后）

---

## 📊 监控配置

### 1. 日志监控

```bash
# 创建日志轮转配置
sudo tee /etc/logrotate.d/celery > /dev/null <<EOF
/var/log/celery/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 celery celery
}
EOF
```

### 2. 健康检查端点

```bash
# 检查应用健康状态
curl http://localhost:8000/api/health/

# 预期输出:
# {
#   "status": "healthy",
#   "database": "ok",
#   "redis": "ok"
# }
```

### 3. 告警配置（可选）

**推荐监控指标:**

- Celery Beat 任务执行失败
- 代理健康状态异常（`is_healthy=False`）
- 代理成功率 < 95%
- 数据库连接失败
- Redis 连接失败

---

## 🔄 升级部署

### 1. 备份数据库

```bash
# PostgreSQL 备份
pg_dump -U ai_story_user ai_story_prod > backup_$(date +%Y%m%d).sql

# 或使用 Django 命令
uv run python manage.py dumpdata proxy > proxy_backup_$(date +%Y%m%d).json
```

### 2. 部署新版本

```bash
# 拉取最新代码
git pull origin main

# 安装依赖
uv sync

# 运行迁移
uv run python manage.py migrate

# 收集静态文件
uv run python manage.py collectstatic --noinput

# 重启服务
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat
```

### 3. 回滚计划

```bash
# 回滚代码
git checkout <previous_commit>

# 回滚数据库迁移
uv run python manage.py migrate proxy <previous_migration>

# 重启服务
sudo systemctl restart gunicorn celery celerybeat
```

---

## 📝 部署检查清单总结

### 部署前
- [ ] 环境依赖已安装
- [ ] 数据库已创建
- [ ] `.env` 文件已配置
- [ ] 密钥已生成

### 部署中
- [ ] 数据库迁移已运行
- [ ] 静态文件已收集
- [ ] Gunicorn 服务已启动
- [ ] Celery Worker 已启动
- [ ] Celery Beat 已启动
- [ ] Nginx 已配置并启动

### 部署后
- [ ] Django Admin 可访问
- [ ] API 端点可访问
- [ ] 代理功能可正常使用
- [ ] 健康检查任务正常运行
- [ ] 日志正常记录
- [ ] 监控已配置

---

## 📚 相关文档

- [安装指南](INSTALLATION.md)
- [配置指南](CONFIGURATION.md)
- [使用指南](USAGE.md)
- [安全指南](SECURITY.md)

---

**部署支持:** 如遇问题，请查看 [故障排查指南](TROUBLESHOOTING.md)
