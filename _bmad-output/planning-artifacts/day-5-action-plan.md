# Day 5行动计划

**日期:** 2026-01-28
**阶段:** Phase 1 - P0 MVP验证
**目标:** 提升测试覆盖率至40-45%，启动WebSocket测试

---

## 📋 任务清单

### 优先级P0 (核心任务)

#### 任务19: 继续Story 1.4 - Redis Pub/Sub测试 ⏰ 45分钟

**目标:** 提升Redis模块覆盖率

**子任务:**
1. ✅ 创建 `tests/test_redis_publisher.py` (20分钟)
   - 测试发布token
   - 测试发布stage update
   - 测试发布error
   - Mock Redis客户端

2. ✅ 修复 `tests/test_core_redis.py` 失败测试 (15分钟)
   - `test_get_message_with_data` Mock配置修复
   - 或者标记为已知问题并跳过

3. ✅ 运行测试并验证覆盖率 (10分钟)

**预期成果:**
- 覆盖率: core/redis/ → 51% → 70%
- 测试数: +5-8个

---

#### 任务20: 继续Story 1.4 - AI客户端单元测试 ⏰ 60分钟

**目标:** 提升AI客户端模块覆盖率

**子任务:**
1. ✅ 创建 `tests/test_ai_client_base.py` (30分钟)
   - 测试LLMClient抽象方法
   - 测试Text2ImageClient抽象方法
   - 测试Image2VideoClient抽象方法
   - 测试AIResponse数据类

2. ✅ 创建 `tests/test_ai_client_factory.py` (30分钟)
   - 测试get_executor_class()
   - 测试create_ai_client()各种路径
   - 测试默认executor回退逻辑

**预期成果:**
- 覆盖率: core/ai_client/ → 平均50% → 70%
- 测试数: +10-15个

---

#### 任务21: 启动Story 3.1 - WebSocket连接测试 ⏰ 90分钟

**目标:** 验证WebSocket实时通信稳定性

**子任务:**
1. ✅ 创建 `tests/test_websocket_consumers.py` (45分钟)
   - Mock WebSocket连接
   - 测试ProjectConsumer连接/断开
   - 测试频道订阅
   - 测试消息接收

2. ✅ 创建 `tests/test_websocket_routing.py` (30分钟)
   - 测试路由配置
   - 验证URL pattern匹配

3. ✅ 集成测试：Redis → WebSocket (15分钟)
   - 测试Redis消息推送至WebSocket

**预期成果:**
- 覆盖率: apps/projects/consumers.py → 0% → 60%
- 测试数: +8-12个
- Epic 3进度: 0% → 30%

---

#### 任务22: 编写集成测试 - 项目创建流程 ⏰ 60分钟

**目标:** 测试完整业务流程

**子任务:**
1. ✅ 创建 `tests/integration/test_project_creation_flow.py` (60分钟)
   - POST /api/v1/projects/ (创建项目)
   - 验证Project记录创建
   - 验证ProjectStage记录创建（5个阶段）
   - 验证Celery任务触发（可选，或使用mock）

**预期成果:**
- 集成测试: +3-5个
- 端到端验证: 项目创建流程

---

### 优先级P1 (次要任务)

#### 任务23: 更新文档 ⏰ 30分钟

**文档更新:**
1. ✅ 更新各模块CLAUDE.md中的测试覆盖状态
2. ✅ 更新backend/README.md测试章节
3. ✅ 记录已知问题和限制

---

## 🎯 成功标准

### Day 5结束时应达成

| 指标 | Day 4 | Day 5目标 | 改进 |
|------|-------|-----------|------|
| **测试通过率** | 99.2% (123/124) | >98% | 保持 |
| **代码覆盖率** | 34% | **40-45%** | +6-11% |
| **新增测试** | 124 | 145-160 | +21-36 |
| **Epic 1进度** | 70% | 85% | +15% |
| **Epic 3进度** | 0% | 30% | +30% |

### 关键里程碑

- ✅ **Story 1.4完成** - 核心模块测试覆盖率>70%
- ✅ **Story 3.1启动** - WebSocket测试基础建立
- ✅ **集成测试** - 至少1个完整业务流程测试

---

## 📊 覆盖率提升预测

### 当前高价值低覆盖模块

| 模块 | 当前覆盖 | 目标覆盖 | 优先级 |
|------|----------|----------|--------|
| `core/redis/subscriber.py` | 51% | 75% | P0 |
| `core/ai_client/base.py` | 73% | 85% | P0 |
| `core/ai_client/factory.py` | 70% | 85% | P0 |
| `apps/projects/consumers.py` | 0% | 60% | P0 |
| `apps/projects/tasks.py` | 0% | 50% | P1 |

### 预期覆盖率提升

```
总体覆盖率预测:
Day 4: 34% (3059/4642行)
Day 5: 41-45% (1900-2100/4642行)
提升: +7-11个百分点
```

---

## 🔧 技术实施策略

### 测试优先级排序

**高价值测试（优先执行）:**
1. ✅ Redis Publisher - 核心基础设施
2. ✅ AI Client Factory - 工厂模式关键路径
3. ✅ WebSocket Consumers - Epic 3核心
4. ✅ 集成测试 - 端到端验证

