# 代理管理系统 - 使用指南

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档介绍如何使用代理管理系统进行日常运维和操作。

**适用角色:**
- ✅ 系统管理员（Django Admin操作）
- ✅ 开发者（API调用和集成）

---

## 🖥️ Django Admin 使用

### 1. 访问 Admin 界面

**URL:** `http://localhost:8000/admin`

使用超级用户登录后，找到 **Proxy Configurations** 菜单。

### 2. 创建代理配置

**步骤:**

1. 点击 "Proxy Configurations" → "ADD PROXY CONFIGURATION"
2. 填写基本配置:
   - **Name（代理名称）**: 唯一标识，如 "美国代理-01"
   - **Protocol（协议）**: HTTP / HTTPS / SOCKS5
   - **Host（主机）**: 代理服务器地址，如 `proxy.example.com`
   - **Port（端口）**: 代理端口，如 `8080`
3. （可选）填写认证信息:
   - **Username（用户名）**: 代理认证用户名
   - **Password（密码）**: 代理认证密码
4. 状态配置:
   - **Is active（是否激活）**: ✅ 勾选
   - **Priority（优先级）**: 数字越小优先级越高，默认 `0`
5. 点击 "SAVE"

**示例配置:**

| 字段 | 示例值 |
|------|--------|
| Name | 美国代理-01 |
| Protocol | HTTPS |
| Host | us-proxy.example.com |
| Port | 8080 |
| Username | proxy_user |
| Password | my_secure_pass |
| Is active | ✅ |
| Priority | 0 |

### 3. 测试代理连接

**单个代理测试:**

1. 进入代理详情页
2. 点击右上角 "Actions" → "测试连接"
3. 查看结果消息:
   - ✅ 成功: `✓ 美国代理-01：连接成功！代理IP: 203.0.113.42，响应时间: 245ms`
   - ❌ 失败: `✗ 美国代理-01：连接失败：Connection timeout`

**批量测试:**

1. 在代理列表页勾选多个代理
2. 选择 "Action" → "测试连接"
3. 查看汇总结果:
   - `测试完成：成功 2 个，失败 1 个`

### 4. 查看使用日志

**步骤:**

1. 点击 "Proxy Usage Logs" 菜单
2. 使用筛选器:
   - **按代理**: 选择特定代理
   - **按AI提供商**: 选择 `OpenAIClient` / `ClaudeClient`
   - **按状态**: 成功 / 失败
   - **按时间**: 选择日期范围
3. 查看统计摘要:
   - 总调用次数
   - 成功率
   - 平均响应时间

### 5. 监控代理健康状态

**实时监控:**

在代理列表页查看以下字段:

| 字段 | 说明 | 示例值 |
|------|------|--------|
| **Is healthy** | 健康状态 | ✅ 健康 / ❌ 不健康 |
| **Last used at** | 最后使用时间 | 2026-01-31 10:30:00 |
| **Consecutive failures** | 连续失败次数 | 0 |
| **Consecutive successes** | 连续成功次数 | 5 |

**自动健康检查:**

- Celery Beat 每5分钟自动检查
- 连续失败 >3次 → 标记为不健康
- 连续成功 ≥3次 → 恢复为健康

### 6. 管理代理配置

**编辑代理:**

1. 点击代理名称进入详情页
2. 修改需要更新的字段
3. 点击 "SAVE"

**禁用代理:**

1. 进入代理详情页
2. 取消勾选 "Is active"
3. 点击 "SAVE"

**删除代理:**

⚠️ **警告**: 删除代理会同时删除所有关联的使用日志！

1. 在代理列表页勾选代理
2. 选择 "Action" → "Delete"
3. 确认删除

---

## 🔌 API 使用

### 1. 获取代理列表（选择器）

**端点:** `GET /api/v1/proxy/select/`

**权限:** 登录用户（IsAuthenticated）

