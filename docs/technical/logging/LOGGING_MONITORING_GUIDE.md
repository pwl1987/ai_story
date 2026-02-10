# 日志查询和告警配置指南

> 最后更新: 2026-01-28
> Epic 2: 系统可观测性 - Story 2.7

---

## 目录

1. [日志系统概览](#日志系统概览)
2. [日志查询方法](#日志查询方法)
3. [日志聚合和分析](#日志聚合和分析)
4. [告警配置](#告警配置)
5. [监控Dashboard](#监控dashboard)
6. [最佳实践](#最佳实践)
7. [故障排查指南](#故障排查指南)

---

## 日志系统概览

### 日志架构

```
┌─────────────────────────────────────────────────────────┐
│                   应用层 (Django)                        │
│  - API中间件 (Story 2.3 + 2.5)                          │
│  - Celery信号处理器 (Story 2.4 + 2.6)                   │
│  - 结构化日志输出                                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   日志层 (JSONFormatter)                │
│  - 结构化JSON格式                                        │
│  - 敏感数据过滤                                          │
│  - 请求上下文注入                                        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   输出层 (Handlers)                     │
│  - Console输出 (开发环境)                                │
│  - 文件轮转 (生产环境)                                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   聚合层 (Optional)                     │
│  - ELK Stack (Elasticsearch + Logstash + Kibana)       │
│  - Grafana Loki                                         │
│  - CloudWatch Logs (AWS)                                │
└─────────────────────────────────────────────────────────┘
```

### 日志格式

所有日志使用结构化JSON格式：

```json
{
  "message": "API Request: GET /api/v1/test/ - 0.18ms",
  "extra_fields": {
    "request_id": "127f33ff-7b5c-41aa-917c-00c5a1c9a251",
    "method": "GET",
    "path": "/api/v1/test/",
    "response_time_ms": 0.18,
    "is_slow_request": false,
    "had_error": false
  },
  "timestamp": "2026-01-28 06:49:03,804",
  "level": "INFO",
  "logger": "apps.api",
  "process_id": 1370283,
  "thread_id": 138616094758720,
  "module": "api_response_time",
  "function": "_log_response_time",
  "line": 107,
  "thread_name": "MainThread"
}
```

### 日志级别使用规范

| 级别 | 数值 | 使用场景 | 示例 |
|------|------|----------|------|
| DEBUG | 10 | 详细的调试信息 | 函数参数、中间变量 |
| INFO | 20 | 正常业务流程 | API请求、任务完成 |
| WARNING | 30 | 潜在问题 | 慢请求、任务重试 |
| ERROR | 40 | 错误但可恢复 | API异常、任务失败 |
| CRITICAL | 50 | 严重错误 | 系统崩溃、数据丢失 |

---

## 日志查询方法

### 方法1: 命令行查询 (开发环境)

#### 使用 `jq` 查询JSON日志

```bash
# 查看所有API请求日志
tail -f logs/django.log | jq 'select(.logger == "apps.api")'

# 查找慢请求 (>500ms)
tail -f logs/django.log | jq 'select(.extra_fields.response_time_ms > 500)'

# 查找特定request_id的日志
tail -f logs/django.log | jq 'select(.extra_fields.request_id == "xxx")'

# 查找错误日志
tail -f logs/django.log | jq 'select(.level == "ERROR")'

# 统计API响应时间P95
tail -n 10000 logs/django.log | \
  jq -r '.extra_fields.response_time_ms' | \
  awk '{print $1}' | sort -n | awk 'NR==950'
```

#### 使用 `grep` 查询

```bash
# 查找包含特定文本的日志
grep "API Error" logs/django.log | jq

# 查找特定时间范围的日志
grep "2026-01-28 06:" logs/django.log | jq

# 查找特定用户的操作日志
grep "user_id\":42" logs/django.log | jq
```

### 方法2: Python脚本查询

```python
#!/usr/bin/env python
"""
日志查询脚本示例
"""

import json
from pathlib import Path

def query_logs(log_file, filters=None):
    """
    查询日志

    Args:
        log_file: 日志文件路径
        filters: 过滤条件字典

    Returns:
        匹配的日志列表
    """
    results = []

    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)

                # 应用过滤条件
                if filters:
                    match = True
                    for key, value in filters.items():
                        if log_entry.get(key) != value:
                            match = False
                            break

                    if not match:
                        continue

                results.append(log_entry)
            except json.JSONDecodeError:
                continue

    return results


# 示例：查找所有慢请求
slow_requests = query_logs('logs/django.log', {
    'logger': 'apps.api'
})

slow_requests = [
    r for r in slow_requests
    if r.get('extra_fields', {}).get('response_time_ms', 0) > 500
]

print(f"找到 {len(slow_requests)} 个慢请求")
for req in slow_requests[:10]:  # 只显示前10个
    print(f"- {req['extra_fields']['path']}: {req['extra_fields']['response_time_ms']}ms")
```

### 方法3: Elasticsearch查询 (生产环境)

#### 基础查询

```json
GET /django-logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"logger": "apps.api"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "sort": [{"timestamp": {"order": "desc"}}],
  "size": 100
}
```

#### 聚合查询 (统计慢请求)

```json
GET /django-logs-*/_search
{
  "query": {
    "range": {
      "extra_fields.response_time_ms": {
        "gte": 500
      }
    }
  },
  "aggs": {
    "slow_paths": {
      "terms": {
        "field": "extra_fields.path",
        "size": 10
      },
      "aggs": {
        "avg_response_time": {
          "avg": {"field": "extra_fields.response_time_ms"}
        }
      }
    }
  }
}
```

---

## 日志聚合和分析

### 1. API响应时间分析

#### 计算P95/P99响应时间

```python
#!/usr/bin/env python
import numpy as np
import json

def calculate_percentiles(log_file):
    """计算API响应时间的P95和P99"""
    response_times = []

    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)
                rt = log_entry.get('extra_fields', {}).get('response_time_ms')
                if rt is not None:
                    response_times.append(rt)
            except json.JSONDecodeError:
                continue

    if not response_times:
        return None

    return {
        'count': len(response_times),
        'mean': np.mean(response_times),
        'p50': np.percentile(response_times, 50),
        'p95': np.percentile(response_times, 95),
        'p99': np.percentile(response_times, 99),
        'max': max(response_times)
    }

# 使用示例
stats = calculate_percentiles('logs/django.log')
print(f"API响应时间统计:")
print(f"- 请求数: {stats['count']}")
print(f"- 平均值: {stats['mean']:.2f}ms")
print(f"- P50: {stats['p50']:.2f}ms")
print(f"- P95: {stats['p95']:.2f}ms")
print(f"- P99: {stats['p99']:.2f}ms")
print(f"- 最大值: {stats['max']:.2f}ms")
```

### 2. Celery任务执行时间分析

```python
#!/usr/bin/env python
import json
from collections import defaultdict

def analyze_task_performance(log_file):
    """分析Celery任务性能"""
    tasks = defaultdict(lambda: {
        'count': 0,
        'runtimes': [],
        'slow_count': 0
    })

    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)

                # 只分析任务完成日志
                if log_entry.get('event') != 'task_postrun':
                    continue

                task_name = log_entry.get('task_name')
                runtime_s = log_entry.get('extra_fields', {}).get('runtime_s')
                is_slow = log_entry.get('extra_fields', {}).get('is_slow_task', False)

                if task_name and runtime_s is not None:
                    tasks[task_name]['count'] += 1
                    tasks[task_name]['runtimes'].append(runtime_s)
                    if is_slow:
                        tasks[task_name]['slow_count'] += 1
            except json.JSONDecodeError:
                continue

    # 计算统计信息
    results = {}
    for task_name, data in tasks.items():
        results[task_name] = {
            'count': data['count'],
            'avg_runtime': sum(data['runtimes']) / len(data['runtimes']),
            'max_runtime': max(data['runtimes']),
            'slow_rate': data['slow_count'] / data['count']
        }

    return results

# 使用示例
tasks = analyze_task_performance('logs/django.log')
print("Celery任务性能分析:")
for task_name, stats in sorted(tasks.items(), key=lambda x: x[1]['avg_runtime'], reverse=True):
    print(f"\n{task_name}:")
    print(f"  执行次数: {stats['count']}")
    print(f"  平均耗时: {stats['avg_runtime']:.2f}s")
    print(f"  最大耗时: {stats['max_runtime']:.2f}s")
    print(f"  慢任务率: {stats['slow_rate']:.1%}")
```

### 3. 错误率分析

```python
#!/usr/bin/env python
import json
from datetime import datetime, timedelta

def calculate_error_rate(log_file, hours=1):
    """计算过去N小时内的错误率"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    total_requests = 0
    error_requests = 0
    errors_by_type = defaultdict(int)

    with open(log_file, 'r') as f:
        for line in f:
            try:
                log_entry = json.loads(line)

                # 解析时间戳
                timestamp_str = log_entry.get('timestamp', '')
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')

                if timestamp < cutoff_time:
                    continue

                # 统计API请求
                if log_entry.get('logger') == 'apps.api':
                    total_requests += 1

                    if log_entry.get('level') in ('ERROR', 'CRITICAL'):
                        error_requests += 1
                        error_type = log_entry.get('extra_fields', {}).get('error_type', 'Unknown')
                        errors_by_type[error_type] += 1
            except (json.JSONDecodeError, ValueError):
                continue

    error_rate = error_requests / total_requests if total_requests > 0 else 0

    return {
        'total_requests': total_requests,
        'error_requests': error_requests,
        'error_rate': error_rate,
        'errors_by_type': dict(errors_by_type)
    }
```

---

## 告警配置

### 1. 基于日志文件的告警

#### 使用Fail2ban监控错误日志

```ini
# /etc/fail2ban/filter.d/django-errors.conf
[Definition]
failregex = ^.*"level": "ERROR".*"error_type": "<ERROR_TYPE>".*$
ignoreregex =

# /etc/fail2ban/jail.d/django.conf
[django-errors]
enabled = true
filter = django-errors
logpath = /path/to/logs/django.log
maxretry = 10
findtime = 3600
bantime = 3600
action = iptables-allports[name=django]
```

### 2. 使用Prometheus + Alertmanager

#### 日志导出指标

```python
# core/metrics.py
from prometheus_client import Counter, Histogram

# API请求计数
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'path', 'status']
)

# API响应时间
api_response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['method', 'path']
)

# Celery任务执行时间
celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name']
)

# Celery任务失败计数
celery_task_failures = Counter(
    'celery_task_failures_total',
    'Total Celery task failures',
    ['task_name', 'exception_type']
)
```

#### Prometheus告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: api_alerts
    rules:
      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          rate(api_requests_total{status=~"5.."}[5m]) /
          rate(api_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率过高"
          description: "{{ $labels.path }} 错误率 {{ $value | humanizePercentage }}"

      # 慢请求告警
      - alert: SlowAPIRequests
        expr: |
          histogram_quantile(0.95,
            rate(api_response_time_seconds_bucket[5m])
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过长"
          description: "P95响应时间 {{ $value }}s"

  - name: celery_alerts
    rules:
      # Celery任务失败率
      - alert: HighCeleryFailureRate
        expr: |
          rate(celery_task_failures_total[5m]) /
          rate(celery_task_duration_count[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery任务失败率过高"
          description: "{{ $labels.task_name }} 失败率 {{ $value | humanizePercentage }}"

      # 慢任务告警
      - alert: SlowCeleryTasks
        expr: |
          histogram_quantile(0.95,
            sum(rate(celery_task_duration_seconds_bucket[5m])) by (task_name, le)
          ) > 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery任务执行时间过长"
          description: "{{ $labels.task_name }} P95执行时间 {{ $value }}s"
```

### 3. 使用ELK Watcher告警

```json
{
  "trigger": {
    "schedule": {
      "interval": "5m"
    }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["django-logs-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"range": {"timestamp": {"gte": "now-5m"}}},
                {"terms": {"level": ["ERROR", "CRITICAL"]}}
              ]
            }
          },
          "aggs": {
            "error_count": {"value_count": {"field": "request_id"}}
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.aggregations.error_count.value": {
        "gt": 100
      }
    }
  },
  "actions": {
    "email_admin": {
      "email": {
        "to": "admin@example.com",
        "subject": "告警: 错误日志过多",
        "body": "检测到 {{ ctx.payload.aggregations.error_count.value }} 个错误"
      }
    }
  }
}
```

### 4. CloudWatch 告警 (AWS)

```python
# 创建CloudWatch Logs指标过滤器
import boto3

logs_client = boto3.client('logs')

# 为慢请求创建指标
logs_client.put_metric_filter(
    logGroupName='/aws/django/production',
    filterName='slow-api-requests',
    filterPattern='[response_time_ms > 500]',
    metricTransformations=[
        {
            'metricName': 'SlowAPIRequests',
            'metricNamespace': 'Django/Production',
            'metricValue': '1',
            'defaultValue': 0
        }
    ]
)

# 创建告警
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_alarm(
    AlarmName='django-slow-requests-alarm',
    AlarmDescription='Alert when API requests are too slow',
    Namespace='Django/Production',
    MetricName='SlowAPIRequests',
    Statistic='Sum',
    Period=300,
    EvaluationPeriods=1,
    Threshold=10,
    ComparisonOperator='GreaterThanThreshold',
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:123456789:alerts']
)
```

---

## 监控Dashboard

### Grafana Dashboard配置

#### 导入JSON配置

```json
{
  "dashboard": {
    "title": "Django API & Celery监控",
    "panels": [
      {
        "title": "API请求速率",
        "targets": [
          {
            "expr": "sum(rate(api_requests_total[5m])) by (path)",
            "legendFormat": "{{path}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "API响应时间P95",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(api_response_time_seconds_bucket[5m])) by (path, le))",
            "legendFormat": "{{path}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "API错误率",
        "targets": [
          {
            "expr": "sum(rate(api_requests_total{status=~\"5..\"}[5m])) / sum(rate(api_requests_total[5m]))",
            "legendFormat": "错误率"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Celery任务执行时间",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(celery_task_duration_seconds_bucket[5m])) by (task_name, le))",
            "legendFormat": "{{task_name}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Celery任务失败率",
        "targets": [
          {
            "expr": "sum(rate(celery_task_failures_total[5m])) by (task_name)",
            "legendFormat": "{{task_name}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### Kibana Dashboard配置

#### 创建可视化

```json
{
  "visState": {
    "title": "慢请求Top 10",
    "type": "table",
    "params": {
      "sort": [
        ["extra_fields.response_time_ms", "desc"]
      ],
      "perPage": 10
    }
  },
  "aggs": [
    {
      "id": "1",
      "type": "terms",
      "schema": "segment",
      "params": {
        "field": "extra_fields.path",
        "size": 10
      }
    },
    {
      "id": "2",
      "type": "avg",
      "schema": "metric",
      "params": {
        "field": "extra_fields.response_time_ms"
      }
    }
  ]
}
```

---

## 最佳实践

### 1. 日志记录规范

#### ✅ DO (推荐做法)

```python
# 结构化日志
logger.info(
    "User logged in",
    extra={'extra_fields': {
        'user_id': user.id,
        'ip_address': request.META['REMOTE_ADDR'],
        'success': True
    }}
)

# 记录关键业务事件
logger.info(
    "Order created",
    extra={'extra_fields': {
        'order_id': order.id,
        'amount': float(order.total_amount),
        'user_id': order.user.id
    }}
)
```

#### ❌ DON'T (避免的做法)

```python
# 字符串拼接 (性能差，不利于查询)
logger.info("User " + str(user.id) + " logged in from " + ip)

# 过于详细的日志
logger.debug(f"Variable x = {x}, y = {y}, z = {z}")  # 除非调试需要

# 记录敏感信息
logger.info(f"Password: {password}")  # 永远不要这样做！
```

### 2. 日志级别选择

| 场景 | 级别 | 示例 |
|------|------|------|
| 正常业务流程 | INFO | 用户登录、订单创建 |
| 性能问题 | WARNING | 慢请求 (>500ms) |
| 可恢复的错误 | ERROR | API调用失败、数据库连接失败 |
| 需要立即处理 | CRITICAL | 磁盘满、内存溢出 |
| 开发调试 | DEBUG | 函数参数、中间变量 |

### 3. 日志量控制

```python
# 生产环境应控制日志量
LOGGING = {
    'loggers': {
        'django': {
            'level': 'WARNING',  # Django框架日志
            'propagate': False,
        },
        'apps': {
            'level': 'INFO',  # 应用日志
            'propagate': False,
        },
    }
}
```

### 4. 性能考虑

```python
# 使用惰性日志 (级别检查)
if logger.isEnabledFor(logging.DEBUG):
    expensive_operation = calculate_something()
    logger.debug(f"Result: {expensive_operation}")

# 避免在热路径中记录过多日志
def hot_path_function():
    # 不要在循环中记录日志
    for item in large_list:
        process(item)  # 不要在循环内记录日志

    # 在循环外记录摘要
    logger.info(f"Processed {len(large_list)} items")
```

### 5. 敏感数据保护

```python
# 敏感字段过滤
SENSITIVE_FIELDS = {
    'password', 'api_key', 'secret', 'token',
    'credit_card', 'ssn', 'account_number'
}

def filter_sensitive_data(data):
    """过滤敏感数据"""
    if isinstance(data, dict):
        return {
            k: '***FILTERED***' if k.lower() in SENSITIVE_FIELDS else filter_sensitive_data(v)
            for k, v in data.items()
        }
    return data
```

---

## 故障排查指南

### 问题1: 日志文件过大

**症状:** 日志文件占用大量磁盘空间

**解决方案:**

1. 配置日志轮转
```python
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 5,
        }
    }
}
```

2. 设置日志保留策略
```bash
# 只保留最近7天的日志
find logs/ -name "*.log" -mtime +7 -delete
```

### 问题2: 日志丢失

**症状:** 某些日志没有记录到文件

**排查步骤:**

1. 检查日志级别配置
```python
logger.setLevel(logging.DEBUG)  # 临时设置DEBUG级别
```

2. 检查handler配置
```python
import logging
root_logger = logging.getLogger()
print("Handlers:", root_logger.handlers)
print("Level:", root_logger.level)
```

3. 检查日志权限
```bash
ls -la logs/django.log
```

### 问题3: 慢请求无法定位

**解决方案:**

1. 记录请求ID
```python
# 在中间件中生成request_id
request.request_id = str(uuid.uuid4())
```

2. 关联所有日志
```python
logger.info(
    "Processing request",
    extra={'extra_fields': {'request_id': request.request_id}}
)
```

3. 查询时使用request_id
```bash
grep "request_id\":\"xxx" logs/django.log | jq
```

### 问题4: Celery任务无日志

**排查步骤:**

1. 检查Celery worker是否运行
```bash
celery -A config inspect active
```

2. 检查worker日志级别
```bash
celery -A config worker -l debug
```

3. 验证信号处理器连接
```python
from config.celery import task_prerun_handler
from celery.signals import task_prerun

# 检查是否已连接
print(task_prerun.receivers)
```

---

## 参考资源

### 官方文档

- [Django Logging](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Celery Signals](https://docs.celeryproject.org/en/stable/userguide/signals.html)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)

### 工具

- [jq](https://stedolan.github.io/jq/) - JSON日志查询工具
- [Grafana](https://grafana.com/) - 开源监控Dashboard
- [ELK Stack](https://www.elastic.co/what-is/elk-stack) - 日志聚合分析

### 社区资源

- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [Monitoring Best Practices](https://www.datadoghq.com/blog/engineering/monitoring-101-alerting-with-the-graphite-period/)

---

## 附录

### A. 日志查询速查表

```bash
# 查看实时日志
tail -f logs/django.log | jq

# 统计错误数量
grep '"level": "ERROR"' logs/django.log | wc -l

# 查找慢请求
jq 'select(.extra_fields.response_time_ms > 500)' logs/django.log

# 统计API请求数
jq 'select(.logger == "apps.api")' logs/django.log | wc -l

# 查找特定时间范围
grep "2026-01-28 06:" logs/django.log | jq

# 导出为CSV
jq -r '[.timestamp, .level, .message] | @csv' logs/django.log > output.csv
```

### B. 告警配置模板

```yaml
# 通用告警规则模板
alerts:
  - name: high_error_rate
    condition: error_rate > 0.05
    duration: 5m
    severity: critical
    notification:
      - email: ops@example.com
      - slack: #alerts

  - name: slow_response_time
    condition: p95_response_time > 1s
    duration: 10m
    severity: warning
    notification:
      - slack: #performance
```

---

*最后更新: 2026-01-28*
*维护者: AI Story开发团队*