**中价值测试（按需执行）:**
1. Redis Subscriber - 已有基础测试
2. AI Client Base - 抽象类测试价值有限
3. Celery Tasks - 需要复杂Mock，可延后

**低价值测试（最后执行）:**
1. 工具函数（utils/）
2. 数据模型方法（models.py）
3. Admin配置

### Mock策略

**Redis Mock:**
```python
@patch('core.redis.publisher.redis')
def test_publish_token(self, mock_redis):
    mock_client = MagicMock()
    mock_redis.from_url.return_value = mock_client
    # 测试逻辑
```

**WebSocket Mock:**
```python
@pytest.mark.asyncio
@patch('apps.projects.consumers.ChannelLayer')
async def test_consumer_connect(self, mock_channel_layer):
    communicator = WebsocketCommunicator(
        ProjectConsumer.as_asgi(),
        '/ws/projects/test-id/'
    )
    connected, _ = await communicator.connect()
    assert connected is True
```

**Celery Task Mock:**
```python
@patch('apps.projects.tasks.execute_llm_stage.delay')
def test_start_triggers_celery(self, mock_delay):
    mock_delay.return_value = MagicMock(task_id='test-id')
    # 测试逻辑
```

---

## ⚠️ 风险与应对

### 风险1: WebSocket测试配置复杂

**风险等级:** 🟡 中等

**应对方案:**
- 使用channels.testing.WebsocketCommunicator
- Mock Redis Pub/Sub避免依赖真实Redis
- 分离单元测试和集成测试

### 风险2: Celery任务难以测试

**风险等级:** 🟡 中等

**应对方案:**
- Mock task.delay()返回值
- 验证任务被调用而非执行结果
- 使用CELERY_TASK_ALWAYS_EAGER配置（开发模式）

### 风险3: 覆盖率提升不如预期

**风险等级:** 🟢 低

**应对方案:**
- 优先测试核心业务逻辑
- 跳过工具函数和配置代码
- 接受35-40%覆盖率（仍比Day 4好）

---

## 📝 执行顺序

### 上午 (3小时)

1. **09:00-09:45** 任务19: Redis Pub/Sub测试
2. **09:45-10:45** 任务20: AI客户端单元测试
3. **10:45-11:00** ☕ 休息
4. **11:00-12:00** 任务21第1部分: WebSocket消费者测试

### 下午 (2小时)

5. **13:00-13:30** 任务21第2部分: WebSocket路由测试
6. **13:30-14:30** 任务22: 集成测试
7. **14:30-15:00** 任务23: 更新文档

### 晚上 (可选)

8. **15:00-15:30** 运行完整测试套件
9. **15:30-16:00** 生成覆盖率报告
10. **16:00-16:30** 创建Day 5执行总结

---

## 🚀 下一步预告

### Day 6方向（如果需要）

**选项A: 继续测试**
- 完成Celery任务测试
- 添加更多集成测试
- 目标覆盖率50%+

**选项B: 开始功能开发**
- 实现真实AI客户端集成
- 完善WebSocket实时推送
- 实现剪映草稿生成

**决策依据:**
- 如果Day 5达到40%覆盖率 → 切换到功能开发
- 如果Day 5未达到35% → 继续测试

---

## 📈 成功指标追踪

### 实时检查点

**10:00 (任务19完成):**
- [ ] test_redis_publisher.py创建
- [ ] Redis publisher测试通过
- [ ] core/redis/覆盖率提升至65%+

**11:00 (任务20完成):**
- [ ] test_ai_client_base.py创建
- [ ] test_ai_client_factory.py创建
- [ ] core/ai_client/覆盖率提升至65%+

**12:00 (任务21第1部分完成):**
- [ ] test_websocket_consumers.py创建
- [ ] WebSocket消费者测试通过
- [ ] consumers.py覆盖率达到50%+

**14:30 (任务22完成):**
- [ ] test_project_creation_flow.py创建
- [ ] 集成测试通过
- [ ] 至少验证1个完整流程

**15:30 (全部完成):**
- [ ] 完整测试套件运行成功
- [ ] 覆盖率达到40-45%
- [ ] 文档更新完成

---

## 💡 提示与最佳实践

### 测试编写技巧

1. **测试命名规范**
   ```python
   def test_<action>_<condition>_<expected_result>():
   # 例: test_create_project_with_valid_data_returns_201()
   ```

2. **AAA模式 (Arrange-Act-Assert)**
   ```python
   def test_update_project_name():
       # Arrange: 准备测试数据
       project = Project.objects.create(name='旧名称')
       new_name = '新名称'

       # Act: 执行被测试的操作
       response = client.patch(f'/api/projects/{project.id}/',
                              {'name': new_name})

       # Assert: 验证结果
       assert response.status_code == 200
       assert response.data['name'] == new_name
   ```

3. **Mock最小化原则**
   - 只Mock外部依赖（Redis、HTTP API）
   - 不要Mock被测试的代码
   - 优先使用真实数据库（@pytest.mark.django_db）

4. **测试独立性**
   - 每个测试应该独立运行
   - 使用fixtures创建测试数据
   - 清理副作用（数据库回滚）

---

**创建时间:** 2026-01-27 10:42 UTC
**预计执行:** 2026-01-28
**预计用时:** 5小时
**预期成果:** 覆盖率40-45%，Epic 3启动

*准备就绪，等待执行! 🚀*
