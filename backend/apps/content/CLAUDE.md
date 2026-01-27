# CLAUDE.md - 内容生成域 (content)

[根目录](../../CLAUDE.md) > [backend](../) > [apps](../) > **content**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

内容生成域负责：
- Pipeline阶段处理器实现（文案改写、分镜生成、文生图、图生视频）
- 内容数据模型（ContentRewrite、Storyboard、GeneratedImage、GeneratedVideo）
- 运镜参数管理（CameraMovement）

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [models.py](./models.py) | 内容数据模型（5个模型） |
| [processors/llm_stage.py](./processors/llm_stage.py) | LLM处理器（510行） |
| [processors/text2image_stage.py](./processors/text2image_stage.py) | 文生图处理器 |
| [processors/image2video_stage.py](./processors/image2video_stage.py) | 图生视频处理器 |
| [processors/camera_movement.py](./processors/camera_movement.py) | 运镜生成处理器 |
| [views.py](./views.py) | 内容API视图 |
| [urls.py](./urls.py) | URL配置 |

---

## 对外接口

### 数据模型

- **ContentRewrite** - 文案改写结果（1对1 with Project）
- **Storyboard** - 分镜（1对多 with Project）
- **GeneratedImage** - 生成图片（多对1 with Storyboard）
- **CameraMovement** - 运镜参数（1对1 with Storyboard）
- **GeneratedVideo** - 生成视频（多对1 with Storyboard）

### 处理器接口

所有处理器继承自 `StageProcessor`：
```python
class LLMStageProcessor(StageProcessor):
    async def validate(self, context) -> bool
    async def process(self, context) -> StageResult
    async def on_failure(self, context, error)
```

---

## 关键依赖

```python
# 依赖的模块
from core.pipeline.base import StageProcessor
from core.ai_client.factory import create_ai_client
from apps.projects.models import Project, ProjectStage
from apps.models.models import ModelProvider
```

---

## 测试覆盖

- ❌ 无单元测试
- 需要添加处理器测试

---

## 变更记录

### 2026-01-26 12:08:52
- 初始化内容生成域文档
