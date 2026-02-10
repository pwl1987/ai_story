# 代理管理系统 - API文档

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档详细描述代理管理系统的所有API端点。

**基础URL:** `http://localhost:8000/api/v1/proxy`

**认证方式:** Bearer Token (JWT)

---

## 🔐 认证

所有API请求需要在Header中携带认证Token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/proxy/select/
```

---

## 📡 API端点

### 1. 代理配置API（管理员）

#### 1.1 获取代理列表

**端点:** `GET /api/v1/proxy/config/`

**权限:** IsAdminUser

**查询参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `page` | int | ❌ | 页码（默认: 1） |
| `page_size` | int | ❌ | 每页数量（默认: 10） |
| `protocol` | str | ❌ | 按协议筛选（http/https/socks5） |
| `is_active` | bool | ❌ | 按激活状态筛选 |
| `is_healthy` | bool | ❌ | 按健康状态筛选 |
| `search` | str | ❌ | 搜索名称或主机 |

**请求示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/proxy/config/?is_active=true&protocol=https" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
    "count": 5,
    "next": "http://localhost:8000/api/v1/proxy/config/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "美国代理-01",
            "protocol": "https",
            "host": "us-proxy.example.com",
            "port": 8080,
            "username": "proxy_user",
            "is_active": true,
            "is_healthy": true,
            "priority": 0,
            "last_used_at": "2026-01-31T10:30:00Z",
            "created_at": "2026-01-30T08:00:00Z",
            "updated_at": "2026-01-31T10:30:00Z"
        }
    ]
}
```

#### 1.2 创建代理配置

**端点:** `POST /api/v1/proxy/config/`

**权限:** IsAdminUser

**请求体:**
```json
{
    "name": "美国代理-01",
    "protocol": "https",
    "host": "us-proxy.example.com",
    "port": 8080,
    "username": "proxy_user",
    "password": "secure_password",
    "is_active": true,
    "priority": 0
}
```

**字段说明:**

| 字段 | 类型 | 必需 | 约束 | 说明 |
|------|------|------|------|------|
| `name` | string | ✅ | 唯一, max=200 | 代理名称 |
| `protocol` | string | ✅ | http/https/socks5 | 代理协议 |
| `host` | string | ✅ | max=255 | 代理主机地址 |
| `port` | integer | ✅ | 1-65535 | 代理端口 |
| `username` | string | ❌ | max=200 | 代理认证用户名 |
| `password` | string | ❌ | max=255 | 代理认证密码 |
| `is_active` | boolean | ❌ | 默认true | 是否激活 |
| `priority` | integer | ❌ | 默认0 | 优先级（数字越小优先级越高） |

**响应示例:**
```json
{
    "id": 1,
    "name": "美国代理-01",
    "protocol": "https",
    "host": "us-proxy.example.com",
    "port": 8080,
    "username": "proxy_user",
    "is_active": true,
    "is_healthy": true,
    "priority": 0,
    "created_at": "2026-01-31T10:30:00Z"
}
```

**错误响应:**
```json
{
    "name": ["此代理名称已被使用"],
    "port": ["端口号必须在1-65535之间"]
}
```

#### 1.3 获取代理详情

**端点:** `GET /api/v1/proxy/config/{id}/`

**权限:** IsAdminUser

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 代理配置ID |

**请求示例:**
```bash
curl -X GET http://localhost:8000/api/v1/proxy/config/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
    "id": 1,
    "name": "美国代理-01",
    "protocol": "https",
    "protocol_display": "HTTPS",
    "host": "us-proxy.example.com",
    "port": 8080,
    "username": "proxy_user",
    "is_active": true,
    "is_healthy": true,
    "priority": 0,
    "consecutive_failures": 0,
    "consecutive_successes": 5,
    "last_used_at": "2026-01-31T10:30:00Z",
    "created_at": "2026-01-30T08:00:00Z",
    "updated_at": "2026-01-31T10:30:00Z"
}
```

#### 1.4 更新代理配置

**端点:** `PUT /api/v1/proxy/config/{id}/` 或 `PATCH /api/v1/proxy/config/{id}/`

**权限:** IsAdminUser

**PUT请求示例（完整更新）:**
```bash
curl -X PUT http://localhost:8000/api/v1/proxy/config/1/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "美国代理-01",
    "protocol": "https",
    "host": "us-proxy.example.com",
    "port": 8080,
    "username": "new_user",
    "password": "new_password",
    "is_active": true,
    "priority": 0
  }'
```

**PATCH请求示例（部分更新）:**
```bash
curl -X PATCH http://localhost:8000/api/v1/proxy/config/1/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

**注意:** 更新 `password` 字段会重新加密密码。

#### 1.5 删除代理配置

**端点:** `DELETE /api/v1/proxy/config/{id}/`

**权限:** IsAdminUser

**请求示例:**
```bash
curl -X DELETE http://localhost:8000/api/v1/proxy/config/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应:** `204 No Content`

⚠️ **警告:** 删除代理会同时删除所有关联的使用日志！

---

### 2. 代理选择器API（只读）

#### 2.1 获取可用代理列表

**端点:** `GET /api/v1/proxy/select/`

**权限:** IsAuthenticated

**说明:** 仅返回 `is_active=True` 且 `is_healthy=True` 的代理。

**请求示例:**
```bash
curl -X GET http://localhost:8000/api/v1/proxy/select/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
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
            "protocol_display": "HTTPS",
            "host": "us-proxy.example.com",
            "port": 8080,
            "status": "✓ 健康",
            "priority": 0
        },
        {
            "id": 2,
            "name": "香港代理-01",
            "protocol": "http",
            "protocol_display": "HTTP",
            "host": "hk-proxy.example.com",
            "port": 8080,
            "status": "✓ 健康",
            "priority": 10
        }
    ]
}
```

