# 异步ORM扫描报告

**扫描时间**: 2026-01-28
**任务**: 异步ORM全项目推广（方案B）
**Django版本**: 3.2.15

---

## 🔍 扫描范围

扫描目录: `apps/projects/`, `apps/content/`, `apps/prompts/`, `apps/users/`

---

## ⚠️ 关键发现

### Django 3.2 不支持原生异步ORM

**测试结果**:
```python
await ModelProvider.objects.filter(...).afirst()
# AttributeError: 'QuerySet' object has no attribute 'afirst'
```

**结论**: Django 3.2.15 需要使用 `sync_to_async` 包装同步ORM调用

---

## 📋 需要修复的文件清单

### 🔴 高优先级 - 运行时错误

#### 1. apps/prompts/services.py

**问题**: 使用了不存在的 `.afirst()` 方法

**行号**: 58-61
```python
# ❌ 错误代码（会抛出AttributeError）
provider = await ModelProvider.objects.filter(
    provider_type='llm',
    is_active=True
).afirst()
```

**影响的异步函数**:
- `_get_ai_client` (line 49)
- `evaluate_prompt` (line 76) - 依赖_get_ai_client
- `compare_prompts` (line 120) - 依赖evaluate_prompt
- `suggest_improvements` (line 178) - 依赖_get_ai_client

**修复方案**:
```python
# ✅ 修复后
from apps.projects.pipeline_adapters import sync_to_async_wrapper

provider = await sync_to_async_wrapper(
    ModelProvider.objects.filter(
        provider_type='llm',
        is_active=True
    ).first
)()
```

**工作量**: 5分钟

---

#### 2. apps/prompts/models.py

**问题**: `get_variables_for_user` 是同步方法，但在异步视图中被await

**行号**: 208-231
```python
# ❌ 当前代码
@classmethod
def get_variables_for_user(cls, user, include_system=True):
    """同步方法"""
    query = Q(created_by=user, scope='user', is_active=True)
    if include_system:
        query |= Q(scope='system', is_active=True)
    variables = {}
    for var in cls.objects.filter(query):  # 同步ORM
        variables[var.key] = var.get_typed_value()
    return variables
```

**调用位置**: `apps/prompts/views.py:429`
```python
# ⚠️ 尝试await同步方法（会失败）
variables = await GlobalVariable.get_variables_for_user(
    user=request.user,
    include_system=include_system
)
```

**修复方案**:

**选项A**: 将方法改为异步（推荐）
```python
@classmethod
async def get_variables_for_user(cls, user, include_system=True):
    """异步方法"""
    from asgiref.sync import sync_to_async

    query = Q(created_by=user, scope='user', is_active=True)
    if include_system:
        query |= Q(scope='system', is_active=True)

    variables = {}
    # 使用sync_to_async包装filter和迭代
    variables_list = await sync_to_async(
        lambda: list(cls.objects.filter(query))
    )()

    for var in variables_list:
        variables[var.key] = var.get_typed_value()

    return variables
```

**选项B**: 在视图中包装（不推荐，破坏封装）
```python
# views.py
from asgiref.sync import sync_to_async

variables = await sync_to_async(GlobalVariable.get_variables_for_user)(
    user=request.user,
    include_system=include_system
)
```

**工作量**: 10分钟

---

### 🟢 低优先级 - 无ORM调用

#### 3. apps/projects/consumers.py

**分析**: 所有异步函数都是WebSocket消费者，只使用Redis Pub/Sub

**ORM调用**: ❌ 无

**结论**: ✅ 不需要修改

---

#### 4. apps/content/

**扫描结果**: 没有异步函数

**结论**: ✅ 不需要修改

---

#### 5. apps/users/

**扫描结果**: 没有异步函数

**结论**: ✅ 不需要修改

---

## 📊 修复优先级

| 文件 | 优先级 | 状态 | 工作量 | 风险 |
|------|--------|------|--------|------|
| `apps/prompts/services.py` | 🔴 高 | ❌ 需修复 | 5分钟 | 低（简单替换） |
| `apps/prompts/models.py` | 🔴 高 | ❌ 需修复 | 10分钟 | 中（需测试迭代） |
| `apps/projects/consumers.py` | 🟢 低 | ✅ 无需修复 | - | - |
| `apps/content/*` | 🟢 低 | ✅ 无需修复 | - | - |
| `apps/users/*` | 🟢 低 | ✅ 无需修复 | - | - |

**总工作量**: 15分钟

---

## 🎯 修复策略

### Phase 1: 修复services.py（5分钟）

1. 导入 `sync_to_async_wrapper`
2. 替换 `.afirst()` 为包装后的 `.first()`
3. 测试验证

### Phase 2: 修复models.py（10分钟）

1. 将 `get_variables_for_user` 改为异步方法
2. 使用 `sync_to_async` 包装ORM查询
3. 测试视图调用

---

## ✅ 验证计划

修复后执行以下测试：

1. **单元测试**:
   ```bash
   uv run pytest apps/prompts/tests/test_services.py -v
   uv run pytest apps/prompts/tests/test_views.py -v
   ```

2. **集成测试**:
   ```bash
   # 测试提示词评估功能
   curl -X POST http://localhost:8000/api/v1/prompts/templates/{id}/evaluate/
   ```

3. **性能测试**:
   - 对比修复前后的响应时间
   - 确保没有性能退化

---

## 📝 技术要点

### Django 3.2 vs Django 4.1+ 异步ORM

| 特性 | Django 3.2 | Django 4.1+ |
|------|-----------|-------------|
| `.aget()` | ❌ 不支持 | ✅ 支持 |
| `.afirst()` | ❌ 不支持 | ✅ 支持 |
| `.acreate()` | ❌ 不支持 | ✅ 支持 |
| `async for` | ❌ 不支持 | ✅ 支持 |
| `sync_to_async` | ✅ 支持 | ✅ 支持 |

**结论**: 在Django 3.2中，必须使用 `sync_to_async` 包装同步ORM

---

## 🎉 预期成果

修复完成后：
- ✅ 所有异步函数可正常运行
- ✅ ORM调用正确包装
- ✅ 提示词评估功能可用
- ✅ 全局变量查询功能可用
- ✅ 无性能退化

---

**报告生成时间**: 2026-01-28
**下一步**: 开始Phase 1修复
**预计完成时间**: 15分钟
