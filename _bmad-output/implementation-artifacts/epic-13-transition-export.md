# Epic 13: 转场与导出

**Epic ID:** epic-13
**创建日期:** 2026-02-11
**状态:** backlog
**优先级:** P0 (核心功能)
**预估工作量:** 1周 (2个Stories)

---

## 📋 Epic 概述

**目标:** 实现章节间转场配置和最终视频导出功能，完成"小说 → 漫剧视频"的完整闭环。

**价值:**
- 完成用户核心需求：导出可分享的漫剧视频
- 提供专业的转场效果，提升观看体验
- 支持多种导出格式和质量设置

**依赖:**
- 🟡 Epic 12: 章节推进工作流 (首尾帧提取)
- ✅ Epic 11.2: ScriptScene 转场配置字段

---

## 🎯 Epic 目标

### 主要目标

1. **转场配置 UI** - 可视化配置场景间转场效果
2. **视频合成与导出** - 拼接场景 + 应用转场 + 导出视频

### 成功标准

- [ ] 用户可以配置场景间的转场类型和时长
- [ ] 支持预览转场效果
- [ ] 可以将章节导出为 MP4 视频
- [ ] 支持多种分辨率和质量设置
- [ ] 导出进度实时显示

---

## 📊 Stories 清单

### Story 13-1: 转场配置与预览

**状态:** backlog
**预估:** 2-3天
**优先级:** P0

**描述:** 创建转场配置 UI，支持可视化配置和预览场景间转场效果。

**任务:**
- [ ] 创建 TransitionConfigPanel.vue 配置面板
- [ ] 创建 TransitionPreview.vue 预览组件
- [ ] 实现转场类型选择器 (fade/dissolve/wipe/slide/zoom)
- [ ] 实现转场时长滑块 (0.5s - 5s)
- [ ] 实现转场预览动画
- [ ] 添加转场 API 端点
- [ ] 更新 ScriptScene 序列化器
- [ ] 编写单元测试

**接受标准:**
- AC1: 用户可以选择场景间的转场类型
- AC2: 可以调整转场时长 (0.5s - 5s)
- AC3: 可以预览转场效果
- AC4: 转场配置保存到 ScriptScene 模型
- AC5: 支持批量应用转场配置

---

### Story 13-2: 视频合成与导出

**状态:** backlog
**预估:** 3-5天
**优先级:** P0

**描述:** 实现视频合成服务，将章节内所有场景拼接成最终视频，应用转场效果。

**任务:**
- [ ] 创建 VideoCompositionService 服务类
- [ ] 集成 FFmpeg 或 moviepy
- [ ] 实现场景拼接逻辑
- [ ] 实现转场效果应用
- [ ] 实现音频合成 (BGM + 对话)
- [ ] 添加字幕叠加功能
- [ ] 实现 Celery 异步导出任务
- [ ] 添加导出 API 端点
- [ ] 创建 ExportModal.vue 导出配置对话框
- [ ] 实现导出进度追踪
- [ ] 编写单元测试

**接受标准:**
- AC1: 可以将章节导出为 MP4 视频
- AC2: 支持多种分辨率 (720p/1080p/4K)
- AC3: 支持多种质量设置 (低/中/高)
- AC4: 正确应用场景间转场效果
- AC5: 音视频同步
- AC6: 导出进度实时显示
- AC7: 导出完成后提供下载链接

---

## 🏗️ 技术设计

### 转场类型定义

```python
# apps/artworks/models.py - 扩展

TRANSITION_TYPES = [
    ('fade', '淡入淡出'),
    ('dissolve', '溶解'),
    ('wipe', '擦除'),
    ('slide', '滑动'),
    ('zoom', '缩放'),
    ('none', '无转场'),
]

# ScriptScene 已有字段 (Epic 11.2):
# - transition_to_next: ForeignKey to ScriptScene
# - transition_type: CharField
# - transition_duration: FloatField
```

### 视频合成服务

```python
# apps/artworks/services/video_composition.py

from moviepy.editor import *
from celery import shared_task

class VideoCompositionService:
    """视频合成服务"""

    def compose_chapter_video(
        self,
        chapter_id: int,
        resolution: str = "1080p",
        quality: str = "high",
        output_format: str = "mp4"
    ) -> str:
        """合成章节视频"""

    def _compose_scenes(self, scenes: List[ScriptScene]) -> VideoClip:
        """拼接场景"""

    def _apply_transition(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        transition_type: str,
        duration: float
    ) -> VideoClip:
        """应用转场效果"""

    def _add_audio(self, video: VideoClip, chapter: Chapter) -> VideoClip:
        """添加音频"""

    def _add_subtitles(self, video: VideoClip, scenes: List[ScriptScene]) -> VideoClip:
        """添加字幕"""

@shared_task
def export_chapter_video_task(chapter_id: int, config: dict) -> str:
    """异步导出章节视频任务"""
```

