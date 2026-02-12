# 【Story 12-5】代码评审修改建议（第2版）

> 评审日期: 2026-02-12
> 评审范围: Story 12-5 首尾帧提取服务 P0 修复验证 + 新问题发现
> 评审人员: 架构师 + PM + 测试工程师
> 评审方式: 官方对抗性代码评审（必须找出问题）

---

## 评审结果总览

| 问题等级 | 数量 | 状态 |
|---------|------|------|
| P0 - 阻塞性问题 | 3 | ❌ 未修复 |
| P1 - 高优先级 | 4 | ❌ 未修复 |
| P2 - 中优先级 | 5 | ❌ 未修复 |
| P3 - 低优先级 | 3 | ❌ 未修复 |

**关键发现**: P0 修复引入了新的导入错误，导致所有测试无法运行！

---

## P0 - 阻塞性问题（必须立即修复）

### P0-1: 导入错误 - `FrameSelectionStrategy` 导入位置错误

**问题描述**:
`apps/artworks/services/__init__.py` 第 16-25 行尝试从 `repositories.py` 导入 `FrameSelectionStrategy`，但该类实际定义在 `frame_selection.py` 中。

**当前代码**:
```python
# __init__.py 第 16-25 行
from .repositories import (
    ISceneRepository,
    IShotRepository,
    RepositoryFactory,
    FrameSelectionStrategy,  # ❌ 错误！应该在 frame_selection.py
    DefaultFrameSelectionStrategy,  # ❌ 错误！应该在 frame_selection.py
    ImageOptimizationService,  # ❌ 错误！应该在 image_optimization.py
    FrameExtractionService,  # ❌ 错误！应该在 frame_extraction.py
    FrameExtractionConfig,  # ❌ 错误！应该在 config.py
)
```

**影响**:
- 所有测试无法运行（ImportError）
- 生产环境启动失败
- 5 个测试文件收集失败

**修复建议**:
```python
# __init__.py 正确导入方式
from .config import FrameExtractionConfig
from .frame_selection import FrameSelectionStrategy, DefaultFrameSelectionStrategy
from .image_optimization import ImageOptimizationService
from .frame_extraction import FrameExtractionService
from .repositories import (
    ISceneRepository,
    IShotRepository,
    RepositoryFactory,
)

# 或者更简洁的导入（推荐）
from .config import FrameExtractionConfig, get_frame_config
from .frame_selection import FrameSelectionStrategy, DefaultFrameSelectionStrategy
from .image_optimization import ImageOptimizationService
from .repositories import (
    ISceneRepository,
    IShotRepository,
    RepositoryFactory,
)
from .frame_extraction import FrameExtractionService

# 导出 FrameExtractionService 为 FrameExtractor 向后兼容
FrameExtractor = FrameExtractionService
```

**验证命令**:
```bash
cd backend && uv run pytest apps/artworks/tests/test_frame_extraction_service.py -v
```

---

### P0-2: `Shot` 模型缺少 `is_head_frame` 和 `is_tail_frame` 字段

**问题描述**:
代码多处使用 `shot.is_head_frame` 和 `shot.is_tail_frame` 字段，但模型中未定义这些字段。

**受影响位置**:
1. `repositories.py` 第 202 行: `shots.filter(is_head_frame=True).first()`
2. `repositories.py` 第 226 行: `shots.filter(is_tail_frame=True).first()`
3. `frame_selection.py` 第 85 行: `shots.filter(is_head_frame=True).first()`
4. `frame_selection.py` 第 111 行: `shots.filter(is_tail_frame=True).first()`
5. `test_frame_extraction_service.py` 第 59-62 行

**影响**:
- 运行时会抛出 `FieldError: Cannot resolve keyword 'is_head_frame' into field`
- 标记首尾帧功能无法使用

**修复建议**:

