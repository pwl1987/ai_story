# 日志管理指南

> **Epic 7.3: 日志查询UI**
> **更新时间**: 2026-01-28

---

## 概述

AI Story生成系统使用结构化日志记录，支持JSON格式和文本格式，便于查询和分析。

---

## 日志配置

### Django日志配置

**配置文件**: `config/settings/base.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django.log',
            'formatter': 'json'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
}
```

---

### Celery日志配置

**配置文件**: `config/celery.py`

```python
worker_log_file = '/tmp/celery_worker.log'
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
```

---

## 日志位置

### Django日志
- **路径**: `/tmp/django.log`
- **格式**: JSON结构化日志（使用python-json-logger）
- **轮转**: 需要配置logrotate

### Celery日志
- **路径**: `/tmp/celery_worker.log`
- **格式**: 文本日志
- **轮转**: 需要配置logrotate

### Redis日志
- **路径**: `/tmp/redis.log`
- **格式**: 文本日志
- **配置**: Docker容器stdout

---

## 日志格式

### Django JSON日志示例

```json
{
  "asctime": "2026-01-28 10:30:45,123",
  "name": "django.request",
  "levelname": "INFO",
  "message": "GET /api/v1/projects/ 200",
  "duration_ms": 45,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "endpoint": "/api/v1/projects/",
  "method": "GET",
  "status": 200
}
```

### Celery文本日志示例

```
[2026-01-28 10:30:45: INFO/MainProcess][tasks.execute_full_pipeline(a62bdbb6-5874-481d-ad0c-b0a289584d20)] Starting pipeline execution
[2026-01-28 10:30:46: INFO/ForkPoolWorker-2][tasks.process_rewrite_stage] Rewrite stage completed
[2026-01-28 10:30:47: INFO/ForkPoolWorker-3][tasks.process_storyboard_stage] Storyboard stage completed
```

---

## 日志查询

### 查看Django日志

**实时查看**:
```bash
tail -f /tmp/django.log
```

**查看最近100行**:
```bash
tail -n 100 /tmp/django.log
```

**JSON格式化输出**:
```bash
cat /tmp/django.log | jq '.'
```

---

### 查看Celery日志

**实时查看**:
```bash
tail -f /tmp/celery_worker.log
```

**查看特定任务**:
```bash
grep "a62bdbb6-5874-481d-ad0c-b0a289584d20" /tmp/celery_worker.log
```

---

### 搜索错误日志

**Django错误**:
```bash
grep "ERROR" /tmp/django.log | jq '.'
```

**Celery错误**:
```bash
grep "ERROR" /tmp/celery_worker.log | tail -20
```

---

### 按时间范围查询

**使用jq**:
```bash
cat /tmp/django.log | jq 'select(.asctime >= "2026-01-28 10:00:00" and .asctime <= "2026-01-28 11:00:00")'
```

**使用awk**:
```bash
awk '/2026-01-28 10:00:00/,/2026-01-28 11:00:00/' /tmp/django.log
```

---

## 日志分析

### 统计API调用

```bash
# 总调用次数
grep "api_request" /tmp/django.log | wc -l

# 按端点统计
cat /tmp/django.log | jq -r '.endpoint' | sort | uniq -c | sort -rn

# 按状态码统计
cat /tmp/django.log | jq -r '.status' | sort | uniq -c | sort -rn
```

---

### 查找慢请求

```bash
# 查找响应时间超过1秒的请求
cat /tmp/django.log | jq 'select(.duration_ms > 1000)'

# 按响应时间排序（最慢的10个）
cat /tmp/django.log | jq -s 'sort_by(.duration_ms) | reverse | .[0:10]'
```

---

### 分析Celery任务执行

```bash
# 统计任务完成数量
grep "stage completed" /tmp/celery_worker.log | wc -l

# 查看失败的任务
grep "Task failed" /tmp/celery_worker.log | tail -20

# 统计各阶段执行次数
grep -oE "(rewrite|storyboard|image_generation|camera_movement|video_generation) stage completed" /tmp/celery_worker.log | sort | uniq -c
```

