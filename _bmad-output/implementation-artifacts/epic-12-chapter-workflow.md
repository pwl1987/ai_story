# Epic 12: 章节推进式工作流

**Epic ID:** epic-12
**创建日期:** 2026-02-11
**状态:** backlog
**优先级:** P0 (核心功能)
**预估工作量:** 1周 (3个Stories)

---

## 📋 Epic 概述

**目标:** 实现章节推进式工作流编排器，实现按章节顺序自动化制作漫剧场景。

**价值:**
- 实现用户"上传小说 → 自动生成漫剧"的核心愿景
- 简化用户操作流程，从手动每场制作到章节级自动化
- 支持暂停/继续，适应不同工作节奏

**依赖:**
- ✅ Epic 10: 本地引擎集成 (已完成)
- ✅ Epic 11: 角色资产 + 分镜编辑 (已完成)

---

## 🎯 Epic 目标

### 主要目标

1. **章节编排服务** - 自动化章节内所有场景的制作流程
2. **首尾帧自动提取** - 智能提取场景首帧和尾帧
3. **章节工作室 UI** - 整合式章节制作界面

### 成功标准

- [ ] 用户可以选择章节，一键启动自动化制作
- [ ] 系统自动处理章节内所有场景：分镜生成 → 图片生成 → 配音
- [ ] 自动提取每个场景的首帧和尾帧
- [ ] 支持暂停/继续工作流
- [ ] 实时进度推送 (WebSocket)

---

## 📊 Stories 清单

### Story 12-1: 章节编排服务

**状态:** backlog
**预估:** 3-5天
**优先级:** P0

**描述:** 实现章节级工作流编排器，自动化处理章节内所有场景的制作流程。

**任务:**
- [ ] 创建 ChapterWorkflowService 服务类
- [ ] 实现工作流状态机 (pending/in_progress/completed/failed)
- [ ] 实现场景队列处理逻辑
- [ ] 集成 OllamaClient (分镜生成)
- [ ] 集成 ComfyUIService (图片生成)
- [ ] 集成 EdgeTTSClient (语音生成)
- [ ] 实现错误重试机制
- [ ] 实现 WebSocket 进度推送
- [ ] 编写单元测试 (目标 80%+ 覆盖率)

**接受标准:**
- AC1: ChapterWorkflowService 能处理章节内所有场景
- AC2: 支持暂停/继续操作
- AC3: 每个场景完成后自动更新进度
- AC4: 错误自动重试最多 3 次
- AC5: WebSocket 实时推送进度更新

---

### Story 12-2: 首尾帧自动提取服务

**状态:** backlog
**预估:** 1-2天
**优先级:** P0

**描述:** 实现自动提取场景首帧(第一镜)和尾帧(最后一镜)的服务。

**任务:**
- [ ] 创建 FrameExtractionService 服务类
- [ ] 实现首帧提取逻辑 (Shot.is_head_frame = True)
- [ ] 实现尾帧提取逻辑 (Shot.is_tail_frame = True)
- [ ] 将提取的图片保存到 ScriptScene.head_frame/tail_frame
- [ ] 添加图片压缩/优化逻辑
- [ ] 实现 Celery 异步任务
- [ ] 添加 API 端点
- [ ] 编写单元测试

**接受标准:**
- AC1: 自动识别场景内第一个镜头并提取首帧
- AC2: 自动识别场景内最后一个镜头并提取尾帧
- AC3: 提取的图片质量符合要求 (1080p)
- AC4: 异步处理，不阻塞主流程
- AC5: 提取失败时有合理的降级处理

---

### Story 12-3: 章节工作室 UI

**状态:** backlog
**预估:** 2-3天
**优先级:** P0

**描述:** 创建整合式章节制作界面，集成工作流启动、进度监控、场景编辑等功能。

**任务:**
- [ ] 创建 ChapterStudio.vue 主页面
- [ ] 创建 WorkflowControlPanel.vue 控制面板
- [ ] 创建 SceneProgressCard.vue 进度卡片
- [ ] 集成 WebSocket 进度订阅
- [ ] 实现启动/暂停/继续按钮
- [ ] 实现场景快速编辑功能
- [ ] 添加首尾帧预览功能
- [ ] 路由配置 (/artworks/chapter-studio/:id)

**接受标准:**
- AC1: 用户可以在页面内查看章节内所有场景
- AC2: 一键启动章节工作流
- AC3: 实时显示每个场景的制作进度
- AC4: 支持暂停/继续工作流
- AC5: 可以快速编辑单个场景

---

## 🏗️ 技术设计

### 章节工作流状态机

```
pending → in_progress → completed
                    ↓
                 failed
```

### 服务类结构

```python
# apps/artworks/services/chapter_workflow.py

class ChapterWorkflowService:
    """章节工作流编排服务"""

    def start_chapter_workflow(self, chapter_id: int) -> str:
        """启动章节工作流"""

    def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""

    def resume_workflow(self, workflow_id: str) -> bool:
        """继续工作流"""

    def get_workflow_status(self, workflow_id: str) -> dict:
        """获取工作流状态"""

    def _process_scene(self, scene_id: int) -> bool:
        """处理单个场景"""
```

```python
# apps/artworks/services/frame_extraction.py

class FrameExtractionService:
    """首尾帧提取服务"""

    def extract_head_frame(self, scene_id: int) -> str:
        """提取场景首帧"""

    def extract_tail_frame(self, scene_id: int) -> str:
        """提取场景尾帧"""

    def extract_frame_from_shot(self, shot_id: int) -> str:
        """从镜头提取帧"""
```

### 数据模型扩展

```python
# 新增模型或扩展现有模型

class ChapterWorkflow(models.Model):
    """章节工作流记录"""
    chapter = models.ForeignKey(Chapter, ...)
    workflow_id = models.UUIDField(default=uuid.uuid4)
    status = models.CharField(...)  # pending/in_progress/completed/failed/paused

    current_scene = models.ForeignKey(ScriptScene, ..., null=True)
    progress_percentage = models.IntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True)
```

---

## 🔌 API 端点设计

```
POST   /api/v1/artworks/chapters/{id}/start-workflow/
POST   /api/v1/artworks/chapters/{id}/pause-workflow/
POST   /api/v1/artworks/chapters/{id}/resume-workflow/
GET    /api/v1/artworks/chapters/{id}/workflow-status/
POST   /api/v1/artworks/scenes/{id}/extract-frames/
GET    /api/v1/artworks/scenes/{id}/frames/
```

---

## 🔌 WebSocket 路由

```python
# config/routing.py

websocket_urlpatterns = [
    ...
    path('ws/chapters/<int:chapter_id>/workflow/', ChapterWorkflowConsumer.as_asgi()),
]
```

---

## 📈 测试策略

### 单元测试
- ChapterWorkflowService 各方法测试
- FrameExtractionService 测试
- 工作流状态机测试
- 错误重试逻辑测试

### 集成测试
- 完整章节工作流测试
- 首尾帧提取集成测试

### 目标测试覆盖率
- 80%+ 新代码覆盖率

---

## 📝 Notes

**设计决策:**
- 使用 Celery 任务队列处理异步场景生成
- 使用 Redis 存储工作流状态 (支持暂停/继续)
- WebSocket 推送进度更新到前端

**风险与缓解:**
- 长时间运行任务可能超时 → 使用 Celery 后台任务
- 大批量图片生成可能耗尽内存 → 限制并发数，分批处理

---

**Epic Owner:** BMad Development Team
**创建日期:** 2026-02-11
**状态:** backlog
