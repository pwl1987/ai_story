# API 迁移指南

## 从旧的 SSE 流式接口迁移到新的 Celery + Redis 架构

### 📋 变更概述

旧的独立SSE端点（如 `rewrite_stream`）已被统一到 `execute_stage` 端点中。新架构提供两种模式：

1. **Celery异步模式** (默认，推荐) - 不阻塞HTTP连接，支持分布式部署
2. **SSE流式模式** (fallback) - 保留旧的行为，通过 `use_streaming=true` 启用

---

## 🔄 API 变更对照

### 旧接口 (已废弃)

#### 文案改写
```bash
POST /api/v1/projects/{id}/rewrite_stream/
Body: {"input_data": {"original_text": "..."}}

返回: text/event-stream 流式响应
```

#### 其他阶段
```bash
POST /api/v1/projects/{id}/execute-stage/
Body: {"stage_name": "storyboard", "input_data": {...}}

返回: text/event-stream 流式响应 (旧实现)
```

---

### 新接口 (统一)

#### 所有阶段统一使用 execute_stage

**默认模式 (Celery异步):**
```bash
POST /api/v1/projects/{id}/execute-stage/
Body: {
  "stage_name": "rewrite",  // 或 storyboard, image_generation 等
  "input_data": {...}
}

返回: {
  "task_id": "xxx",
  "channel": "ai_story:project:xxx:stage:rewrite",
  "message": "任务已启动"
}
```

**兼容模式 (SSE流式):**
```bash
POST /api/v1/projects/{id}/execute-stage/
Body: {
  "stage_name": "rewrite",
  "input_data": {...},
  "use_streaming": true  // 启用SSE模式
}

返回: text/event-stream 流式响应
```

---

## 🚀 前端迁移步骤

### 步骤1: 更新API调用

#### 旧代码 (SSE EventSource)
```javascript
// 旧方式 - 使用 rewrite_stream 端点
const eventSource = new EventSource(
  `/api/v1/projects/${projectId}/rewrite_stream/`,
  {
    method: 'POST',
    body: JSON.stringify({
      input_data: { original_text: '...' }
    })
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 处理消息
};
```

#### 新代码 (WebSocket，推荐)
```javascript
// 新方式1 - Celery异步 + WebSocket
// 1. 启动任务
const response = await fetch(`/api/v1/projects/${projectId}/execute-stage/`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    stage_name: 'rewrite',
    input_data: { original_text: '...' }
  })
});

const { task_id, channel } = await response.json();

// 2. 连接WebSocket订阅实时进度
const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/stage/rewrite/`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'token':
      // 流式文本片段
      updateText(data.full_text);
      break;
    case 'done':
      // 任务完成
      console.log('完成:', data.full_text);
      ws.close();
      break;
    case 'error':
      // 错误处理
      console.error('错误:', data.error);
      break;
  }
};
```

#### 兼容代码 (SSE，fallback)
```javascript
// 新方式2 - 使用 use_streaming=true 保持旧行为
const eventSource = new EventSource(
  `/api/v1/projects/${projectId}/execute-stage/`,
  {
    method: 'POST',
    body: JSON.stringify({
      stage_name: 'rewrite',
      input_data: { original_text: '...' },
      use_streaming: true  // 启用SSE模式
    })
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // 处理消息 (与旧方式相同)
};
```

---

### 步骤2: 更新状态管理

#### Vuex Store 示例

```javascript
// store/modules/project.js

export default {
  state: {
    currentTask: null,
    wsConnection: null,
    streamingText: ''
  },

  mutations: {
    SET_TASK(state, task) {
      state.currentTask = task;
    },
    SET_WS_CONNECTION(state, ws) {
      state.wsConnection = ws;
    },
    APPEND_TEXT(state, text) {
      state.streamingText = text;
    },
    CLEAR_STREAMING(state) {
      state.streamingText = '';
      if (state.wsConnection) {
        state.wsConnection.close();
        state.wsConnection = null;
      }
    }
  },

  actions: {
    // 新方式: Celery异步 + WebSocket
    async executeStage({ commit }, { projectId, stageName, inputData }) {
      try {
        // 1. 启动任务
        const response = await this.$api.projects.executeStage(projectId, {
          stage_name: stageName,
          input_data: inputData
        });

        commit('SET_TASK', response.data);

        // 2. 连接WebSocket
        const ws = new WebSocket(
          `ws://localhost:8000/ws/projects/${projectId}/stage/${stageName}/`
        );

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'token':
              commit('APPEND_TEXT', data.full_text);
              break;
            case 'done':
              commit('APPEND_TEXT', data.full_text);
              commit('CLEAR_STREAMING');
              break;
            case 'error':
              console.error('任务失败:', data.error);
              commit('CLEAR_STREAMING');
              break;
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket错误:', error);
          commit('CLEAR_STREAMING');
        };

        commit('SET_WS_CONNECTION', ws);

      } catch (error) {
        console.error('启动任务失败:', error);
        throw error;
      }
    },

    // 旧方式兼容: SSE流式
    async executeStageStreaming({ commit }, { projectId, stageName, inputData }) {
      // 使用 use_streaming=true
      const response = await this.$api.projects.executeStage(projectId, {
        stage_name: stageName,
        input_data: inputData,
        use_streaming: true
      });

      // 处理SSE响应...
    }
  }
};
```

---

### 步骤3: 错误处理

#### 新架构的错误处理

```javascript
// 1. 任务启动失败
try {
  const response = await fetch('/api/v1/projects/{id}/execute-stage/', {
    method: 'POST',
    body: JSON.stringify({ stage_name: 'rewrite', input_data: {...} })
  });

  if (!response.ok) {
    throw new Error('任务启动失败');
  }

  const { task_id, channel } = await response.json();

} catch (error) {
  console.error('API错误:', error);
}

