# Story 11.2.4: 单分镜重新生成

**用户故事:**
作为漫剧编辑，
我希望能够单独重新生成某个分镜的内容（图像和音频），
以便在不影响其他分镜的情况下调整和优化单个镜头。

---

## Acceptance Criteria

### [场景1: 单镜头重新生成 API]
**Given** 用户请求重新生成镜头ID=5
**When** 调用 POST /api/v1/artworks/shots/5/regenerate/
**Then** API 返回 202 Accepted
**And** 触发 Celery 异步任务 regenerate_shot_content
**And** 任务接收 shot_id 作为参数
**And** 任务在 'image' 和 'audio' 队列中执行
**And** 前端通过 WebSocket 接收生成进度

### [场景2: 参数快速调整]
**Given** 用户在重新生成弹窗中
**When** 打开高级选项
**Then** 显示可调整的参数列表
**And** 可以修改图像生成提示词
**And** 可以修改角色造型 (character_pose)
**And** 可以修改运镜参数 (camera_movement_params)
**And** 可以修改时长 (duration)
**And** 可以选择是否重新生成图像 (复选框)
**And** 可以选择是否重新生成音频 (复选框)
**And** 参数验证通过后才能提交

### [场景3: 不影响其他分镜]
**Given** 项目包含10个镜头
**When** 重新生成镜头ID=5
**Then** 只有镜头ID=5的状态变为 'processing'
**And** 其他镜头状态保持不变
**And** 其他镜头的生成文件不受影响
**And** 重新生成完成后，只有镜头ID=5的文件被替换
**And** 任务日志中记录重新生成操作

### [场景4: 生成失败重试逻辑]
**Given** 镜头生成失败 (generation_error 有内容)
**When** 用户点击"重试"按钮
**Then** 调用重新生成 API
**And** generation_retry_count 字段增加1
**And** 当 generation_retry_count < 3 时，自动重试
**And** 当 generation_retry_count >= 3 时，停止重试并标记为失败
**And** 错误信息更新到 generation_error 字段

### [场景5: 生成进度实时推送]
**Given** Celery 任务正在执行
**When** 生成进度更新
**Then** 通过 Redis Pub/Sub 推送进度消息
**And** WebSocket 连接接收消息
**And** 前端更新进度条显示
**And** 消息格式: {"type": "progress", "shot_id": 5, "progress": 50, "message": "正在生成图像..."}

### [场景6: 前端重新生成界面]
**Given** 用户点击镜头卡片的"重新生成"按钮
**When** 重新生成弹窗打开
**Then** 弹窗显示当前镜头信息
**And** 显示可调整的参数表单
**And** 显示"生成图像"和"生成音频"复选框
**And** 显示"确认"和"取消"按钮
**And** 点击确认后，按钮显示加载状态
**And** 生成完成后显示成功提示
**And** 镜头卡片自动更新显示新生成的内容

### [场景7: 批量重新生成]
**Given** 用户选中5个镜头
**When** 点击"批量重新生成"按钮
**Then** 弹窗显示选中的镜头列表
**And** 显示通用参数表单 (应用于所有镜头)
**And** 点击确认后，依次提交5个重新生成请求
**And** 每个镜头独立执行重新生成任务
**And** 显示整体进度 (已完成1/5)
**And** 所有任务完成后显示汇总提示

### [场景8: 单元测试和集成测试]
**Given** 运行测试套件
**When** 测试重新生成功能
**Then** 测试 API 端点 (POST /regenerate/) ✅
**And** 测试 Celery 任务执行 ✅
**And** 测试参数验证逻辑 ✅
**And** 测试重试计数器 ✅
**And** 测试进度推送机制 ✅
**And** 集成测试验证完整流程 ✅
**And** 测试覆盖率 > 85% ✅

---

## Tasks / Subtasks

### 后端 API 开发
- [ ] 1.1 在 `backend/apps/artworks/views.py` 的 `ShotViewSet` 中添加 `regenerate` action
- [ ] 1.2 创建 `RegenerateShotSerializer` 序列化器验证输入参数
- [ ] 1.3 实现参数验证逻辑 (regenerate_image, regenerate_audio, override_params)
- [ ] 1.4 返回 202 Accepted 状态和 task_id