检查 `Shot` 模型是否有以下字段（第1版评审中提到需要添加）:
```python
# apps/artworks/models.py Shot 模型应包含
class Shot(models.Model):
    # ... 其他字段 ...
    is_head_frame = models.BooleanField(
        default=False,
        verbose_name=_("是首帧"),
        help_text=_("标记此镜头为场景首帧")
    )
    is_tail_frame = models.BooleanField(
        default=False,
        verbose_name=_("是尾帧"),
        help_text=_("标记此镜头为场景尾帧")
    )
```

如果字段不存在，需要创建数据库迁移:
```bash
uv run python manage.py makemigrations
uv run python manage.py migrate
```

---

### P0-3: `permissions.py` 中的 `IsOwner` 权限类逻辑错误

**问题描述**:
`permissions.py` 第 41 行使用 `obj.artwork.user` 验证所有权，但 `Artwork` 模型没有 `user` 字段（根据 Story 12-5 需求，Artwork 与用户无直接关联）。

**当前代码**:
```python
# permissions.py 第 40-41 行
return obj.artwork.user == request.user  # ❌ Artwork 没有 user 字段
```

**影响**:
- 所有权限检查失败
- 返回 `AttributeError: 'Artwork' object has no attribute 'user'`
- API 端点无法正常工作

**修复建议**:

需要确认实际的权限控制逻辑。根据 Story 12-5 需求，可能的修复方案：

**方案 A - 移除权限检查（如果本功能不需要权限控制）**:
```python
class IsOwner(permissions.BasePermission):
    """允许所有认证用户"""
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated
```

**方案 B - 基于 Project 的权限（如果有关联）**:
```python
class IsOwner(permissions.BasePermission):
    """验证用户是否有权限访问该场景所属的作品"""
    def has_object_permission(self, request, view, obj):
        # obj 是 Chapter 或 ScriptScene
        # 假设 Artwork 通过某种方式关联到用户
        artwork = obj.artwork if hasattr(obj, 'artwork') else obj.chapter.artwork
        # TODO: 实现实际的权限检查逻辑
        return True  # 临时允许所有认证用户
```

---

## P1 - 高优先级问题

### P1-1: `tasks.py` 中 `extract_frames_task` 返回数据结构不一致

**问题描述**:
`tasks.py` 第 1769-1873 行的 `extract_frames_task` 在成功时返回的字典结构与调用方期望不一致。

**当前代码**:
```python
# tasks.py 第 1843-1844 行
result["head_frame_url"] = scene.head_frame.url if scene.head_frame else None
result["tail_frame_url"] = scene.tail_frame.url if scene.tail_frame else None
```

**问题**:
- 直接访问 `.url` 可能抛出 `AttributeError`（当文件为 None 时）
- 没有使用 DRF 的序列化器统一格式

**修复建议**:
```python
# 使用 get_field() 安全访问
def get_file_url(file_field):
    if file_field and hasattr(file_field, 'url'):
        return file_field.url
    return None

result["head_frame_url"] = get_file_url(scene.head_frame)
result["tail_frame_url"] = get_file_url(scene.tail_frame)
```

---

### P1-2: 首尾帧文件命名缺少唯一性保证

**问题描述**:
`frame_extraction.py` 中生成的文件名格式为 `head_{scene_id}_{shot_id}.jpg`，但没有考虑并发提取和重新提取的情况。

**当前代码**:
```python
# frame_extraction.py
filename = f"head_{scene.id}_{shot.id}.jpg"  # 不够唯一
```

**影响**:
- 多次提取会覆盖旧文件
- 并发提取可能导致文件冲突
- 无法区分不同时间提取的帧

**修复建议**:
```python
import uuid
from datetime import datetime

# 添加时间戳和 UUID 确保唯一性
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
unique_id = uuid.uuid4().hex[:8]
filename = f"head_{scene.id}_{shot.id}_{timestamp}_{unique_id}.jpg"

# 或者使用 Django 的自动生成
filename = f"scenes/head_{scene.id}/{shot.id}_{uuid.uuid4().hex}.jpg"
```

---

### P1-3: 图片优化服务缺少错误恢复机制

