# CLAUDE.md - 工作流引擎模块 (pipeline)

[根目录](../../../CLAUDE.md) > [backend](../../) > [core](../) > **pipeline**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

工作流引擎是系统的**责任链模式实现层**，负责：
- 定义Pipeline抽象基类（StageProcessor）
- 编排工作流阶段执行顺序
- 自动处理阶段重试和错误恢复
- 携带上下文数据（PipelineContext）

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [base.py](./base.py) | 抽象基类（StageProcessor、PipelineContext、StageResult） |
| [orchestrator.py](./orchestrator.py) | 工作流编排器（ProjectPipeline） |

### 类层次结构

```
PipelineContext (数据类)
    ├─ results: Dict[str, Any]     # 各阶段结果
    ├─ metadata: Dict[str, Any]    # 元数据
    ├─ add_result()                # 添加结果
    └─ get_result()                # 获取结果

StageResult (数据类)
    ├─ success: bool               # 是否成功
    ├─ data: Dict[str, Any]        # 结果数据
    ├─ error: Optional[str]        # 错误信息
    └─ can_retry: bool             # 是否可重试

StageProcessor (抽象基类)
    ├─ validate()                  # 验证阶段
    ├─ process()                   # 执行阶段
    ├─ on_success()                # 成功处理
    └─ on_failure()                # 失败处理

ProjectPipeline (编排器)
    ├─ stages: List[StageProcessor]  # 阶段列表
    └─ execute()                     # 执行工作流
```

---

## 对外接口

### StageProcessor 接口

```python
class StageProcessor(ABC):
    """阶段处理器抽象基类"""

    def __init__(self, stage_name: str):
        self.stage_name = stage_name

    @abstractmethod
    async def validate(self, context: PipelineContext) -> bool:
        """
        验证阶段是否可以执行

        Returns:
            bool: 是否可以执行
        """
        pass

    @abstractmethod
    async def process(self, context: PipelineContext) -> StageResult:
        """
        执行阶段核心逻辑

        Returns:
            StageResult: 阶段执行结果
        """
        pass

    @abstractmethod
    async def on_failure(self, context: PipelineContext, error: Exception):
        """失败处理"""
        pass

    async def on_success(self, context: PipelineContext, result: StageResult):
        """成功处理（可选重写）"""
        pass
```

### PipelineContext 接口

```python
@dataclass
class PipelineContext:
    """工作流上下文"""

    project_id: str
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, stage: str, data: Any):
        """添加阶段结果"""
        self.results[stage] = data

    def get_result(self, stage: str) -> Optional[Any]:
        """获取阶段结果"""
        return self.results.get(stage)

    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        return self.metadata.get(key)
```

### ProjectPipeline 接口

```python
class ProjectPipeline:
    """项目工作流编排器"""

    def __init__(self, stages: List[StageProcessor]):
        self.stages = stages

    async def execute(self, project_id: str) -> PipelineContext:
        """
        执行完整的项目工作流

        Args:
            project_id: 项目ID

        Returns:
            PipelineContext: 包含所有结果的上下文
        """
        context = PipelineContext(project_id=project_id)

        for stage in self.stages:
            # 1. 验证
            if not await stage.validate(context):
                raise ValidationError(...)

            # 2. 执行
            result = await stage.process(context)

            # 3. 处理结果
            if result.success:
                context.add_result(stage.stage_name, result.data)
                await stage.on_success(context, result)
            else:
                # 4. 重试或失败
                if result.can_retry:
                    result = await self._retry_stage(stage, context)
                if not result.success:
                    break  # 停止工作流

        return context
```

---

## 关键依赖与配置

### 使用示例

```python
from core.pipeline.base import StageProcessor, PipelineContext, StageResult
from core.pipeline.orchestrator import ProjectPipeline

# 1. 定义阶段处理器
class RewriteProcessor(StageProcessor):
    async def validate(self, context):
        return bool(context.get_metadata('original_topic'))

    async def process(self, context):
        # 处理逻辑
        return StageResult(success=True, data={'text': '...'})

    async def on_failure(self, context, error):
        print(f"失败: {error}")

# 2. 创建工作流
pipeline = ProjectPipeline([
    RewriteProcessor('rewrite'),
    StoryboardProcessor('storyboard'),
    ImageGenerationProcessor('image_generation'),
    # ...
])

# 3. 执行
context = await pipeline.execute(project_id='xxx')
```

### 实际应用

