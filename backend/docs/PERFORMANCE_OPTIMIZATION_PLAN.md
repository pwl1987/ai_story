# 性能优化方案 - 并行处理实施指南

**版本**: 1.0
**更新时间**: 2026-01-28
**状态**: 📋 方案阶段
**预期收益**: 30-50%性能提升

---

## 📊 当前性能分析

### 基准测试结果（来源: FINAL_ALL_TASKS_REPORT.md）

```
总执行时间: 10.91秒
平均每阶段: 2.18秒
```

### 阶段耗时分布（估算）

| 阶段 | 耗时 | 占比 | 并行化潜力 |
|------|------|------|-----------|
| Rewrite | ~1.5s | 13.8% | ❌ 低（单次LLM调用）|
| Storyboard | ~2.0s | 18.3% | ❌ 低（单次LLM调用）|
| **Image Generation** | **~3.0s** | **27.5%** | **✅ 高（多场景独立）** |
| **Camera Movement** | **~2.5s** | **22.9%** | **✅ 高（多场景独立）** |
| Video Generation | ~1.9s | 17.4% | ❌ 中（依赖图片）|

**关键发现**: Image Generation和Camera Movement阶段具有显著的并行化潜力！

---

## 🎯 并行优化策略

### 策略1: Image Generation并行处理 ⭐⭐⭐⭐⭐

**当前实现** (串行):
```python
# apps/projects/pipeline_adapters.py:ImageGenerationStageAdapter

for chunk in self.processor.process_stream(project_id=project.id):
    # 逐个处理场景
    if chunk_type == 'image_generated':
        images.append(chunk.get('image_url'))
```

**优化后** (并行):
```python
import asyncio

async def process(self, context: PipelineContext) -> StageResult:
    """并行执行文生图"""
    project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

    # 获取storyboard数据
    storyboard_result = context.get_result('storyboard')
    scenes = storyboard_result.get('storyboard', [])

    # 并行处理每个场景
    tasks = [
        self._generate_scene_image(scene['index'], scene['image_prompt'])
        for scene in scenes
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    images = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"场景图片生成失败: {result}")
        else:
            images.append(result)

    return StageResult(success=True, data={'images': images})

async def _generate_scene_image(self, scene_index, prompt):
    """生成单个场景的图片"""
    # 调用AI客户端生成图片
    client = await self._get_ai_client()
    response = await client.generate(prompt=prompt, width=1024, height=1024)

    if response.success:
        return response.data.get('image_url')
    else:
        raise Exception(response.error)
```

**预期收益**:
- 假设3个场景，串行需要3.0秒
- 并行后只需要 ~1.0秒
- **性能提升: 66%** ✅

---

### 策略2: Camera Movement并行处理 ⭐⭐⭐⭐⭐

**当前实现** (串行):
```python
# apps/projects/pipeline_adapters.py:CameraMovementStageAdapter

for chunk in self.processor.process_stream(project_id=project.id):
    # 逐个处理场景
```

**优化后** (并行):
```python
async def process(self, context: PipelineContext) -> StageResult:
    """并行执行运镜生成"""
    project = await sync_to_async_wrapper(Project.objects.get)(id=context.project_id)

    # 获取storyboard数据
    storyboard_result = context.get_result('storyboard')
    scenes = storyboard_result.get('storyboard', [])

    # 并行处理每个场景的运镜
    tasks = [
        self._generate_camera_movement(scene['index'], scene['scene_description'])
        for scene in scenes
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    camera_movements = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"场景运镜生成失败: {result}")
        else:
            camera_movements.append(result)

    return StageResult(success=True, data={'camera_movements': camera_movements})

async def _generate_camera_movement(self, scene_index, description):
    """生成单个场景的运镜"""
    # 调用LLM客户端生成运镜参数
    client = await self._get_ai_client()

    prompt = f"""
    根据以下场景描述生成运镜参数:
    {description}

    返回JSON格式:
    {{
      "movement_type": "slow_zoom_in",
      "movement_params": {{
        "start_scale": 1.0,
        "end_scale": 1.2,
        "duration": 3.0
      }}
    }}
    """

    response = await client.generate(prompt=prompt, max_tokens=500)

    if response.success:
        import json
        movement_data = json.loads(response.text)
        return {
            'scene_index': scene_index,
            'movement_type': movement_data['movement_type'],
            'movement_params': movement_data['movement_params']
        }
    else:
        raise Exception(response.error)
```

**预期收益**:
- 假设3个场景，串行需要2.5秒
- 并行后只需要 ~0.9秒
- **性能提升: 64%** ✅

---

### 策略3: 批量API调用（可选） ⭐⭐⭐☆☆

**说明**: 某些AI服务提供商支持批量API调用

**示例** (Stable Diffusion批量生成):
```python
async def _generate_batch_images(self, prompts: List[str]) -> List[str]:
    """批量生成图片"""
    client = await self._get_ai_client()

    # 如果支持批量API
    if hasattr(client, 'generate_batch'):
        response = await client.generate_batch(
            prompts=prompts,
            width=1024,
            height=1024
        )
        return response.data.get('image_urls', [])
    else:
        # 退回到并行调用
        tasks = [client.generate(prompt=p) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return [r.data.get('image_url') for r in results]
```