### Celery 任务开发
- [ ] 2.1 在 `backend/apps/artworks/tasks.py` 创建 `regenerate_shot_content` 任务
- [ ] 2.2 实现状态更新逻辑 (is_generated=False, generation_retry_count+=1)
- [ ] 2.3 集成图像生成服务 (ImageGenerationService)
- [ ] 2.4 集成音频生成服务 (AudioGenerationService)
- [ ] 2.5 实现进度推送 (Redis Pub/Sub)
- [ ] 2.6 实现错误处理和重试逻辑 (max_retries=3)

### WebSocket 进度推送
- [ ] 3.1 在 `backend/apps/artworks/consumers.py` 添加 `ShotRegenerateConsumer`
- [ ] 3.2 实现 WebSocket 连接处理 (ws://.../shots/{shot_id}/regenerate/)
- [ ] 3.3 实现进度消息转发到前端
- [ ] 3.4 更新 `config/routing.py` 添加路由

### 前端组件开发
- [ ] 4.1 创建 `frontend/src/components/artworks/RegenerateModal.vue` 组件
- [ ] 4.2 实现参数表单 (图像/音频复选框、高级选项)
- [ ] 4.3 实现确认和取消逻辑
- [ ] 4.4 实现加载状态显示
- [ ] 4.5 集成到 `StoryboardViewer.vue` (添加"重新生成"按钮)

### 前端 API 集成
- [ ] 5.1 在 `frontend/src/services/artworkService.js` 添加 `regenerateShot` 方法
- [ ] 5.2 在 `frontend/src/services/artworkService.js` 添加 `batchRegenerate` 方法
- [ ] 5.3 实现 WebSocket 进度订阅
- [ ] 5.4 实现进度条更新逻辑

### 测试
- [ ] 6.1 编写 API 端点单元测试 (`test_api_regenerate.py`)
- [ ] 6.2 编写 Celery 任务单元测试 (`test_regenerate_task.py`)
- [ ] 6.3 编写序列化器验证测试 (`test_regenerate_serializer.py`)
- [ ] 6.4 编写集成测试 (`test_regenerate_integration.py`)
- [ ] 6.5 运行测试套件并确保 >85% 覆盖率

---

## Dev Notes

### 前置条件
- ✅ Story 11.2.2 完成 (Shot 数据模型增强，包含生成状态字段)
- ✅ Story 11.2.3 完成 (分镜编辑器前端界面 - StoryboardViewer.vue)
- ✅ Celery 任务队列配置正确
- ✅ Redis Pub/Sub 配置正确
- ✅ WebSocket 实时通信基础设施已存在 (channels)

### 依赖关系
- 依赖 Story 11.2.2 (Shot 数据模型的生成状态字段)
- 依赖 Story 11.2.3 (前端 StoryboardViewer 组件)
- 依赖 Celery 任务系统 (apps/projects/tasks.py 中的任务模式)
- 依赖 WebSocket 消费者 (config/routing.py)

### 技术实现要点

**后端 API 实现:**
```python
# apps/artworks/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from .tasks import regenerate_shot_content

class ShotViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """重新生成镜头内容"""
        shot = self.get_object()

        # 验证参数
        serializer = RegenerateShotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 触发异步任务
        task = regenerate_shot_content.delay(
            shot_id=shot.id,
            regenerate_image=serializer.validated_data.get('regenerate_image', True),
            regenerate_audio=serializer.validated_data.get('regenerate_audio', True),
            override_params=serializer.validated_data.get('override_params', {})
        )

        return Response({
            'task_id': task.id,
            'message': '重新生成任务已启动'
        }, status=202)
```

**Celery 任务实现:**
```python
# apps/artworks/tasks.py
@app.task(bind=True, max_retries=3)
def regenerate_shot_content(self, shot_id, regenerate_image=True, regenerate_audio=True, override_params=None):
    """重新生成镜头内容"""
    from apps.artworks.models import Shot
    from core.redis.stream_publisher import RedisStreamPublisher

    shot = Shot.objects.get(id=shot_id)

    # 更新状态
    shot.is_generated = False
    shot.generation_error = ''
    shot.generation_retry_count += 1
    shot.save()

    # 推送进度
    publisher = RedisStreamPublisher(f'shot_{shot_id}')
    publisher.publish({
        'type': 'progress',
        'progress': 0,
        'message': '开始重新生成...'
    })

    try:
        # 生成图像
        if regenerate_image:
            publisher.publish({'type': 'progress', 'progress': 25, 'message': '正在生成图像...'})
            # 调用图像生成服务

        # 生成音频
        if regenerate_audio:
            publisher.publish({'type': 'progress', 'progress': 75, 'message': '正在生成音频...'})
            # 调用音频生成服务

        # 更新状态
        shot.is_generated = True
        shot.generated_at = timezone.now()
        shot.save()

        publisher.publish({'type': 'completed', 'progress': 100, 'message': '生成完成'})

    except Exception as e:
        shot.generation_error = str(e)
        shot.save()
        publisher.publish({'type': 'error', 'message': f'生成失败: {str(e)}'})
        raise
```

**WebSocket 消费者:**
```python
# apps/artworks/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ShotRegenerateConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.shot_id = self.scope['url_route']['kwargs']['shot_id']
        self.room_group_name = f'shot_{self.shot_id}_regenerate'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def regenerate_progress(self, event):
        await self.send_json(event)
```

**路由配置:**
```python
# config/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from apps.artworks.consumers import ShotRegenerateConsumer

websocket_urlpatterns = [
    re_path(r'ws/shots/(?P<shot_id>\d+)/regenerate/$', ShotRegenerateConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': URLRouter(websocket_urlpatterns),
})
```

### 关键文件路径

**后端文件:**
- `backend/apps/artworks/views.py` - ShotViewSet.regenerate action
- `backend/apps/artworks/serializers.py` - RegenerateShotSerializer
- `backend/apps/artworks/tasks.py` - regenerate_shot_content 任务
- `backend/apps/artworks/consumers.py` - ShotRegenerateConsumer
- `backend/config/routing.py` - WebSocket 路由配置
- `backend/apps/artworks/tests/test_regenerate_*.py` - 测试文件

**前端文件:**
- `frontend/src/components/artworks/RegenerateModal.vue` - 重新生成弹窗组件
- `frontend/src/components/content/StoryboardViewer.vue` - 集成重新生成按钮
- `frontend/src/services/artworkService.js` - API 调用服务

### 现有可复用组件
- `frontend/src/components/common/LoadingContainer.vue` - 加载状态
- `frontend/src/services/websocketClient.js` - WebSocket 客户端 (可扩展)

### SOLID 原则应用
- **单一职责 (SRP)**:
  - RegenerateShotSerializer 只负责参数验证
  - regenerate_shot_content 任务只负责生成逻辑
  - ShotRegenerateConsumer 只负责 WebSocket 通信
- **开闭原则 (OCP)**:
  - 通过 override_params 扩展生成参数，无需修改任务代码
- **依赖倒置 (DIP)**:
  - 任务依赖抽象的服务接口 (ImageGenerationService, AudioGenerationService)

---

## Dev Agent Record

### Implementation Plan

**Phase 1: 后端 API 和 Celery 任务 (Day 1-2)**
1. 在 `apps/artworks/views.py` 添加 `regenerate` action
2. 创建 `RegenerateShotSerializer`
3. 创建 `regenerate_shot_content` Celery 任务
4. 实现进度推送逻辑

**Phase 2: WebSocket 通信 (Day 2)**
1. 创建 `ShotRegenerateConsumer`
2. 更新 `config/routing.py`
3. 测试 WebSocket 连接

**Phase 3: 前端组件 (Day 2-3)**
1. 创建 `RegenerateModal.vue`
2. 集成到 `StoryboardViewer.vue`
3. 实现 API 调用和进度订阅

**Phase 4: 测试 (Day 3)**
1. 编写单元测试
2. 编写集成测试
3. 运行测试并修复问题

### Debug Log

---

### Completion Notes

---

## File List

---

## Change Log

---

## Status

**Status:** ready-for-dev
**Assigned To:**
**Start Date:**
**Completion Date:**
