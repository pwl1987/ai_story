# 代理管理系统 - 故障排查指南

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档提供代理管理系统常见问题的诊断和解决方案。

---

## 🔍 快速诊断流程

### 诊断检查清单

当遇到代理问题时，按以下顺序检查：

1. ✅ **代理配置检查**: Django Admin → Proxy Configurations
2. ✅ **健康状态检查**: `Is healthy` 字段
3. ✅ **日志检查**: Proxy Usage Logs
4. ✅ **连接测试**: "测试连接" 功能
5. ✅ **Celery检查**: 健康检查任务是否运行
6. ✅ **网络检查**: 代理服务器可达性

---

## 🐛 常见问题

### 问题1: 代理连接失败

**症状:**
- 测试连接显示: `Connection timeout`
- AI调用失败: `Proxy connection failed`

**诊断步骤:**

```bash
# 1. 检查代理服务器是否可达
ping proxy.example.com

# 2. 检查端口是否开放
telnet proxy.example.com 8080

# 3. 使用curl测试
curl -x https://proxy_user:proxy_pass@proxy.example.com:8080 https://httpbin.org/ip
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 代理服务器宕机 | 联系代理服务提供商 |
| 端口被封禁 | 更换代理端口 |
| 网络不通 | 检查防火墙规则 |
| DNS解析失败 | 检查DNS配置，尝试使用IP地址 |

### 问题2: 认证失败

**症状:**
- 测试连接显示: `HTTP error 407` (Proxy Authentication Required)
- 日志错误: `403 Forbidden`

**诊断步骤:**

1. 检查用户名/密码是否正确:
   - Django Admin → 代理详情页
   - 重新输入密码并保存

2. 检查密码是否正确加密:

```python
# Django Shell
from apps.proxy.models import ProxyConfig

proxy = ProxyConfig.objects.get(name="美国代理-01")
print(f"用户名: {proxy.username}")
print(f"密码已加密: {proxy.password_encrypted is not None}")

# 测试解密
try:
    password = proxy.decrypt_password(proxy.password_encrypted)
    print(f"密码解密成功: {password[:3]}***")
except Exception as e:
    print(f"解密失败: {e}")
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 用户名/密码错误 | 重新输入正确的用户名和密码 |
| 密码过期 | 联系代理服务提供商重置密码 |
| 加密密钥错误 | 检查 `.env` 中的 `PROXY_ENCRYPTION_KEY` |

### 问题3: 代理响应慢

**症状:**
- 测试连接响应时间 > 3000ms
- AI调用超时

**诊断步骤:**

1. 查看使用日志中的响应时间:
   - Django Admin → Proxy Usage Logs
   - 查看最近成功的日志的 `response_time_ms`

2. 对比不同代理的响应时间:

```python
from apps.proxy.models import ProxyUsageLog
from django.db.models import Avg

stats = ProxyUsageLog.objects.filter(success=True).values(
    "proxy__name"
).annotate(
    avg_response_time=Avg("response_time_ms")
).order_by("-avg_response_time")

for stat in stats:
    print(f"{stat['proxy__name']}: {stat['avg_response_time']:.0f}ms")
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 代理服务器负载高 | 更换其他代理或升级代理套餐 |
| 网络延迟 | 选择地理位置更近的代理 |
| 代理服务器限速 | 联系代理服务提供商 |

### 问题4: 健康检查任务不运行

**症状:**
- 代理状态长时间不更新
- `consecutive_failures` 和 `consecutive_successes` 始终为0

**诊断步骤:**

```bash
# 1. 检查Celery Beat是否运行
ps aux | grep celery

# 2. 检查Celery Beat日志
tail -f /var/log/celery/beat.log

# 3. 检查任务是否注册
uv run celery -A config inspect registered | grep check-proxy-health
```

**预期输出:**
```
celery@hostname: OK
    * check-proxy-health
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| Celery Beat未启动 | 启动 Celery Beat: `uv run celery -A config beat -l info` |
| Redis未运行 | 启动 Redis: `redis-server` |
| 任务未注册 | 重启 Celery Beat |
| 配置错误 | 检查 `CELERY_BEAT_SCHEDULE` 配置 |

### 问题5: 代理频繁被标记为不健康

**症状:**
- 代理 `is_healthy` 频繁在 True/False 之间切换
- `consecutive_failures` 经常 > 3

**诊断步骤:**

1. 查看健康检查日志:
   - Django Admin → Proxy Usage Logs
   - 筛选 `ai_provider="celery"` 和 `success=False`

2. 分析失败模式:
   - 是否集中在特定时间段（如高峰期）
   - 是否所有代理都失败（可能是网络问题）
   - 是否单个代理失败（代理问题）

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 代理不稳定 | 更换稳定的代理服务 |
| 健康检查间隔太短 | 调整 `CELERY_BEAT_SCHEDULE` 间隔 |
| 阈值设置太低 | 增加失败阈值（默认3次） |
| 网络波动 | 增加超时时间（默认5秒） |

### 问题6: 密码加密/解密失败

**症状:**
- 保存代理时出错: `ImproperlyConfigured: 代理密码加密需要PROXY_ENCRYPTION_KEY环境变量`
- 使用代理时出错: `InvalidToken`

**诊断步骤:**