**问题描述**:
`image_optimization.py` 中的 `_resize_image()` 和 `_optimize_jpeg()` 方法在 PIL 操作失败时没有恢复机制。

**当前代码**:
```python
# image_optimization.py
def _resize_image(self, image: Image.Image, target_size: tuple) -> Image.Image:
    # ... 没有异常处理 ...
    return image.resize(target_size, Image.LANCZOS)
```

**影响**:
- 损坏的图片会导致整个提取流程失败
- 没有降级方案

**修复建议**:
```python
def _resize_image(self, image: Image.Image, target_size: tuple) -> Image.Image:
    try:
        return image.resize(target_size, Image.LANCZOS)
    except Exception as e:
        logger.warning(f"图片调整失败，使用 NEAREST: {e}")
        # 降级到更简单的算法
        return image.resize(target_size, Image.NEAREST)
```

---

### P1-4: 缺少 API 速率限制

**问题描述**:
`views.py` 中的首尾帧提取 API 没有速率限制，可能被滥用。

**当前代码**:
```python
# views.py - 没有速率限制
class ScriptSceneViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def extract_frames(self, request, pk=None):
        # 直接处理，无速率限制
```

**影响**:
- 恶意用户可能频繁调用导致服务器资源耗尽
- 没有防抖机制

**修复建议**:
```python
from rest_framework.throttling import UserRateThrottle

class FrameExtractionThrottle(UserRateThrottle):
    rate = '10/min'  # 每分钟最多 10 次
    scope = 'frame_extraction'

class ScriptSceneViewSet(viewsets.ModelViewSet):
    @action(
        detail=True,
        methods=['post'],
        throttle_classes=[FrameExtractionThrottle]
    )
    def extract_frames(self, request, pk=None):
        # ... 现有逻辑 ...
```

---

## P2 - 中优先级问题

### P2-1: `test_frame_extraction_api.py` 缺少测试数据清理

**问题描述**:
测试用例没有在测试后清理创建的临时文件，可能导致磁盘空间泄漏。

**当前代码**:
```python
# test_frame_extraction_api.py
def test_extract_frames_saves_to_scene(self):
    self.client.post(f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/")
    # ... 没有清理上传的图片文件 ...
```

**修复建议**:
```python
import shutil
import tempfile

@pytest.fixture(autouse=True)
def cleanup_media_files():
    """自动清理测试媒体文件"""
    yield
    # 测试结束后清理
    media_root = settings.MEDIA_ROOT
    test_upload_dir = os.path.join(media_root, 'scenes')
    if os.path.exists(test_upload_dir):
        shutil.rmtree(test_upload_dir)
```

---

### P2-2: `admin.py` 中的健康检查功能未实现

**问题描述**:
`admin.py` 第 492-497 行的 `test_health` action 只是打印 "待实现"。

**当前代码**:
```python
# admin.py 第 492-497 行
def test_health(self, request, queryset):
    """测试引擎健康状态"""
    # TODO: 实现健康检查逻辑
    self.message_user(request, _("健康检查功能待实现"))  # ❌ 未实现
```

**修复建议**:
```python
def test_health(self, request, queryset):
    """测试引擎健康状态"""
    from apps.artworks.services.comfyui_service import get_comfyui_service

    service = get_comfyui_service()
    result = service.health_check()

    if result.get('healthy'):
        self.message_user(request, f"引擎健康: {result}")
    else:
        self.message_user(request, f"引擎异常: {result.get('error')}", level='ERROR')
```

---

### P2-3: `repositories.py` 中日志级别使用不当

**问题描述**:
`repositories.py` 在场景不存在时使用 `logger.warning()`，但这种情况是正常业务逻辑。

**当前代码**:
```python
# repositories.py 第 140 行
except ScriptScene.DoesNotExist:
    logger.warning(f"场景不存在: scene_id={scene_id}")  # 应该是 info
    return None
```

**修复建议**:
```python
except ScriptScene.DoesNotExist:
    logger.info(f"场景不存在: scene_id={scene_id}")  # 正常业务情况
    return None
```

---

