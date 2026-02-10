# 代理管理系统 - 配置指南

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档详细介绍代理管理系统的所有配置选项。

---

## 🔧 环境变量配置

### 核心配置

**配置文件:** `.env`（开发环境）或环境变量（生产环境）

```bash
# 代理密码加密密钥（必需）
PROXY_ENCRYPTION_KEY=your_fernet_key_here

# Redis配置（用于Celery）
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 密钥生成

```bash
# 生成新的Fernet密钥
uv run python scripts/generate_proxy_key.py
```

⚠️ **安全提示:**
- 生产环境必须使用强密钥
- 密钥泄露会导致所有代理密码可被解密
- 建议定期轮换密钥（需重新加密所有密码）

---

## 🗄️ 数据库配置

### ProxyConfig 模型字段

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | CharField(200) | ✅ | - | 代理名称（唯一标识） |
| `protocol` | CharField(10) | ✅ | HTTP | 代理协议（http/https/socks5） |
| `host` | CharField(255) | ✅ | - | 代理主机地址 |
| `port` | IntegerField | ✅ | - | 代理端口（1-65535） |
| `username` | CharField(200) | ❌ | NULL | 代理认证用户名（可选） |
| `password` | CharField(255) | ❌ | NULL | 代理认证密码（明文，保存后清空） |
| `password_encrypted` | BinaryField | ❌ | NULL | 加密后的密码（自动生成） |
| `is_active` | BooleanField | ❌ | True | 代理是否激活 |
| `is_healthy` | BooleanField | ❌ | True | 代理健康状态（自动更新） |
| `consecutive_failures` | IntegerField | ❌ | 0 | 连续失败次数（健康检查使用） |
| `consecutive_successes` | IntegerField | ❌ | 0 | 连续成功次数（健康检查使用） |
| `priority` | IntegerField | ❌ | 0 | 代理优先级（数字越小优先级越高） |
| `last_used_at` | DateTimeField | ❌ | NULL | 最后使用时间（自动更新） |

### ProxyUsageLog 模型字段

| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `proxy` | ForeignKey | ✅ | - | 关联的代理配置 |
| `ai_provider` | CharField(50) | ✅ | - | AI客户端类型（如'OpenAIClient'） |
| `endpoint` | CharField(255) | ✅ | - | API端点路径 |
| `response_time_ms` | PositiveIntegerField | ✅ | - | API响应时间（毫秒） |
| `success` | BooleanField | ✅ | True | 调用是否成功 |
| `error_message` | TextField | ❌ | NULL | 错误信息（失败时） |
| `timestamp` | DateTimeField | ✅ | auto_now_add | 日志时间戳 |

---

## ⚙️ Celery配置

### 健康检查任务配置

**配置文件:** `config/settings/base.py`

```python
# Celery Beat定时任务配置
CELERY_BEAT_SCHEDULE = {
    "check-proxy-health": {
        "task": "apps.proxy.tasks.check_proxy_health",
        "schedule": 300.0,  # 执行间隔（秒）
        "options": {
            "queue": "llm",  # 队列名称
        },
    },
}
```

### 调整健康检查间隔

**开发环境（快速测试）:**
```python
"schedule": 60.0,  # 1分钟
```

**生产环境（推荐）:**
```python
"schedule": 300.0,  # 5分钟
```

**高频监控（不推荐）:**
```python
"schedule": 30.0,  # 30秒（可能增加代理服务器负担）
```

### 健康检查阈值

**配置文件:** `apps/proxy/tasks.py`

```python
# 连续失败阈值（默认: 3次）
if proxy.consecutive_failures > 3:
    proxy.is_healthy = False

# 健康恢复阈值（默认: 3次）
if proxy.consecutive_successes >= 3:
    proxy.is_healthy = True
```

**自定义阈值:**
- 失败阈值: `> N`（N次失败后标记不健康）
- 恢复阈值: `>= N`（N次成功后恢复健康）

---

## 🔌 代理协议配置

### HTTP/HTTPS 代理

```python
# 无认证
protocol = "http"  # 或 "https"
host = "proxy.example.com"
port = 8080
# username, password 留空

# 有认证
protocol = "https"
host = "proxy.example.com"
port = 8080
username = "user"
password = "pass"  # 保存后自动加密
```

### SOCKS5 代理（V2功能）

```python
# 需要安装 httpx[socks]
protocol = "socks5"
host = "socks5.example.com"
port = 1080
username = "user"  # 可选
password = "pass"  # 可选
```

---

## 🎯 Django Admin 配置

### ProxyConfig Admin 选项

**配置文件:** `apps/proxy/admin.py`

```python
@admin.register(ProxyConfig)
class ProxyConfigAdmin(admin.ModelAdmin):
    # 列表页配置
    list_display = [
        "name", "protocol", "host", "port",
        "is_active", "is_healthy", "priority",
        "last_used_at", "created_at"
    ]
    list_filter = ["protocol", "is_active", "is_healthy", "created_at"]
    search_fields = ["name", "host", "username"]

    # 自定义Action
    actions = ["test_connection"]  # 测试连接功能

    # 详情页字段分组
    fieldsets = (
        ("基本配置", {"fields": ("name", "protocol", "host", "port")}),
        ("认证信息", {"fields": ("username", "password")}),
        ("状态配置", {"fields": ("is_active", "priority")}),
        ("只读信息", {"fields": ("is_healthy", "last_used_at")}),
    )