**响应:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "美国代理-01",
            "protocol": "https",
            "host": "us-proxy.example.com",
            "port": 8080,
            "status": "✓ 健康"
        },
        {
            "id": 2,
            "name": "香港代理-01",
            "protocol": "http",
            "host": "hk-proxy.example.com",
            "port": 8080,
            "status": "✓ 健康"
        }
    ]
}
```

**注意:** 仅返回 `is_active=True` 且 `is_healthy=True` 的代理。

### 2. 测试代理连接

**端点:** `POST /api/v1/proxy/{id}/test_connection/`

**权限:** 登录用户（IsAuthenticated）

**请求:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/1/test_connection/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应（成功）:**
```json
{
    "success": true,
    "ip": "203.0.113.42",
    "response_time_ms": 245,
    "error": null
}
```

**响应（失败）:**
```json
{
    "success": false,
    "ip": null,
    "response_time_ms": 5000,
    "error": "Connection timeout"
}
```

### 3. 创建代理配置（Admin）

**端点:** `POST /api/v1/proxy/config/`

**权限:** 管理员（IsAdminUser）

**请求:**
```bash
curl -X POST http://localhost:8000/api/v1/proxy/config/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新加坡代理-01",
    "protocol": "https",
    "host": "sg-proxy.example.com",
    "port": 8443,
    "username": "proxy_user",
    "password": "my_pass",
    "is_active": true,
    "priority": 10
  }'
```

**响应:**
```json
{
    "id": 3,
    "name": "新加坡代理-01",
    "protocol": "https",
    "host": "sg-proxy.example.com",
    "port": 8443,
    "is_active": true,
    "is_healthy": true,
    "priority": 10,
    "created_at": "2026-01-31T10:30:00Z"
}
```

### 4. 更新代理配置（Admin）

**端点:** `PUT /api/v1/proxy/config/{id}/`

**权限:** 管理员（IsAdminUser）

**请求:**
```bash
curl -X PUT http://localhost:8000/api/v1/proxy/config/3/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新加坡代理-01",
    "protocol": "https",
    "host": "sg-proxy.example.com",
    "port": 8443,
    "is_active": false,
    "priority": 10
  }'
```

### 5. 删除代理配置（Admin）

**端点:** `DELETE /api/v1/proxy/config/{id}/`

**权限:** 管理员（IsAdminUser）

**请求:**
```bash
curl -X DELETE http://localhost:8000/api/v1/proxy/config/3/ \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 🚀 项目中使用代理

### 1. 在前端选择代理

**步骤:**

1. 创建新项目
2. 在 "代理配置" 下拉框中选择代理
3. 保存项目

**注意:**
- 下拉框仅显示健康且激活的代理
- 可选: 不选择代理则使用直连

### 2. 修改项目代理

**步骤:**

1. 进入项目详情页
2. 点击 "编辑" 按钮
3. 更改 "代理配置" 下拉框
4. 保存更改

### 3. 代理自动降级

当代理失败时，系统会自动降级到直连，无需手动干预。

**降级事件会记录到日志:**

```json
{
    "proxy": "美国代理-01",
    "ai_provider": "OpenAIClient",
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "response_time_ms": 0,
    "success": false,
    "error_message": "Proxy connection failed, degraded to direct connection",
    "timestamp": "2026-01-31T10:30:00Z"
}
```

---

## 📊 数据分析与报表

### 1. 代理成功率统计

**查询 Django Shell:**

```python
from apps.proxy.models import ProxyUsageLog
from django.db.models import Count, Q

# 统计每个代理的成功率
stats = ProxyUsageLog.objects.values("proxy__name").annotate(
    total=Count("id"),
    success=Count("id", filter=Q(success=True)),
    failure=Count("id", filter=Q(success=False))
).order_by("-total")

for stat in stats:
    success_rate = stat["success"] / stat["total"] * 100
    print(f"{stat['proxy__name']}: {success_rate:.1f}% ({stat['success']}/{stat['total']})")
```

**输出示例:**
```
美国代理-01: 98.5% (197/200)
香港代理-01: 99.0% (198/200)
新加坡代理-01: 95.0% (190/200)
```

### 2. 平均响应时间统计