### P2-4: 首尾帧提取服务缺少事务处理

**问题描述**:
`frame_extraction.py` 中的 `extract_frames()` 方法没有使用数据库事务，可能导致部分更新失败。

**当前代码**:
```python
# frame_extraction.py
def extract_frames(self, scene_id: int) -> dict:
    # ... 没有 transaction.atomic ...
    self._scene_repo.update_frames(scene, head_frame, tail_frame)
```

**修复建议**:
```python
from django.db import transaction

@transaction.atomic
def extract_frames(self, scene_id: int) -> dict:
    """使用事务确保数据一致性"""
    # ... 现有逻辑 ...
```

---

### P2-5: 测试覆盖率不完整

**问题描述**:
缺少以下测试场景：
1. 并发提取同一场景
2. 大文件（超过 10MB）提取
3. 特殊字符文件名处理
4. 图片格式转换边界情况

**修复建议**:
```python
# test_frame_extraction_service.py 新增
def test_concurrent_extraction(self):
    """测试并发提取同一场景"""
    import threading

    scene = self._create_scene_with_shots(shot_count=2)
    results = []
    threads = []

    def extract():
        result = self.service.extract_frames(scene.id)
        results.append(result)

    # 启动多个线程同时提取
    for _ in range(3):
        t = threading.Thread(target=extract)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # 验证至少有一个成功
    success_count = sum(1 for r in results if r.get('success'))
    assert success_count >= 1
```

---

## P3 - 低优先级问题

### P3-1: 文档字符串格式不统一

**问题描述**:
部分函数使用 Google 风格文档字符串，部分使用 NumPy 风格。

**修复建议**:
统一使用 Google 风格（DRF 标准）:
```python
def extract_frames(self, scene_id: int) -> dict:
    """提取场景首尾帧.

    Args:
        scene_id: 场景 ID

    Returns:
        包含 success, message 等字段的字典

    Raises:
        ValueError: 场景不存在或无有效镜头
    """
```

---

### P3-2: 硬编码的图片尺寸参数

**问题描述**:
`config.py` 中将 1920x1080 硬编码为默认值，不够灵活。

**当前代码**:
```python
# config.py
FRAME_TARGET_SIZE: Tuple[int, int] = (1920, 1080)  # 硬编码
```

**修复建议**:
```python
# config.py
DEFAULT_FRAME_TARGET_SIZE = (1920, 1080)  # 提供多种预设
PRESET_SIZES = {
    '1080p': (1920, 1080),
    '720p': (1280, 720),
    '480p': (640, 480),
}
```

---

### P3-3: 缺少性能监控指标

**问题描述**:
服务没有记录关键性能指标（提取耗时、文件大小等）。

**修复建议**:
```python
import time

def extract_frames(self, scene_id: int) -> dict:
    start_time = time.time()

    # ... 提取逻辑 ...

    elapsed = time.time() - start_time
    logger.info(f"首尾帧提取完成: scene_id={scene_id},耗时={elapsed:.2f}s")

    result['metrics'] = {
        'elapsed_seconds': elapsed,
        'file_size_kb': ...,
    }
    return result
```

---

## P0 问题修复验证清单

- [ ] **P0-1**: 修复 `__init__.py` 导入错误
  - 验证命令: `uv run pytest apps/artworks/tests/test_frame_extraction_service.py -v`
  - 预期: 无 ImportError

- [ ] **P0-2**: 确认 `Shot` 模型有 `is_head_frame` 和 `is_tail_frame` 字段
  - 验证命令: 检查 `apps/artworks/models.py` Shot 模型定义
  - 预期: 两个字段都存在且已迁移

- [ ] **P0-3**: 修复 `permissions.py` 中 `IsOwner` 权限类
  - 验证命令: 运行 API 测试
  - 预期: 无 AttributeError

---

## 架构合规性检查

### ✅ 已符合的架构原则