在 `apps.content.processors.llm_stage.py` 中：

```python
class LLMStageProcessor(StageProcessor):
    """LLM阶段处理器（文案改写、分镜、运镜）"""

    async def validate(self, context: PipelineContext) -> bool:
        """验证输入数据"""
        return bool(context.get_result('rewrite'))

    async def process(self, context: PipelineContext) -> StageResult:
        """调用AI客户端生成"""
        client = create_ai_client(self.model_provider)
        response = await client.generate(prompt=...)

        if response.success:
            return StageResult(success=True, data=response.text)
        else:
            return StageResult(success=False, error=response.error)

    async def on_failure(self, context: PipelineContext, error: Exception):
        """更新阶段状态"""
        stage = ProjectStage.objects.get(...)
        stage.status = 'failed'
        stage.error_message = str(error)
        stage.save()
```

---

## 数据模型

### 无独立数据模型

本模块是纯业务逻辑层，不包含Django模型。依赖 `apps.projects.models.ProjectStage` 存储状态。

---

## 测试与质量

### 当前测试覆盖 (Day 6更新)

- ✅ **Base 92%覆盖** - `test_core_pipeline_base.py` (99%覆盖)
- ✅ **Orchestrator 82%覆盖** - `test_pipeline_orchestrator.py` (92%覆盖)
- ✅ **集成测试** - `tests/integration/test_workflow_trigger.py` (Celery任务触发验证)

### 测试文件清单

```
tests/
├── test_core_pipeline_base.py        # 156行，99%覆盖
├── test_pipeline_orchestrator.py     # 103行，92%覆盖
└── integration/
    └── test_workflow_trigger.py      # Celery任务完整验证
```

### 测试重点

1. **基类测试**
   - StageProcessor 抽象方法强制实现
   - PipelineContext 数据存储和检索

2. **编排器测试**
   - 阶段按顺序执行
   - 失败阶段停止工作流
   - 重试机制（指数退避）

3. **集成测试**
   - 完整工作流执行
   - 上下文数据传递

---

## 常见问题 (FAQ)

### Q1: 如何添加新的阶段？

**A:** 步骤：
1. 继承 `StageProcessor`
2. 实现 `validate()`, `process()`, `on_failure()`
3. 注册到 `ProjectPipeline.stages`

示例：
```python
class MyCustomProcessor(StageProcessor):
    async def validate(self, context):
        return True

    async def process(self, context):
        # 你的逻辑
        return StageResult(success=True, data={})

    async def on_failure(self, context, error):
        # 失败处理
        pass

# 注册
pipeline = ProjectPipeline([
    ...,
    MyCustomProcessor('my_custom_stage')
])
```

### Q2: 如何控制阶段执行顺序？

**A:** 在 `ProjectPipeline` 初始化时按顺序传入：
```python
pipeline = ProjectPipeline([
    RewriteProcessor('rewrite'),           # 第1个
    StoryboardProcessor('storyboard'),     # 第2个
    ImageGenerationProcessor('image_generation'),  # 第3个
])
```

### Q3: 如何实现条件执行？

**A:** 在 `validate()` 方法中判断：
```python
class ConditionalProcessor(StageProcessor):
    async def validate(self, context):
        # 只在有分镜数据时执行
        return bool(context.get_result('storyboard'))
```

### Q4: 重试机制如何工作？

**A:** 编排器自动处理：
```python
# 默认重试3次，指数退避
if not result.success and result.can_retry:
    result = await self._retry_stage(stage, context)
    # 等待: 1s, 2s, 4s
```

---

## 相关文件清单

### 核心文件

```
backend/core/pipeline/
├── __init__.py
├── base.py                    # 抽象基类
└── orchestrator.py            # 工作流编排器
```

### 关键依赖

```
# 领域依赖
apps/projects/models.py       # Project, ProjectStage
apps/content/processors/       # 各阶段处理器实现

# 内部依赖
core/ai_client/                # AI客户端
```

### 实现的处理器

```
apps/content/processors/
├── llm_stage.py              # LLM处理器（文案、分镜、运镜）
├── text2image_stage.py       # 文生图处理器
├── image2video_stage.py      # 图生视频处理器
└── camera_movement.py        # 运镜生成处理器
```

---

## 变更记录 (Changelog)

### 2026-01-26 12:08:52
- 初始化工作流引擎模块文档
- 添加导航面包屑
- 完成接口、编排器、测试覆盖分析
