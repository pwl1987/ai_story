# 性能监控指南

> **Epic 7.2: 性能监控仪表板**
> **更新时间**: 2026-01-28

---

## 概述

AI Story生成系统使用Prometheus + Grafana进行性能监控，实时追踪系统关键指标。

---

## 监控架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Django     │────▶│  Prometheus  │────▶│  Grafana    │
│  + Celery   │指标 │  (指标存储)   │查询 │  (可视化)   │
└─────────────┘     └──────────────┘     └─────────────┘
```

---

## 已集成的监控指标

### 1. API响应时间监控 (Epic 2.5)

**实现位置**: `core/middleware/api_response_time.py`

**指标名称**:
- `http_request_duration_seconds` (Histogram)
  - 标签: `endpoint_type`, `method`, `status`
  - 单位: 秒

**查询示例**:
```promql
# API 95分位延迟
histogram_quantile(0.95, http_request_duration_seconds_bucket{endpoint_type="api"})*1000

# 平均延迟
rate(http_request_duration_seconds_sum{endpoint_type="api"}[5m]) /
rate(http_request_duration_seconds_count{endpoint_type="api"}[5m]) * 1000
```

---

### 2. Celery任务执行时间监控 (Epic 2.6)

**实现位置**: `config/celery.py`

**指标名称**:
- `celery_task_duration_seconds` (Histogram)
  - 标签: `task_name`, `status`
  - 单位: 秒
- `celery_task_count_total` (Counter)
  - 标签: `task_name`, `status`

**查询示例**:
```promql
# Celery任务95分位执行时间
histogram_quantile(0.95, celery_task_duration_seconds_bucket)*1000

# 任务执行速率
rate(celery_task_count_total[1m])

# 任务失败率
rate(celery_task_count_total{status="failed"}[5m]) /
rate(celery_task_count_total[5m]) * 100
```

---

### 3. API请求计数 (Epic 2.5)

**指标名称**:
- `api_request_count_total` (Counter)
  - 标签: `endpoint`, `method`, `status`

**查询示例**:
```promql
# API请求速率 (每秒请求数)
rate(api_request_count_total[1m])

# 按状态码统计
sum by(status) (rate(api_request_count_total[5m]))
```

---

## Grafana仪表板

### 导入仪表板

**配置文件**: `backend/grafana_dashboard.json`

**导入步骤**:

1. 登录Grafana (`http://localhost:3000`)
2. 点击 "+" → "Import"
3. 上传 `grafana_dashboard.json` 或粘贴JSON内容
4. 选择Prometheus数据源
5. 点击"Import"

---

### 仪表板面板

| 面板ID | 面板名称 | 类型 | 描述 |
|--------|---------|------|------|
| 1 | System Overview | Stat | Django/Celery/Redis运行状态 |
| 2 | API Response Time | Graph | API 95分位响应时间(ms) |
| 3 | API Request Rate | Graph | API请求速率(请求/秒) |
| 4 | Celery Task Duration | Graph | Celery任务95分位执行时间(ms) |
| 5 | Celery Task Rate | Graph | Celery任务执行速率(任务/秒) |
| 6 | Celery Task Errors | Graph | Celery任务错误速率(错误/秒) |
| 7 | Memory Usage | Graph | Django和Celery内存使用(MB) |
| 8 | CPU Usage | Graph | Django和Celery CPU使用率(%) |

---

## Prometheus配置

### 安装Prometheus

**Docker方式**:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

**配置文件** (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'celery-exporter'
    static_configs:
      - targets: ['localhost:9540']
```

---

## Django Prometheus集成

### 安装依赖

```bash
uv add prometheus-client
```

### 配置Django暴露指标

在 `config/urls.py` 中:
```python
from django_prometheus.urls import urlpatterns as prometheus_urls

urlpatterns += [
    path('metrics/', prometheus_urls)
]
```

---

## Celery Exporter配置

### 安装Celery Exporter

```bash
docker run -d \
  --name celery-exporter \
  -p 9540:9540 \
  -e CELERY_BROKER_URL=redis://localhost:6379/0 \
  --network host \
  frodenas/celery-exporter:latest
```

**访问**: `http://localhost:9540/metrics`

---

## 告警规则

### API响应时间告警

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95,
            http_request_duration_seconds_bucket{endpoint_type="api"}
          ) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API响应时间过高"
          description: "95分位响应时间超过1秒"
```

### Celery任务失败告警

```yaml
  - alert: HighCeleryFailureRate
    expr: |
      rate(celery_task_count_total{status="failed"}[5m]) /
      rate(celery_task_count_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Celery任务失败率过高"
      description: "任务失败率超过10%"
```

---

## 性能基准

### 目标指标

| 指标 | 目标值 | 当前状态 |
|------|--------|---------|
| API 95分位延迟 | < 500ms | ✅ 达标 |
| API平均延迟 | < 200ms | ✅ 达标 |
| Celery任务95分位 | < 30s | ✅ 达标 |
| Celery任务失败率 | < 1% | ✅ 达标 |
| 内存使用 (Django) | < 500MB | ✅ 达标 |
| 内存使用 (Celery) | < 300MB | ✅ 达标 |

---

## 故障排查

### 问题1: Prometheus无法抓取指标

**症状**: Prometheus显示"Targets down"

**排查步骤**:
1. 检查Django是否运行: `curl http://localhost:8000/metrics/`
2. 检查网络连通性: `nc -zv localhost 8000`
3. 检查Prometheus配置: `prometheus.yml` 中的 `targets`

---

### 问题2: Grafana面板显示"No data"

**症状**: Grafana面板空白

**排查步骤**:
1. 检查Prometheus数据源配置
2. 验证Prometheus有数据: `curl http://localhost:9090/api/v1/query?query=up`
3. 检查时间范围是否正确

---

### 问题3: 指标数据缺失

**症状**: 部分指标没有数据

**可能原因**:
- Django Prometheus中间件未启用
- Celery任务未执行
- Exporter未启动

**解决方案**:
1. 检查 `config/settings/base.py` 中的 `INSTALLED_APPS`
2. 验证Celery Worker运行状态
3. 重启Exporter

---

## 快速启动

### 一键启动监控栈

```bash
#!/bin/bash
# start_monitoring.sh

echo "启动Redis..."
docker run -d --name happy-redis -p 6379:6379 redis:7-alpine

echo "启动Prometheus..."
docker run -d --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest

echo "启动Grafana..."
docker run -d --name grafana \
  -p 3000:3000 \
  grafana/grafana:latest

echo "启动Celery Exporter..."
docker run -d --name celery-exporter \
  -p 9540:9540 \
  -e CELERY_BROKER_URL=redis://localhost:6379/0 \
  frodenas/celery-exporter:latest

echo "监控栈启动完成!"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3000 (admin/admin)"
```

---

## 相关文档

- [Grafana Dashboard配置](../grafana_dashboard.json)
- [日志查询指南](./LOGGING.md)
- [健康检查端点](../HEALTH_CHECK.md)

---

*最后更新: 2026-01-28*
*Epic 7.2: 性能监控仪表板*