### 导出配置

```python
# apps/artworks/models.py - 新增

class VideoExport(models.Model):
    """视频导出记录"""
    chapter = models.ForeignKey(Chapter, ...)
    export_id = models.UUIDField(default=uuid.uuid4)

    # 配置
    resolution = models.CharField(...)  # 720p/1080p/4k
    quality = models.CharField(...)  # low/medium/high
    format = models.CharField(default='mp4', max_length=10)

    # 状态
    status = models.CharField(...)  # pending/processing/completed/failed
    progress_percentage = models.IntegerField(default=0)

    # 输出
    output_file = models.FileField(...)
    file_size = models.IntegerField(null=True)
    duration_seconds = models.FloatField(null=True)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
```

---

## 🔌 API 端点设计

```
POST   /api/v1/artworks/chapters/{id}/export/
GET    /api/v1/artworks/exports/{export_id}/status/
GET    /api/v1/artworks/exports/{export_id}/download/
DELETE /api/v1/artworks/exports/{export_id}/
GET    /api/v1/artworks/chapters/{id}/exports/
```

### 导出请求示例

```json
POST /api/v1/artworks/chapters/123/export/

{
  "resolution": "1080p",
  "quality": "high",
  "format": "mp4",
  "include_subtitles": true,
  "background_music": null
}
```

---

## 🔌 WebSocket 路由

```python
# config/routing.py

websocket_urlpatterns = [
    ...
    path('ws/exports/<uuid:export_id>/', ExportProgressConsumer.as_asgi()),
]
```

### 进度推送格式

```json
{
  "type": "export.progress",
  "export_id": "uuid",
  "status": "processing",
  "progress": 45,
  "current_step": "applying_transitions",
  "message": "正在应用转场效果..."
}
```

---

## 🎨 UI 设计

### 转场配置面板

```
┌─────────────────────────────────────────────────────────┐
│ 转场配置                                    [保存][取消] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  从: 纳米中心-日        →  到: 实验室-夜                │
│                                                          │
│  转场类型:                                               │
│  ○ 无转场                                                │
│  ● 淡入淡出 (Fade)     [预览]                            │
│  ○ 溶解 (Dissolve)     [预览]                            │
│  ○ 擦除 (Wipe)         [预览]                            │
│  ○ 滑动 (Slide)        [预览]                            │
│  ○ 缩放 (Zoom)         [预览]                            │
│                                                          │
│  转场时长: ████████░░ 2.0 秒                             │
│                                                          │
│  [应用到所有场景]  [批量配置]                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 导出配置对话框

```
┌─────────────────────────────────────────────────────────┐
│ 导出视频                                    [取消][导出] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  分辨率:                                                 │
│  ○ 720p (HD)         1280x720                           │
│  ● 1080p (Full HD)   1920x1080                          │
│  ○ 4K (Ultra HD)     3840x2160                          │
│                                                          │
│  质量:                                                   │
│  ○ 低 (小文件)                                          │
│  ○ 中 (平衡)                                             │
│  ● 高 (最佳质量)                                         │
│                                                          │
│  格式: MP4                                               │
│                                                          │
│  ☑ 包含字幕                                              │
│  ☐ 背景音乐: [选择...]                                   │
│                                                          │
│  预计文件大小: ~150 MB                                   │
│  预计导出时间: ~5 分钟                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 测试策略

### 单元测试
- VideoCompositionService 各方法测试
- 转场效果应用测试
- 音视频合成测试
- 字幕叠加测试

### 集成测试
- 完整导出流程测试
- 不同分辨率/质量配置测试
- 转场效果验证测试

### 目标测试覆盖率
- 80%+ 新代码覆盖率

---

## 📝 Notes

**技术选型:**
- **moviepy** 或 **ffmpeg-python** 用于视频合成
- **Celery** 用于异步导出任务
- **Redis** 存储导出进度

**性能考虑:**
- 视频导出是 CPU 密集型操作，使用独立 Worker 队列
- 大文件导出使用分块上传到云存储
- 支持断点续传

**风险与缓解:**
- FFmpeg 安装问题 → 使用 Docker 镜像预装
- 长时间导出可能超时 → 使用 Celery 后台任务
- 存储空间不足 → 实现清理策略，定期删除旧导出

---

**Epic Owner:** BMad Development Team
**创建日期:** 2026-02-11
**状态:** backlog