**使用场景:** 前端项目创建页面的代理选择器下拉框。

---

### 3. 测试连接API

#### 3.1 测试代理连接

**端点:** `POST /api/v1/proxy/{id}/test_connection/`

**权限:** IsAuthenticated

**路径参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | int | 代理配置ID |

**请求示例:**
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

**错误类型:**

| error | 说明 |
|-------|------|
| `Connection timeout` | 连接超时（5秒） |
| `HTTP error 407` | 代理认证失败 |
| `HTTP error 403` | 代理IP被封禁 |
| `HTTP error 502` | 代理服务器错误 |

**副作用:** 测试成功/失败会更新代理的 `is_healthy` 状态，并创建使用日志。

---

### 4. 使用日志API（管理员）

#### 4.1 获取使用日志列表

**端点:** `GET /api/v1/proxy/logs/`

**权限:** IsAdminUser

**查询参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `page` | int | ❌ | 页码（默认: 1） |
| `page_size` | int | ❌ | 每页数量（默认: 20） |
| `proxy` | int | ❌ | 按代理ID筛选 |
| `ai_provider` | str | ❌ | 按AI提供商筛选 |
| `success` | bool | ❌ | 按成功状态筛选 |
| `start` | date | ❌ | 开始日期（YYYY-MM-DD） |
| `end` | date | ❌ | 结束日期（YYYY-MM-DD） |

**请求示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/proxy/logs/?proxy=1&success=true&start=2026-01-01&end=2026-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/v1/proxy/logs/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "proxy": 1,
            "proxy_name": "美国代理-01",
            "ai_provider": "OpenAIClient",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "response_time_ms": 245,
            "success": true,
            "error_message": null,
            "timestamp": "2026-01-31T10:30:00Z"
        }
    ]
}
```

#### 4.2 获取日志统计

**端点:** `GET /api/v1/proxy/logs/stats/`

**权限:** IsAdminUser

**查询参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `proxy` | int | ❌ | 代理ID（不提供则统计所有代理） |
| `start` | date | ❌ | 开始日期 |
| `end` | date | ❌ | 结束日期 |

**请求示例:**
```bash
curl -X GET "http://localhost:8000/api/v1/proxy/logs/stats/?proxy=1&start=2026-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
    "proxy_name": "美国代理-01",
    "total_calls": 200,
    "success_count": 198,
    "failure_count": 2,
    "success_rate": 99.0,
    "avg_response_time_ms": 245.5,
    "min_response_time_ms": 120,
    "max_response_time_ms": 850
}
```

---

## 🔒 权限矩阵

| 端点 | 匿名用户 | 普通用户 | 管理员 |
|------|----------|----------|--------|
| `GET /api/v1/proxy/config/` | ❌ | ❌ | ✅ |
| `POST /api/v1/proxy/config/` | ❌ | ❌ | ✅ |
| `GET /api/v1/proxy/config/{id}/` | ❌ | ❌ | ✅ |
| `PUT /api/v1/proxy/config/{id}/` | ❌ | ❌ | ✅ |
| `DELETE /api/v1/proxy/config/{id}/` | ❌ | ❌ | ✅ |
| `GET /api/v1/proxy/select/` | ❌ | ✅ | ✅ |
| `POST /api/v1/proxy/{id}/test_connection/` | ❌ | ✅ | ✅ |
| `GET /api/v1/proxy/logs/` | ❌ | ❌ | ✅ |
| `GET /api/v1/proxy/logs/stats/` | ❌ | ❌ | ✅ |

---

## 📊 状态码

| 状态码 | 说明 |
|--------|------|
| `200 OK` | 请求成功 |
| `201 Created` | 创建成功 |
| `204 No Content` | 删除成功 |
| `400 Bad Request` | 请求参数错误 |
| `401 Unauthorized` | 未认证 |
| `403 Forbidden` | 权限不足 |
| `404 Not Found` | 资源不存在 |
| `422 Unprocessable Entity` | 验证失败 |

---

## 🧪 测试API

### 使用 curl 测试

```bash
# 设置Token
export TOKEN="your_jwt_token_here"

# 获取代理列表
curl -X GET http://localhost:8000/api/v1/proxy/select/ \
  -H "Authorization: Bearer $TOKEN"

# 创建代理配置
curl -X POST http://localhost:8000/api/v1/proxy/config/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试代理",
    "protocol": "https",
    "host": "proxy.example.com",
    "port": 8080,
    "username": "user",
    "password": "pass"
  }'

# 测试连接
curl -X POST http://localhost:8000/api/v1/proxy/1/test_connection/ \
  -H "Authorization: Bearer $TOKEN"
```

### 使用 Python 测试

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/proxy"
TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 获取代理列表
response = requests.get(f"{BASE_URL}/select/", headers=headers)
print(response.json())

# 创建代理
data = {
    "name": "测试代理",
    "protocol": "https",
    "host": "proxy.example.com",
    "port": 8080,
    "username": "user",
    "password": "pass"
}
response = requests.post(f"{BASE_URL}/config/", headers=headers, json=data)
print(response.json())

# 测试连接
response = requests.post(f"{BASE_URL}/1/test_connection/", headers=headers)
print(response.json())
```

---

## 📚 相关文档

- [安装指南](INSTALLATION.md)
- [配置指南](CONFIGURATION.md)
- [使用指南](USAGE.md)
- [故障排查](TROUBLESHOOTING.md)

---

**API支持:** 如遇问题，请查看 [故障排查指南](TROUBLESHOOTING.md)
