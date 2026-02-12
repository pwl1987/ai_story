# Story 13-2.2: 实现导出进度追踪

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P1
> **预估工作量:** 1天
> **依赖:** 13.1.4, 13.2.1

---

## 📋 需求描述

**用户故事：** 作为前端用户，我需要实时查看视频导出的进度，包括处理状态、百分比和完成通知。

**功能说明：**
- 实现 WebSocket 进度推送
- 实现前端进度监听
- 显示导出进度条
- 显示导出完成后的下载链接
- 支持导出失败重试

**边界条件：**
- 不包含视频合成逻辑
- 只负责进度通知
- 前端监听和显示

**验收标准：**
- [ ] WebSocket 进度推送正常
- [ ] 前端进度实时更新
- [ ] 完成通知正常触发
- [ ] 错误处理正确

---

## 🔧 技术实现细节

### WebSocket 消费者

```python
# config/routing.py

from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

websocket_urlpatterns = [
    re_path(r'^ws/exports/(?P<export_id>[^/]+)/$', consumers.ExportProgressConsumer),
]

application = ProtocolTypeRouter(
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
)
```

### WebSocket 消费者实现

```python
# apps/artworks/consumers.py

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class ExportProgressConsumer(AsyncWebsocketConsumer):
    """导出进度 WebSocket 消费者"""

    async def connect(self):
        """接受连接"""
        self.export_id = self.scope['url_route']['kwargs']['export_id']

        # 验证导出记录存在
        try:
            export_record = await sync_to_async(
                VideoExport.objects.get(export_id=self.export_id)
            )

            if export_record.chapter.project.user.id != self.scope['user'].id:
                await self.close(code=4003, reason='Unauthorized')
                return

            # 添加到 Redis 频道
            await self.channel_layer.group_add(
                f'export_{self.export_id}',
                self.channel_name
            )

            # 发送当前状态
            await self.send_progress_update(export_record)

        except VideoExport.DoesNotExist:
            await self.close(code=4004, reason='Export not found')

    async def disconnect(self, close_code):
        """断开连接"""
        await self.channel_layer.group_discard(
            f'export_{self.export_id}',
            self.channel_name
        )

    async def receive(self, text_data):
        """接收客户端消息"""
        data = json.loads(text_data)

        # 处理客户端命令（如取消导出）
        if data.get('action') == 'cancel':
            await self.cancel_export()

    async def send_progress_update(self, export_record):
        """发送进度更新"""
        message = {
            'type': 'progress',
            'export_id': self.export_id,
            'status': export_record.status,
            'progress': export_record.progress_percentage,
            'file_size': export_record.file_size,
            'duration': export_record.duration_seconds
        }

        await self.send(text_data=json.dumps(message))

    async def export_progress_notification(self, event):
        """处理导出进度事件"""
        from channels.layers import get_channel_layer

        event_data = event.data

        # 广播到所有订阅此导出的客户端
        message = {
            'type': 'progress_update',
            'export_id': event_data.get('export_id'),
            'status': event_data.get('status'),
            'progress': event_data.get('progress', 0)
        }

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"export_{event_data.get('export_id')}",
            {
                'type': 'progress_update',
                'text': json.dumps(message)
            }
        )

    @staticmethod
    def get_export_id():
        """从作用域获取导出ID"""
        # 已在 connect 方法中实现
        pass
```

### 前端进度监听组件

```javascript
// frontend/src/composables/useExportProgress.js

import { ref, onUnmounted } from 'vue'

export function useExportProgress(exportId) {
  const progress = ref(0)
  const status = ref('pending')
  const error = ref(null)
  const outputUrl = ref(null)
  const fileSize = ref(null)
  const duration = ref(null)
  let ws = null

  const connect = () => {
    const wsUrl = `${process.env.VUE_APP_WS_URL}/ws/exports/${exportId}/`
    ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'progress':
        case 'progress_update':
          progress.value = data.progress
          status.value = data.status
          break
        case 'export_completed':
          status.value = 'completed'
          outputUrl.value = data.output_file
          fileSize.value = data.file_size
          duration.value = data.duration
          break
        case 'export_failed':
          status.value = 'failed'
          error.value = data.error
          break
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      error.value = '连接失败'
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    progress,
    status,
    error,
    outputUrl,
    fileSize,
    duration,
    connect,
    disconnect
  }
}
```

### 导出进度模态框

