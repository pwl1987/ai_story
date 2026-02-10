# Celery + Redis Pub/Sub 流式架构使用指南

## 📋 架构概述

本系统采用 **Celery异步任务 + Redis Pub/Sub** 架构，实现AI生成任务的异步执行和实时流式输出。

### 数据流向

```
前端请求 → Django API → Celery任务(异步) → AI处理器(流式生成)
                ↓                              ↓
           返回task_id                  发布到Redis Pub/Sub
                                               ↓
                                        WebSocket订阅 → 前端实时接收
```

### 核心组件

1. **RedisStreamPublisher** (`core/redis/publisher.py`)
   - 封装Redis Pub/Sub发布功能
   - 提供统一的消息格式

2. **Celery任务** (`apps/projects/tasks.py`)
   - `execute_llm_stage` - LLM类阶段（文案改写/分镜/运镜）
   - `execute_text2image_stage` - 文生图阶段
   - `execute_image2video_stage` - 图生视频阶段

3. **WebSocket Consumer** (`apps/projects/consumers.py`)
   - `ProjectStageConsumer` - 订阅单个阶段
   - `ProjectConsumer` - 订阅整个项目

4. **API端点** (`apps/projects/views.py`)
   - `POST /api/v1/projects/{id}/execute-stage/` - 启动任务
   - `GET /api/v1/projects/{id}/task-status/?task_id=xxx` - 查询任务状态

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend

# 安装Redis异步客户端
uv add redis[hiredis]

# 如果需要异步支持
uv add redis[asyncio]
```

### 2. 启动Redis服务

```bash
# macOS (使用Homebrew)
brew install redis
brew services start redis

# 或使用Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. 启动Celery Worker

```bash
cd backend

# 启动默认队列worker
uv run celery -A config worker -l info

# 或启动多个队列worker (推荐)
uv run celery -A config worker -Q llm,image,video -l info

# 后台运行
uv run celery -A config worker -Q llm,image,video -l info --detach
```

### 4. 启动Django服务器 (ASGI模式)

```bash
cd backend

# 使用Daphne (推荐)
./run_asgi.sh

# 或使用Uvicorn
uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

---

## 📡 API使用示例

### 1. 启动阶段任务

#### 方式1: Celery异步任务 (默认，推荐)

**请求:**
```bash
POST /api/v1/projects/{project_id}/execute-stage/
Content-Type: application/json
Authorization: Bearer {token}

{
  "stage_name": "rewrite",
  "input_data": {
    "original_text": "这是原始文案..."
  }
}
```

**响应:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "channel": "ai_story:project:123e4567:stage:rewrite",
  "stage": "rewrite",
  "message": "阶段 文案改写 任务已启动",
  "project_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### 方式2: SSE流式输出 (旧方式，作为fallback)

**请求:**
```bash
POST /api/v1/projects/{project_id}/execute-stage/
Content-Type: application/json
Authorization: Bearer {token}

{
  "stage_name": "rewrite",
  "input_data": {
    "original_text": "这是原始文案..."
  },
  "use_streaming": true  // 启用SSE流式模式
}
```

**响应:**
返回 `text/event-stream` 流式响应，前端使用 `EventSource` 接收。

⚠️ **注意**: SSE模式需要ASGI服务器支持，且会阻塞HTTP连接直到任务完成。推荐使用Celery异步模式。

### 2. 查询任务状态 (轮询方式)

**请求:**
```bash
GET /api/v1/projects/{project_id}/task-status/?task_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890
Authorization: Bearer {token}
```

**响应:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "state": "SUCCESS",
  "result": {
    "success": true,
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "channel": "ai_story:project:123e4567:stage:rewrite",
    "result": "改写后的完整文案..."
  },
  "info": "任务执行成功",
  "project_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

## 🔌 WebSocket使用示例

### 方式1: 订阅单个阶段

**连接URL:**
```
ws://localhost:8000/ws/projects/{project_id}/stage/{stage_name}/
```

**示例 (JavaScript):**
```javascript
const projectId = '123e4567-e89b-12d3-a456-426614174000';
const stageName = 'rewrite';
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/stage/${stageName}/`);

ws.onopen = () => {
  console.log('WebSocket已连接');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'connected':
      console.log('已连接到实时流:', data.channel);
      break;

    case 'token':
      // 流式文本片段
      console.log('Token:', data.content);
      // 更新UI显示累积文本
      updateText(data.full_text);
      break;

    case 'stage_update':
      // 阶段状态更新
      console.log('进度:', data.progress, '%');
      updateProgress(data.progress);
      break;

    case 'done':
      // 任务完成
      console.log('完成:', data.full_text);
      console.log('元数据:', data.metadata);
      break;

    case 'error':
      // 错误
      console.error('错误:', data.error);
      break;

    case 'progress':
      // 批量处理进度
      console.log(`进度: ${data.current}/${data.total}`);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
};

ws.onclose = () => {
  console.log('WebSocket已关闭');
};

// 心跳检测 (可选)
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: Date.now()
    }));
  }
}, 30000);
```

### 方式2: 订阅整个项目

**连接URL:**
```
ws://localhost:8000/ws/projects/{project_id}/
```

**特点:**
- 同时监听项目所有阶段的更新
- 适合项目整体进度监控

---

## 📨 消息格式规范

### Token消息 (流式文本)
```json
{
  "type": "token",
  "content": "生成的文本片段",
  "full_text": "累积的完整文本",
  "stage": "rewrite",
  "project_id": "123e4567",
  "timestamp": 1699000000.123
}
```