**预期收益**: 额外10-20%性能提升

---

## 📈 综合性能预期

### 优化前

```
总时间: 10.91秒
- Image Generation: 3.0s (27.5%)
- Camera Movement: 2.5s (22.9%)
其他: 5.41s (49.6%)
```

### 优化后（策略1+2）

```
总时间: ~7.0秒  (36%提升)
- Image Generation: 1.0s (14.3%) ⬇️ 66%
- Camera Movement: 0.9s (12.9%) ⬇️ 64%
其他: 5.1s (72.8%)
```

### 优化后（策略1+2+3）

```
总时间: ~6.3秒  (42%提升)
- Image Generation: 0.8s (12.7%)
- Camera Movement: 0.7s (11.1%)
其他: 4.8s (76.2%)
```

---

## 🔧 实施步骤

### Phase 1: Image Generation并行（优先级最高）

**工作量**: 3-4小时

**步骤**:
1. 修改`ImageGenerationStageAdapter.process()`方法
2. 添加`_generate_scene_image()`辅助方法
3. 使用`asyncio.gather()`并行处理
4. 添加错误处理和重试逻辑
5. 更新单元测试

**文件修改**:
- `apps/projects/pipeline_adapters.py` - ImageGenerationStageAdapter

**测试**:
- `apps/projects/tests/test_pipeline_adapters.py`
- 性能基准测试对比

---

### Phase 2: Camera Movement并行（优先级高）

**工作量**: 2-3小时

**步骤**:
1. 修改`CameraMovementStageAdapter.process()`方法
2. 添加`_generate_camera_movement()`辅助方法
3. 使用`asyncio.gather()`并行处理
4. 添加错误处理
5. 更新单元测试

**文件修改**:
- `apps/projects/pipeline_adapters.py` - CameraMovementStageAdapter

---

### Phase 3: 批量API支持（可选）

**工作量**: 2-3小时

**步骤**:
1. 检查AI服务提供商是否支持批量API
2. 在BaseAIClient中添加`generate_batch()`接口
3. 在具体客户端中实现批量方法
4. 更新factory逻辑

**文件修改**:
- `core/ai_client/base.py`
- `core/ai_client/text2image_client.py`

---

## ⚠️ 注意事项

### 1. 并发限制

**问题**: AI服务提供商可能有并发限制

**解决方案**:
```python
import asyncio

async def _generate_with_limit(tasks, limit=5):
    """限制并发数量"""
    semaphore = asyncio.Semaphore(limit)

    async def bounded_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*[bounded_task(t) for t in tasks])
```

**配置**:
```python
# settings.py
AI_CONCURRENT_LIMIT = 5  # 同时最多5个并发请求
```

---

### 2. 错误处理

**问题**: 并行任务中部分失败

**解决方案**:
```python
results = await asyncio.gather(*tasks, return_exceptions=True)

successful = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]

logger.warning(f"并行处理完成: {len(successful)}成功, {len(failed)}失败")

if failed:
    # 重试失败的任务
    ...
```

---

### 3. 资源管理

**问题**: 大量并发可能导致内存/连接问题

**解决方案**:
```python
async def _generate_scene_image(self, scene_index, prompt):
    """生成单个场景的图片（带资源管理）"""
    async with self._client_semaphore:  # 限制并发
        try:
            client = self._get_client()
            response = await client.generate(prompt=prompt)
            return response.data.get('image_url')
        finally:
            # 确保资源释放
            await self._release_client(client)
```

---

## 📊 测试计划

### 性能对比测试

```python
import time

async def benchmark_parallel():
    """性能基准测试"""
    projects = [create_test_project() for _ in range(10)]

    # 测试串行版本
    start = time.time()
    for project in projects:
        await execute_image_generation_serial(project)
    serial_time = time.time() - start

    # 测试并行版本
    start = time.time()
    for project in projects:
        await execute_image_generation_parallel(project)
    parallel_time = time.time() - start

    print(f"串行: {serial_time:.2f}s")
    print(f"并行: {parallel_time:.2f}s")
    print(f"提升: {(1 - parallel_time/serial_time) * 100:.1f}%")
```

**预期结果**:
```
串行: 30.0s
并行: 10.5s
提升: 65.0% ✅
```

---

## 🎯 验收标准

- [ ] Image Generation并行实现完成
- [ ] Camera Movement并行实现完成
- [ ] 性能提升 ≥ 30%
- [ ] 单元测试通过
- [ ] 错误处理完善
- [ ] 并发限制配置

---

## 📚 参考资料

- [Python asyncio.gather文档](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)
- [Django异步ORM最佳实践](https://docs.djangoproject.com/en/3.2/topics/async/)
- [AI服务提供商并发限制文档](https://platform.openai.com/docs/guides/rate-limits)

---

**方案制定时间**: 2026-01-28
**预估工作量**: 5-8小时
**预期收益**: 30-50%性能提升
**维护者**: AI Story Backend Team