```python
from django.db.models import Avg

stats = ProxyUsageLog.objects.values("proxy__name").annotate(
    avg_response_time=Avg("response_time_ms", filter=Q(success=True))
).order_by("avg_response_time")

for stat in stats:
    print(f"{stat['proxy__name']}: {stat['avg_response_time']:.0f}ms")
```

**输出示例:**
```
香港代理-01: 245ms
美国代理-01: 312ms
新加坡代理-01: 380ms
```

### 3. 导出使用日志

**Django Admin:**

1. 进入 "Proxy Usage Logs"
2. 筛选需要的数据
3. 点击 "导出CSV" Action

**API:**

```bash
# 使用 API 导出（需要实现自定义端点）
curl -X GET "http://localhost:8000/api/v1/proxy/logs/export/?format=csv&start=2026-01-01&end=2026-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o proxy_logs.csv
```

---

## 🎯 最佳实践

### 1. 代理配置命名规范

**推荐格式:** `{地区}-代理-{序号}`

**示例:**
- ✅ 美国代理-01
- ✅ 香港代理-02
- ✅ 新加坡代理-01
- ❌ test-proxy
- ❌ proxy1

### 2. 优先级设置

**策略:**

| 优先级 | 用途 | 示例 |
|--------|------|------|
| 0 | 主要代理 | 美国代理-01 |
| 10 | 备用代理 | 香港代理-01 |
| 20 | 测试代理 | 测试代理-01 |
| 100 | 禁用代理（保留） | 旧代理-01 |

### 3. 密码管理

**安全建议:**
- ✅ 使用强密码（16+字符，包含大小写、数字、符号）
- ✅ 定期更换代理密码
- ✅ 不同代理使用不同密码
- ❌ 不要在多个系统共享代理密码

### 4. 监控告警

**推荐监控指标:**

1. **健康状态**: 代理 `is_healthy=False` 时告警
2. **成功率**: 成功率 < 95% 时告警
3. **响应时间**: 平均响应时间 > 1000ms 时告警
4. **连续失败**: `consecutive_failures >= 3` 时告警

---

## 🔍 常见使用场景

### 场景1: 新增代理服务器

**目标:** 添加新的美国代理

**步骤:**

1. 获取代理服务器信息:
   - 协议: HTTPS
   - 主机: us-proxy.company.com
   - 端口: 8080
   - 用户名: company_user
   - 密码: secure_password

2. 在 Django Admin 创建代理:
   - Name: "美国代理-03"
   - Protocol: "HTTPS"
   - Host: "us-proxy.company.com"
   - Port: 8080
   - Username: "company_user"
   - Password: "secure_password"
   - Is active: ✅
   - Priority: 0

3. 测试连接:
   - 进入代理详情页
   - 点击 "测试连接"
   - 验证返回: ✅ 连接成功

### 场景2: 代理故障排查

**症状:** AI调用频繁失败

**排查步骤:**

1. 检查代理健康状态:
   - Django Admin → Proxy Configurations
   - 查看 `Is healthy` 列

2. 查看使用日志:
   - Proxy Usage Logs
   - 筛选该代理 + 最近1小时
   - 查看错误信息

3. 测试连接:
   - 使用 "测试连接" 功能
   - 查看响应时间

4. 根据错误信息处理:
   - `Connection timeout`: 检查网络连接
   - `HTTP error 407`: 检查用户名/密码
   - `HTTP error 403`: 检查代理IP是否被封禁

### 场景3: 代理轮换

**目标:** 从旧代理切换到新代理

**步骤:**

1. 创建新代理配置
2. 测试新代理连接
3. 修改项目代理配置:
   - 项目详情 → 编辑
   - 选择新代理
   - 保存
4. 验证AI调用正常
5. 禁用旧代理:
   - 旧代理详情 → 取消勾选 "Is active"
   - 保存

---

## 📚 参考资源

- [安装指南](INSTALLATION.md)
- [配置指南](CONFIGURATION.md)
- [API文档](API.md)
- [故障排查](TROUBLESHOOTING.md)

---

**使用支持:** 如遇问题，请查看 [故障排查指南](TROUBLESHOOTING.md)
