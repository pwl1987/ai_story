# 告警配置指南

## 概述

本文档说明如何配置AI Story系统的告警规则和通知渠道。

## 告警类型

### 1. Celery任务失败告警

当Celery任务失败时，系统会自动记录结构化日志。可以通过日志聚合工具设置告警。

**示例告警规则（Grafana Loki）:**
```yaml
alert: celery_task_failure
expr: |
  {logger="apps.celery", event="task_failure"}
  | logfmt
  | unwrap exception_message
  | quantile_over_time(0.9, 5m)
for: 1m
annotations:
  summary: "Celery任务失败: {{ $labels.task_name }}"
  description: |
    任务ID: {{ $labels.task_id }}
    任务名: {{ $labels.task_name }}
    异常类型: {{ $labels.exception_type }}
    异常信息: {{ $labels.exception_message }}
```

### 2. 慢任务告警

当任务执行时间超过阈值时，会记录WARNING级别日志。

**示例告警规则（Grafana Loki）:**
```yaml
alert: celery_slow_task
expr: |
  {logger="apps.celery", event="task_postrun", is_slow_task="true"}
  | logfmt
  | unwrap runtime_s
  | quantile_over_time(0.95, 10m)
for: 5m
annotations:
  summary: "检测到慢任务: {{ $labels.task_name }}"
  description: |
    任务ID: {{ $labels.task_id }}
    任务名: {{ $labels.task_name }}
    执行时间: {{ $value }}秒
```

### 3. API响应时间告警

当API响应时间超过阈值时，会记录WARNING级别日志。

**示例告警规则（Grafana Loki）:**
```yaml
alert: api_slow_response
expr: |
  {logger="apps.api", is_slow_request="true"}
  | logfmt
  | unwrap response_time_ms
  | quantile_over_time(0.95, 5m)
  > 500
for: 2m
annotations:
  summary: "API响应缓慢: {{ $labels.path }}"
  description: |
    请求路径: {{ $labels.path }}
    请求方法: {{ $labels.method }}
    响应时间: {{ $value }}ms
```

### 4. 健康检查失败告警

当健康检查显示组件不健康时触发。

**示例告警规则（Grafana Loki）:**
```yaml
alert: health_check_unhealthy
expr: |
  {path="/api/v1/health/"}
  | logfmt
  | json
  | unwrap status
  != "healthy"
for: 1m
annotations:
  summary: "系统健康检查失败"
  description: |
    检查失败的组件请查看健康检查详情
```

## 通知渠道配置

### 1. Webhook通知

配置Celery失败信号处理器发送Webhook通知。

**实现示例（config/celery.py）:**
```python
import requests

def send_webhook_notification(task_name, exception, task_id):
    """发送Webhook告警通知"""
    webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)
    if not webhook_url:
        return

    payload = {
        'task_name': task_name,
        'exception': str(exception),
        'task_id': task_id,
        'timestamp': time.time()
    }

    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")
```

**Settings配置:**
```python
# config/settings/base.py
ALERT_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### 2. 邮件通知

配置Django邮件发送告警通知。

**Settings配置:**
```python
# config/settings/base.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'alerts@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
ALERT_EMAIL_TO = ['ops@example.com']
```

## 日志查询示例

### 查询所有失败任务

**Grafana Loki查询:**
```
{logger="apps.celery", event="task_failure"}
| logfmt
| line_format "{{.task_name}}: {{.exception_message}}"
```

### 查询特定任务的执行时间

**Grafana Loki查询:**
```
{logger="apps.celery", event="task_postrun", task_name="execute_llm_stage"}
| logfmt
| unwrap runtime_s
```

### 查询慢请求

**Grafana Loki查询:**
```
{logger="apps.api", is_slow_request="true"}
| logfmt
| unwrap response_time_ms
| line_format "{{.path}}: {{.response_time_ms}}ms"
```

## 监控指标导出

系统已集成Prometheus metrics，可通过以下端点访问：

- **健康检查**: `GET /api/v1/health/metrics/`
- **API响应时间**: 自动记录在中间件
- **Celery任务**: 自动记录在信号处理器

## 告警最佳实践

### 1. 分级告警

- **P0 - 严重**: 系统不可用、数据丢失风险
- **P1 - 高**: 核心功能失败
- **P2 - 中**: 性能下降
- **P3 - 低**: 非关键问题

### 2. 告警静默

避免告警风暴，配置合理的静默规则：

```yaml
# 夜间静默非关键告警
mute_times:
  - start: "23:00"
    end: "07:00"
    severity: ["P2", "P3"]
```

### 3. 告警聚合

将相似告警聚合，避免重复通知：

```yaml
aggregation_rules:
  - match:
      task_name: "execute_*_stage"
    group_by: ["project_id"]
    wait: 5m
```

## 故障排查

### 常见问题

**Q: 告警未触发？**
- 检查日志级别配置
- 验证告警规则语法
- 确认日志输出正常

**Q: 误报太多？**
- 调整阈值（如`SLOW_TASK_THRESHOLD_S`）
- 增加观察期（`for`字段）
- 配置告警抑制规则

**Q: Webhook发送失败？**
- 验证URL可访问性
- 检查网络连接
- 查看Celery worker日志

## 配置示例

完整配置示例（config/settings/base.py）:

```python
# 慢任务阈值（秒）
SLOW_TASK_THRESHOLD_S = 60

# 慢API请求阈值（毫秒）
SLOW_REQUEST_THRESHOLD_MS = 500

# 告警Webhook
ALERT_WEBHOOK_URL = os.environ.get('ALERT_WEBHOOK_URL')

# 告警邮件
ALERT_EMAIL_TO = os.environ.get('ALERT_EMAIL_TO', '').split(',')

# 告警开关
ENABLE_ALERTS = os.environ.get('ENABLE_ALERTS', 'true').lower() == 'true'
```

## 参考资料

- [Grafana Loki告警文档](https://grafana.com/docs/loki/latest/alerting/)
- [Prometheus告警规则](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Celery信号文档](https://docs.celeryproject.org/en/stable/userguide/signals.html)
