# 日志查询指南

> **Epic 7.3: 日志查询UI**
> **更新时间**: 2026-01-28

## 日志位置

### Django日志
- 路径: `/tmp/django.log`
- 格式: JSON结构化日志（使用python-json-logger）

### Celery日志
- 路径: `/tmp/celery_worker.log`
- 格式: 文本日志

### Redis日志
- 路径: `/tmp/redis.log`
- 格式: 文本日志

## 日志查询

### 查看Django日志

\`\`\`bash
tail -f /tmp/django.log
\`\`\`

### 查看Celery日志

\`\`\`bash
tail -f /tmp/celery_worker.log
\`\`\`

### 搜索错误日志

\`\`\`bash
grep "ERROR" /tmp/django.log
\`\`\`

## 日志分析

### 统计API调用

\`\`\`bash
grep "api_request" /tmp/django.log | wc -l
\`\`\`

### 查找慢请求

\`\`\`bash
grep "slow_request" /tmp/django.log
\`\`\`

### 分析Celery错误

\`\`\`bash
grep "ERROR" /tmp/celery_worker.log | tail -20
\`\`\`