// 2. WebSocket连接失败
ws.onerror = (error) => {
  console.error('WebSocket错误:', error);
  // 降级到轮询模式
  startPolling(task_id);
};

// 3. 任务执行失败 (通过WebSocket接收)
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'error') {
    console.error('任务执行失败:', data.error);
    // 显示错误提示
    showErrorNotification(data.error);
  }
};
```

---

## 📊 功能对比

| 特性 | 旧架构 (SSE) | 新架构 (Celery + Redis) |
|------|-------------|------------------------|
| HTTP连接 | 阻塞直到完成 | 立即返回 |
| 并发能力 | 受限于HTTP连接数 | 无限制 |
| 任务重试 | 不支持 | 自动重试3次 |
| 超时控制 | 简单超时 | 软/硬超时 |
| 分布式部署 | 不支持 | 支持 |
| 任务监控 | 困难 | 支持Flower监控 |
| 前端实现 | EventSource | WebSocket或轮询 |
| 服务器要求 | ASGI | ASGI + Redis + Celery |

---

## ⚠️ 注意事项

### 1. 向后兼容性

- ✅ 旧的SSE行为通过 `use_streaming=true` 保留
- ✅ 消息格式保持一致
- ⚠️ 独立的 `rewrite_stream` 端点已移除

### 2. 性能影响

- **Celery模式**: 不阻塞HTTP连接，支持更高并发
- **SSE模式**: 每个请求占用一个HTTP连接，并发受限

### 3. 部署要求

使用Celery模式需要额外服务：
- Redis服务器
- Celery Worker进程

### 4. 前端兼容性

- **WebSocket**: 所有现代浏览器支持
- **EventSource**: 所有现代浏览器支持
- **轮询**: 最大兼容性，但效率较低

---

## 🔧 迁移检查清单

- [ ] 更新API调用，使用统一的 `execute_stage` 端点
- [ ] 移除对 `rewrite_stream` 等独立端点的引用
- [ ] 实现WebSocket连接逻辑
- [ ] 添加错误处理和重连机制
- [ ] 更新状态管理代码
- [ ] 测试所有阶段的执行
- [ ] 添加降级方案（轮询或SSE）
- [ ] 更新文档和注释

---

## 📚 相关文档

- [完整使用文档](CELERY_REDIS_STREAMING.md)
- [WebSocket API文档](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Celery文档](https://docs.celeryproject.org/)

---

## 🆘 常见问题

### Q1: 为什么要迁移？
**A:** 新架构不阻塞HTTP连接，支持更高并发和分布式部署，提供更好的可靠性和可扩展性。

### Q2: 必须立即迁移吗？
**A:** 不必须。通过 `use_streaming=true` 可以继续使用旧的SSE行为，但推荐尽快迁移以获得更好的性能。

### Q3: WebSocket连接失败怎么办？
**A:** 可以降级到轮询模式，使用 `task-status` API定期查询任务状态。

### Q4: 如何测试新架构？
**A:** 运行 `python test_celery_redis.py` 测试脚本，确保Redis和Celery正常工作。

---

**最后更新**: 2025-11-03