```

### 批量操作

Django Admin支持以下批量操作:
1. **测试连接**: 选中多个代理 → Action → "测试连接"
2. **激活/禁用**: 选中多个代理 → Action → "标记为激活/禁用"
3. **删除**: 选中多个代理 → Action → "删除"

---

## 🌐 API 配置

### 权限配置

**配置文件:** `apps/proxy/views.py`

```python
# 代理配置API（管理员CRUD）
class ProxyConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]  # 仅管理员

# 代理选择器API（所有用户只读）
class ProxySelectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]  # 登录用户

# 测试连接API（所有用户）
class TestConnectionView(APIView):
    permission_classes = [IsAuthenticated]  # 登录用户
```

### API 端点列表

| 端点 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/v1/proxy/config/` | GET/POST/PUT/DELETE | Admin | 代理配置CRUD |
| `/api/v1/proxy/select/` | GET | Authenticated | 代理选择器列表 |
| `/api/v1/proxy/{id}/test_connection/` | POST | Authenticated | 测试代理连接 |

---

## 🔐 安全配置

### 密码加密

代理密码使用 **Fernet 对称加密**（AES-128）。

**加密流程:**
```python
# 1. 保存时自动加密
proxy.password = "my_password"  # 明文
proxy.save()  # 自动加密到 password_encrypted

# 2. 密码字段自动清空
proxy.password  # None（明文不存储）

# 3. 使用时自动解密
proxy_url = proxy.get_proxy_url()  # 内部解密密码
```

### 密钥轮换（生产环境）

**步骤:**
1. 生成新密钥: `uv run python scripts/generate_proxy_key.py`
2. 更新 `.env` 文件中的 `PROXY_ENCRYPTION_KEY`
3. 重新保存所有代理配置（触发重新加密）

```bash
# Django Shell脚本
from apps.proxy.models import ProxyConfig

for proxy in ProxyConfig.objects.all():
    if proxy.password_encrypted:
        # 临时保存明文密码（需要先解密）
        original_password = proxy.decrypt_password(proxy.password_encrypted)
        proxy.password = original_password
        proxy.save()  # 使用新密钥重新加密
```

---

## 📊 日志配置

### 结构化日志

代理管理使用结构化JSON日志。

**配置文件:** `config/settings/base.py`

```python
LOGGING = {
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/proxy.log",
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "apps.proxy": {
            "handlers": ["file"],
            "level": "INFO",
        },
    },
}
```

### 日志级别

- `INFO`: 正常操作（创建代理、健康检查通过）
- `WARNING`: 非致命错误（健康检查失败、代理降级）
- `ERROR`: 严重错误（加密失败、代理不可用）

---

## 🎛️ 高级配置

### 代理优先级

**用途:** 控制代理选择顺序

```python
# 优先级配置示例
proxy1.priority = 0  # 最高优先级
proxy2.priority = 10  # 次优先级
proxy3.priority = 100  # 最低优先级

# 查询时自动排序
ProxyConfig.objects.filter(is_active=True).order_by("priority", "name")
```

### 自动降级配置

**配置文件:** `apps/proxy/services.py`

```python
class ProxyManager:
    # 自动降级开关
    ENABLE_AUTO_DEGRADATION = True

    # 降级日志记录
    LOG_DEGRADATION = True
```

### 数据库索引优化

**配置文件:** `apps/proxy/models.py`

```python
class Meta:
    indexes = [
        # 复合索引: 活跃且健康的代理
        models.Index(fields=["is_active", "is_healthy"], name="proxy_active_healthy_idx"),
        # 单字段索引: 最后使用时间
        models.Index(fields=["-last_used_at"], name="proxy_last_used_idx"),
    ]
```

---

## ✅ 配置验证

### 1. 检查环境变量

```bash
cd backend

# 检查PROXY_ENCRYPTION_KEY是否设置
uv run python -c "from django.conf import settings; print(settings.PROXY_ENCRYPTION_KEY[:10] + '...')"
```

预期输出:
```
gAAAAABl...（Fernet密钥前缀）
```

### 2. 检查Celery Beat任务

```bash
# 检查任务是否注册
uv run celery -A config inspect registered | grep check-proxy-health
```

预期输出:
```
    - tasks.check_proxy_health
```

### 3. 检查数据库连接

```bash
# 检查代理表是否存在
uv run python manage.py dbshell
```

```sql
-- PostgreSQL
SELECT COUNT(*) FROM proxy_proxyconfig;

-- SQLite
SELECT COUNT(*) FROM proxy_proxyconfig;
```

---

## 📚 配置示例

### 示例1: 开发环境配置

```bash
# .env
PROXY_ENCRYPTION_KEY=dev_key_for_testing_only
REDIS_HOST=localhost
REDIS_PORT=6379
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 示例2: 生产环境配置

```bash
# /etc/environment
PROXY_ENCRYPTION_KEY=<强密钥，从密钥管理服务获取>
REDIS_HOST=redis.internal
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis.internal:6379/0
```

---

**配置支持:** 如遇问题，请查看 [故障排查指南](TROUBLESHOOTING.md)