### 阶段更新消息
```json
{
  "type": "stage_update",
  "stage": "rewrite",
  "status": "processing",
  "progress": 45,
  "message": "正在生成第3段...",
  "project_id": "123e4567",
  "timestamp": 1699000000.123
}
```

### 进度消息 (批量处理)
```json
{
  "type": "progress",
  "stage": "image_generation",
  "current": 3,
  "total": 10,
  "progress": 30,
  "item_name": "分镜3",
  "project_id": "123e4567",
  "timestamp": 1699000000.123
}
```

### 完成消息
```json
{
  "type": "done",
  "stage": "rewrite",
  "full_text": "完整生成结果",
  "metadata": {
    "latency_ms": 5000,
    "tokens_used": 1500,
    "model": "gpt-4"
  },
  "project_id": "123e4567",
  "timestamp": 1699000000.123
}
```

### 错误消息
```json
{
  "type": "error",
  "stage": "rewrite",
  "error": "API请求失败: 429 - Rate limit exceeded",
  "retry_count": 2,
  "project_id": "123e4567",
  "timestamp": 1699000000.123
}
```

---

## 🔧 配置说明

### Redis配置 (`config/settings/base.py`)

```python
# Celery Broker (Redis)
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Channels (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', 'localhost'), 6379)],
        },
    },
}
```

### Celery任务配置 (`config/celery.py`)

```python
# 任务路由 - 不同类型任务分配到不同队列
task_routes={
    'apps.projects.tasks.execute_llm_stage': {'queue': 'llm'},
    'apps.projects.tasks.execute_text2image_stage': {'queue': 'image'},
    'apps.projects.tasks.execute_image2video_stage': {'queue': 'video'},
}

# 超时配置
soft_time_limit=600,  # 10分钟软超时
time_limit=900  # 15分钟硬超时
```

---

## 🧪 测试

### 1. 测试Redis连接

```bash
redis-cli ping
# 应返回: PONG
```

### 2. 测试Celery任务

```python
# Django Shell
python manage.py shell

from apps.projects.tasks import execute_llm_stage

# 启动测试任务
task = execute_llm_stage.delay(
    project_id='your-project-id',
    stage_name='rewrite',
    input_data={'original_text': '测试文案'},
    user_id=1
)

print(f"Task ID: {task.id}")
```

### 3. 测试Redis Pub/Sub

```bash
# 终端1: 订阅频道
redis-cli
SUBSCRIBE ai_story:project:test:stage:rewrite

# 终端2: 发布消息
redis-cli
PUBLISH ai_story:project:test:stage:rewrite '{"type":"token","content":"测试"}'
```

### 4. 测试WebSocket

使用浏览器控制台或Postman测试WebSocket连接。

---

## 📊 监控和调试

### 1. 查看Celery任务

```bash
# 查看活跃任务
uv run celery -A config inspect active

# 查看已注册任务
uv run celery -A config inspect registered

# 查看统计信息
uv run celery -A config inspect stats
```

### 2. 使用Flower监控 (可选)

```bash
# 安装Flower
uv add flower

# 启动Flower
uv run celery -A config flower

# 访问 http://localhost:5555
```

### 3. Redis监控

```bash
# 查看Redis信息
redis-cli info

# 监控实时命令
redis-cli monitor

# 查看订阅频道
redis-cli PUBSUB CHANNELS ai_story:*
```

---

## ⚠️ 注意事项

### 1. 性能优化

- **Redis连接池**: 已在 `RedisStreamPublisher` 中使用连接池
- **消息批量发布**: 对于高频token消息，可考虑批量发布
- **频道清理**: 任务完成后自动清理，避免内存泄漏

### 2. 错误处理

- **Celery自动重试**: 失败任务自动重试3次（指数退避）
- **Redis连接失败**: 可降级到数据库轮询模式
- **超时处理**: 软超时10分钟，硬超时15分钟

### 3. 安全性

- **用户权限验证**: 在Celery任务中验证 `user_id`
- **频道命名**: 使用项目ID隔离不同用户的数据
- **WebSocket认证**: 可在Consumer中添加认证逻辑

### 4. 扩展性

- **多队列**: 不同类型任务分配到不同队列
- **多Worker**: 可启动多个Worker处理不同队列
- **分布式**: Redis和Celery都支持分布式部署

---

## 🔄 迁移指南

### 从旧的SSE架构迁移

1. **API兼容性**: 旧的SSE接口已保留（`rewrite_stream`等），可作为fallback
2. **前端改造**:
   - 将SSE EventSource改为WebSocket
   - 或使用轮询API（`task-status`）
3. **渐进式迁移**: 可以先迁移部分阶段，逐步完成

---

## 📚 相关文档

- [Celery官方文档](https://docs.celeryproject.org/)
- [Redis Pub/Sub文档](https://redis.io/docs/manual/pubsub/)
- [Django Channels文档](https://channels.readthedocs.io/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## 🆘 常见问题

### Q1: WebSocket连接失败？
**A:** 确保使用ASGI服务器（Daphne/Uvicorn），WSGI不支持WebSocket。

### Q2: 收不到Redis消息？
**A:** 检查Celery Worker是否正常运行，查看日志确认任务是否执行。

### Q3: 任务一直PENDING？
**A:** 确认Celery Worker已启动，并且监听了正确的队列。

### Q4: 如何处理长时间运行的任务？
**A:** 调整 `soft_time_limit` 和 `time_limit` 参数，或拆分为多个子任务。

---

**最后更新**: 2025-11-03