```vue
<!-- frontend/src/components/artworks/ExportProgressModal.vue -->
<template>
  <div class="modal modal-open">
    <div class="modal-box">
      <div class="modal-body">
        <h3 class="text-lg font-bold mb-4">📦 视频导出中</h3>

        <!-- 章节信息 -->
        <div class="bg-base-200 p-4 rounded mb-4">
          <p class="font-medium">{{ chapter.title }}</p>
          <p class="text-sm text-gray-600">
            分辨率: {{ config.resolution }} | 质量: {{ config.quality }}
          </p>
        </div>

        <!-- 进度条 -->
        <div class="mb-4">
          <div class="flex justify-between mb-2">
            <span>{{ statusDisplay }}</span>
            <span>{{ progress }}%</span>
          </div>
          <progress
            class="progress progress-primary"
            :value="progress"
            max="100"
          ></progress>
        </div>

        <!-- 导出信息 -->
        <div v-if="status === 'completed'" class="bg-success bg-opacity-10 p-4 rounded mb-4">
          <h4 class="font-bold text-success mb-2">✅ 导出完成</h4>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-gray-600">文件大小</p>
              <p class="font-medium">{{ formatFileSize(fileSize) }}</p>
            </div>
            <div>
              <p class="text-gray-600">视频时长</p>
              <p class="font-medium">{{ formatDuration(duration) }}</p>
            </div>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="status === 'failed'" class="bg-error bg-opacity-10 p-4 rounded mb-4">
          <h4 class="font-bold text-error mb-2">❌ 导出失败</h4>
          <p class="text-error">{{ error }}</p>
        </div>

        <!-- 日志输出 -->
        <div class="bg-base-300 p-4 rounded max-h-40 overflow-y-auto">
          <h4 class="text-sm font-bold mb-2">📋 导出日志</h4>
          <div class="space-y-1 text-sm font-mono">
            <div v-for="(log, index) in logs" :key="index" class="flex gap-2">
              <span class="text-gray-500 w-16">{{ log.time }}</span>
              <span :class="{
                'text-info': log.type === 'info',
                'text-success': log.type === 'success',
                'text-error': log.type === 'error'
              }">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-action">
        <button
          v-if="status === 'processing'"
          @click="handleCancel"
          class="btn btn-error"
        >
          ❌ 取消导出
        </button>

        <button
          v-if="status === 'completed'"
          @click="handleDownload"
          class="btn btn-primary"
        >
          📥 下载视频
        </button>

        <button
          v-if="status === 'failed'"
          @click="handleRetry"
          class="btn btn-warning"
        >
          🔄 重试导出
        </button>

        <button
          @click="$emit('close')"
          class="btn btn-outline"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { useExportProgress } from '@/composables/useExportProgress'

export default {
  name: 'ExportProgressModal',

  props: {
    chapter: {
      type: Object,
      required: true
    },
    config: {
      type: Object,
      required: true
    },
    exportId: {
      type: String,
      required: true
    }
  },

  setup(props) {
    const {
      progress,
      status,
      error,
      outputUrl,
      fileSize,
      duration,
      connect,
      disconnect
    } = useExportProgress(props.exportId)

    // 模拟日志
    const logs = ref([
      { time: '00:00', type: 'info', message: '初始化导出任务...' },
      { time: '00:01', type: 'info', message: '加载场景数据...' },
      { time: '00:02', type: 'info', message: '开始视频合成...' }
    ])

    const { progress: currentProgress } = toRefs(progress)
    watch(currentProgress, (newVal) => {
      logs.value.push({
        time: new Date().toLocaleTimeString(),
        type: 'info',
        message: `进度更新: ${newVal}%`
      })
    })

    const { status: currentStatus } = toRefs(status)
    watch(currentStatus, (newVal) => {
      if (newVal === 'completed') {
        logs.value.push({
          time: new Date().toLocaleTimeString(),
          type: 'success',
          message: '导出完成！'
        })
      } else if (newVal === 'failed') {
        logs.value.push({
          time: new Date().toLocaleTimeString(),
          type: 'error',
          message: `导出失败: ${error.value}`
        })
      }
    })

    // 组件挂载时连接
    connect()

    return {
      progress,
      status,
      error,
      outputUrl,
      fileSize,
      duration,
      logs,

      formatFileSize(bytes) {
        if (!bytes) return '-'
        const mb = bytes / (1024 * 1024)
        return `${mb.toFixed(2)} MB`
      },

      formatDuration(seconds) {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins}m ${secs}s`
      },

      handleCancel() {
        // 发送取消请求
        const ws = connect()
        ws.send(JSON.stringify({ action: 'cancel' }))
      },

      handleDownload() {
        if (outputUrl.value) {
          window.open(`/api/v1/artifacts/downloads/${outputUrl.value}`)
        }
      },

      handleRetry() {
        // 重新触发导出
        disconnect()
        this.$emit('retry')
      }
    }
  }
}
</script>
```

---

## 📊 依赖关系

**前置 Story:** 13.1.4, 13.2.1
**阻塞 Story:** 无

---

## 🎯 成功标准

- [ ] WebSocket 进度推送正常
- [ ] 前端进度实时更新
- [ ] 完成通知正常触发
- [ ] 错误处理正确
