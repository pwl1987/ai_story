# 代理管理系统 - 安装指南

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档介绍如何为AI Story生成系统安装和配置代理管理功能。

**前置条件:**
- ✅ Python 3.11+
- ✅ Django 3.2.15
- ✅ Redis（用于Celery）
- ✅ PostgreSQL（推荐）/ SQLite（开发环境）

---

## 🚀 快速安装

### Step 1: 安装Python依赖

代理管理系统需要以下Python包：

```bash
cd backend

# 安装核心依赖（httpx已包含在项目中）
uv sync

# 如果需要SOCKS5支持（V2功能）
uv pip install httpx[socks]
```

**依赖说明:**
- `httpx` - HTTP客户端，支持代理
- `cryptography` - Fernet密码加密
- `celery` - 异步任务队列
- `redis` - 缓存和消息队列

### Step 2: 生成加密密钥

代理密码使用Fernet对称加密，需要生成密钥：

```bash
cd backend

# 生成Fernet密钥
uv run python scripts/generate_proxy_key.py
```

**输出示例:**
```
✅ Fernet密钥已生成到 .env 文件
PROXY_ENCRYPTION_KEY=your_fernet_key_here
```

**密钥说明:**
- 密钥存储位置: `.env` 文件
- 密钥格式: 44字节URL安全的base64编码字符串
- ⚠️ **重要**: 生产环境请使用强密钥，并妥善保管

### Step 3: 数据库迁移

创建代理管理所需的数据库表：

```bash
cd backend

# 运行迁移
uv run python manage.py migrate proxy
```

**迁移内容:**
- `proxy_proxyconfig` - 代理配置表
- `proxy_proxyusagelog` - 使用日志表

**验证迁移:**
```bash
uv run python manage.py showmigrations proxy
```

预期输出:
```
proxy
 [X] 0001_initial
 [X] 0002_initial
 [X] 0003_proxyusagelog
 [X] 0004_proxyconfig_consecutive_failures_and_more
```

### Step 4: 创建超级用户（如果还没有）

```bash
cd backend

# 创建Django超级用户
uv run python manage.py createsuperuser
```

按提示输入：
- 用户名
- 邮箱
- 密码

---

## 🔧 Celery Beat配置

### Step 1: 配置定时任务

代理健康检查需要Celery Beat定时任务。

**配置文件:** `config/settings/base.py`

```python
# Celery Beat定时任务配置
CELERY_BEAT_SCHEDULE = {
    "check-proxy-health": {
        "task": "apps.proxy.tasks.check_proxy_health",
        "schedule": 300.0,  # 5分钟（300秒）
        "options": {"queue": "llm"},
    },
}
```

### Step 2: 启动Celery Beat

**开发环境:**
```bash
cd backend

# 启动Celery Beat
uv run celery -A config beat -l info
```

**生产环境（使用Supervisor）:**

创建配置文件 `/etc/supervisor/conf.d/celerybeat.conf`:

```ini
[program:celerybeat]
command=/path/to/uv run celery -A config beat -l info
directory=/path/to/backend
user=celery
numprocs=1
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat_err.log
```

启动服务:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start celerybeat
```

---

## ✅ 验证安装

### 1. 检查Django Admin

访问: `http://localhost:8000/admin`

登录后应该看到:
- ✅ Proxy Configurations
- ✅ Proxy Usage Logs

### 2. 检查API端点

```bash
# 获取代理列表（需要登录）
curl -X GET http://localhost:8000/api/v1/proxy/select/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

预期返回:
```json
{
    "count": 0,
    "next": null,
    "previous": null,
    "results": []
}
```

### 3. 检查Celery Beat

查看Celery Beat日志:

```bash
tail -f /var/log/celery/beat.log
```

预期输出（每5分钟）:
```
[2026-01-31 10:00:00,123: INFO/MainProcess] Scheduler: Sending due task check-proxy-health
```

---

## 📦 安装清单

- [ ] Python依赖安装完成
- [ ] Fernet密钥已生成并配置到 `.env`
- [ ] 数据库迁移已执行
- [ ] Django超级用户已创建
- [ ] Celery Beat已启动并正常运行
- [ ] Django Admin可以访问代理管理界面
- [ ] API端点可以正常访问

---

## 🐛 常见安装问题

### 问题1: 迁移失败 "No module named 'cryptography'"

**解决方案:**
```bash
uv pip install cryptography
```

### 问题2: 密钥生成失败 "PROXY_ENCRYPTION_KEY already exists"

**解决方案:**
```bash
# 手动编辑 .env 文件
# 删除或注释掉现有的 PROXY_ENCRYPTION_KEY 行
# 然后重新运行生成脚本
```

### 问题3: Celery Beat不执行任务

**检查清单:**
1. Redis是否运行: `redis-cli ping`
2. Celery Beat是否启动: `ps aux | grep celery`
3. 任务是否注册: `uv run celery -A config inspect registered`

---

## 📚 下一步

安装完成后，请参考:
- [配置指南](CONFIGURATION.md) - 详细的配置选项
- [使用指南](USAGE.md) - 如何使用代理管理功能
- [API文档](API.md) - API接口说明

---

**安装支持:** 如遇问题，请查看 [故障排查指南](TROUBLESHOOTING.md)