```bash
# 1. 检查环境变量
uv run python -c "from django.conf import settings; print(hasattr(settings, 'PROXY_ENCRYPTION_KEY'))"

# 预期输出: True

# 2. 检查密钥格式
uv run python -c "from django.conf import settings; print(len(settings.PROXY_ENCRYPTION_KEY))"

# 预期输出: 44 (Fernet密钥长度)
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| `.env` 文件不存在 | 生成密钥: `uv run python scripts/generate_proxy_key.py` |
| 密钥格式错误 | 重新生成密钥 |
| 密钥不匹配 | 检查是否使用了正确的 `.env` 文件 |
| 密钥已更换 | 需要重新保存所有代理配置 |

### 问题7: API返回403 Forbidden

**症状:**
- API请求返回: `{"detail": "您没有权限执行此操作"}`

**诊断步骤:**

1. 检查用户权限:
   - `/api/v1/proxy/config/` 需要管理员权限
   - `/api/v1/proxy/select/` 需要登录用户权限

2. 检查Token是否有效:

```bash
# 验证Token
curl -X GET http://localhost:8000/api/v1/user/me/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 非管理员访问CRUD API | 使用管理员账户登录 |
| Token过期 | 重新登录获取新Token |
| 权限配置错误 | 检查 `apps/proxy/views.py` 权限配置 |

### 问题8: 自动降级不工作

**症状:**
- 代理失败时没有自动降级到直连
- AI调用直接失败

**诊断步骤:**

1. 检查降级日志:
   - Django Admin → Proxy Usage Logs
   - 查找 `error_message` 包含 "degraded" 的日志

2. 检查ProxyManager配置:

```python
# Django Shell
from apps.proxy.services import ProxyManager

manager = ProxyManager()
print(f"自动降级启用: {manager.ENABLE_AUTO_DEGRADATION}")
```

**可能原因和解决方案:**

| 原因 | 解决方案 |
|------|----------|
| 降级功能被禁用 | 启用 `ProxyManager.ENABLE_AUTO_DEGRADATION = True` |
| 异常未被捕获 | 检查 `core/ai_client/base.py` 异常处理 |
| 日志未记录 | 检查降级日志记录开关 |

---

## 🔧 高级诊断

### 1. 启用调试日志

**修改配置:** `config/settings/base.py`

```python
LOGGING = {
    "loggers": {
        "apps.proxy": {
            "level": "DEBUG",  # 改为 DEBUG
            "handlers": ["file", "console"],
        },
    },
}
```

### 2. 查看Celery任务日志

```bash
# 实时查看健康检查任务日志
tail -f /var/log/celery/beat.log | grep check-proxy-health

# 查看Worker日志
tail -f /var/log/celery/worker.log | grep check-proxy-health
```

### 3. 数据库查询分析

```python
# Django Shell
from apps.proxy.models import ProxyConfig, ProxyUsageLog
from django.db import connection

# 查看最近失败的代理
failed_proxies = ProxyUsageLog.objects.filter(
    success=False
).values("proxy__name").annotate(
    count=Count("id")
).order_by("-count")

for proxy in failed_proxies[:5]:
    print(f"{proxy['proxy__name']}: {proxy['count']} 次失败")

# 查看慢查询（响应时间 > 1000ms）
slow_logs = ProxyUsageLog.objects.filter(
    success=True,
    response_time_ms__gt=1000
).count()

print(f"慢查询数量: {slow_logs}")
```

### 4. 网络诊断工具

```bash
# 测试代理连接
curl -v -x https://user:pass@proxy.example.com:8080 https://httpbin.org/ip

# 测试DNS解析
nslookup proxy.example.com

# 测试端口连通性
nc -zv proxy.example.com 8080

# 追踪路由
traceroute proxy.example.com
```

---

## 📞 获取帮助

### 日志收集

提交问题时，请提供以下信息:

1. **系统信息:**
   ```bash
   uname -a
   python --version
   uv --version
   ```

2. **代理配置信息:**
   - 代理名称、协议、主机、端口（脱敏）
   - 是否有认证

3. **错误日志:**
   ```bash
   # 代理应用日志
   tail -n 100 logs/proxy.log

   # Celery Beat日志
   tail -n 100 /var/log/celery/beat.log

   # Celery Worker日志
   tail -n 100 /var/log/celery/worker.log
   ```

4. **数据库查询结果:**
   ```python
   # Django Shell
   from apps.proxy.models import ProxyConfig, ProxyUsageLog

   # 代理配置
   print(ProxyConfig.objects.values())

   # 最近10条日志
   print(ProxyUsageLog.objects.order_by("-timestamp")[:10].values())
   ```

### 常用命令

```bash
# 重启Celery Beat
sudo supervisorctl restart celerybeat

# 清空代理日志（谨慎操作）
uv run python manage.py shell -c "from apps.proxy.models import ProxyUsageLog; ProxyUsageLog.objects.all().delete()"

# 重置所有代理健康状态
uv run python manage.py shell -c "from apps.proxy.models import ProxyConfig; ProxyConfig.objects.update(is_healthy=True, consecutive_failures=0, consecutive_successes=0)"

# 手动触发健康检查
uv run celery -A config call apps.proxy.tasks.check_proxy_health
```

---

## 📚 参考资源

- [安装指南](INSTALLATION.md)
- [配置指南](CONFIGURATION.md)
- [使用指南](USAGE.md)
- [API文档](API.md)

---

**故障排查支持:** 如问题未解决，请收集日志信息并提交Issue