---

### 日志聚合分析

**使用awk统计**:
```bash
# 统计每分钟的请求数
awk '{print substr($1, 12, 5)}' /tmp/django.log | sort | uniq -c

# 统计错误率
ERROR_COUNT=$(grep -c "ERROR" /tmp/django.log)
TOTAL_COUNT=$(wc -l < /tmp/django.log)
echo "Error rate: $(echo "scale=2; $ERROR_COUNT * 100 / $TOTAL_COUNT" | bc)%"
```

---

## 日志轮转

### 配置logrotate

**配置文件**: `/etc/logrotate.d/ai-story`

```
/tmp/django.log
/tmp/celery_worker.log
/tmp/redis.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        # 发送SIGHUP信号重新打开日志文件
        kill -USR1 $(cat /tmp/django.pid 2>/dev/null) 2>/dev/null || true
        kill -USR1 $(cat /tmp/celery.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
```

**手动测试**:
```bash
sudo logrotate -f /etc/logrotate.d/ai-story
```

---

## 日志级别

| 级别 | 描述 | 使用场景 |
|------|------|---------|
| DEBUG | 调试信息 | 开发环境详细日志 |
| INFO | 一般信息 | 正常业务流程 |
| WARNING | 警告信息 | 潜在问题 |
| ERROR | 错误信息 | 异常和错误 |
| CRITICAL | 严重错误 | 系统级故障 |

**修改日志级别**:

在 `config/settings/base.py` 中:
```python
LOGGING = {
    'handlers': {
        'file': {
            'level': 'DEBUG',  # 修改这里
            ...
        }
    }
}
```

---

## 日志最佳实践

### 1. 结构化日志

使用JSON格式便于机器解析:
```python
import jsonlogging
logger = logging.getLogger(__name__)
logger.info({"event": "user_login", "user_id": user.id})
```

### 2. 上下文信息

记录关键上下文:
```python
logger.info({
    "event": "api_request",
    "endpoint": request.path,
    "method": request.method,
    "user_id": request.user.id,
    "duration_ms": duration
})
```

### 3. 敏感信息脱敏

避免记录敏感信息:
```python
# ❌ 不要这样做
logger.info({"password": user.password})

# ✅ 应该这样做
logger.info({"user_id": user.id})
```

### 4. 异常堆栈

完整记录异常信息:
```python
try:
    risky_operation()
except Exception as e:
    logger.exception({"event": "operation_failed", "error": str(e)})
```

---

## 故障排查

### 问题1: 日志文件过大

**症状**: 日志文件占用大量磁盘空间

**解决方案**:
1. 配置logrotate自动轮转
2. 降低日志级别（INFO → WARNING）
3. 清理历史日志:
   ```bash
   rm /tmp/django.log.1
   ```

### 问题2: 日志丢失

**症状**: 部分日志没有写入文件

**可能原因**:
- 日志文件权限问题
- 磁盘空间不足
- 日志缓冲未刷新

**解决方案**:
```bash
# 检查权限
ls -l /tmp/django.log

# 检查磁盘空间
df -h

# 手动刷新日志
import logging
logging.shutdown()
```

### 问题3: JSON格式无法解析

**症状**: `jq` 命令解析失败

**可能原因**:
- 日志格式不是纯JSON
- 多行JSON记录

**解决方案**:
```bash
# 验证JSON格式
cat /tmp/django.log | jq '.' 2>&1 | head -20

# 提取有效JSON行
grep '^{' /tmp/django.log | jq '.'
```

---

## 相关文档

- [性能监控指南](./PERFORMANCE_MONITORING.md)
- [API文档](http://localhost:8000/api/schema/redoc/)
- [故障排查手册](../TROUBLESHOOTING.md)

---

*最后更新: 2026-01-28*
*Epic 7.3: 日志查询UI*