1. **SRP（单一职责）**: `ImageOptimizationService` 独立处理图片优化
2. **DIP（依赖倒置）**: 使用仓储接口 `ISceneRepository`、`IShotRepository`
3. **OCP（开闭原则）**: `FrameSelectionStrategy` 使用 Protocol，易于扩展

### ❌ 不符合的架构原则

1. **模块导入混乱**: `__init__.py` 导入错误导致无法使用（P0-1）
2. **缺少事务管理**: 数据更新没有事务保护（P2-4）
3. **错误处理不完整**: 图片处理缺少降级方案（P1-3）

---

## 测试工程师检查结果

### 测试可运行性: ❌ 失败

**问题**: 所有测试无法收集，存在 ImportError

```bash
$ uv run pytest apps/artworks/tests/test_frame_extraction_service.py -v
ERROR: ImportError: cannot import name 'FrameSelectionStrategy' from 'apps.artworks.services.repositories'
```

### 测试覆盖情况（假设能运行后）:

| 模块 | 单元测试 | 集成测试 | 覆盖率估计 |
|------|---------|-----------|------------|
| frame_extraction.py | ✅ | ✅ | ~85% |
| image_optimization.py | ⚠️ 部分 | ❌ | ~60% |
| repositories.py | ❌ 无 | ❌ | 0% |
| frame_selection.py | ❌ 无 | ✅ | ~70% |

### 测试缺失项:

1. ❌ 并发测试
2. ❌ 大文件测试
3. ❌ 边界值测试（零镜头、空图片等）
4. ❌ 性能测试

---

## PM 需求匹配度检查

### ✅ 已实现的需求

1. ✅ 首尾帧自动提取
2. ✅ 标记优先级（is_head_frame / is_tail_frame）
3. ✅ 图片优化（1080p JPEG）
4. ✅ API 端点
5. ✅ Celery 异步任务

### ❌ 部分实现的需求

1. ⚠️ 权限控制：存在但逻辑错误（P0-3）
2. ⚠️ 错误处理：缺少降级方案（P1-3）

### ❌ 未实现的需求

根据 Story 12-5 需求文档，需要确认以下功能：

1. ❓ 批量提取多个场景
2. ❓ 提取进度实时通知
3. ❓ 首尾帧预览缩略图生成

---

## 修复优先级建议

### 第一阶段（立即修复，阻塞性）:
1. **P0-1**: 修复导入错误 - 预计 10 分钟
2. **P0-2**: 确认模型字段 - 预计 5 分钟（如果已存在）或 30 分钟（需要添加）
3. **P0-3**: 修复权限类 - 预计 15 分钟

### 第二阶段（本周修复）:
1. **P1-2**: 文件命名唯一性 - 预计 20 分钟
2. **P1-3**: 错误恢复机制 - 预计 30 分钟
3. **P2-4**: 添加事务处理 - 预计 15 分钟

### 第三阶段（下次迭代）:
1. **P1-1**: 返回数据结构统一
2. **P1-4**: API 速率限制
3. **P2-1 到 P2-5**: 测试和文档改进
4. **P3-1 到 P3-3**: 代码质量提升

---

## 总结

### 关键发现

1. **P0 修复引入了新的严重问题**：导入错误导致所有测试失败，必须立即修复
2. **架构设计基本正确**：仓储模式、策略模式使用得当，但实现细节有误
3. **测试覆盖需要补充**：缺少并发、大文件、边界测试

### 下一步行动

1. **立即修复 P0 问题**，确保测试可以运行
2. **运行完整测试套件**验证修复
3. **补充缺失的测试用例**
4. **按优先级修复 P1/P2 问题**

### 评审结论

**当前状态**: ❌ 代码评审不通过

**原因**:
- P0 问题导致代码无法正常运行
- 测试套件完全无法执行
- 存在数据一致性风险

**通过条件**:
- 所有 P0 问题修复并通过测试
- 测试覆盖率达到 80% 以上
- 无 P0/P1 级别架构违反

---

**评审人员签名**:
- 架构师: [待确认]
- PM: [待确认]
- 测试工程师: [待确认]

**下次评审**: P0 问题修复后安排
