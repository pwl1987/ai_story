# Mock环境配置指南

> **文档版本**: 1.0
> **更新日期**: 2026-01-28
> **适用场景**: 开发测试、端到端验证

---

## 目录

- [概述](#概述)
- [Mock Providers](#mock-providers)
- [配置步骤](#配置步骤)
- [使用Mock环境](#使用mock环境)
- [验证测试](#验证测试)
- [常见问题](#常见问题)
- [故障排查](#故障排查)

---

## 概述

Mock环境用于开发测试，避免调用真实AI API，具有以下优势：

1. **成本控制** - 不产生API调用费用
2. **快速反馈** - 无需等待真实API响应
3. **离线开发** - 无需网络连接
4. **可预测性** - 返回固定的模拟响应

---

## Mock Providers

系统提供3种类型的Mock Provider：

### 1. Mock LLM Client

**用途**: 模拟文案改写、分镜生成、运镜生成

```
名称: Mock LLM for E2E Test
类型: llm
执行器: core.ai_client.mock_llm_client.MockLLMClient
API URL: mock://localhost
```

**模拟响应**:
- **文案改写**: 返回固定的改写文本（约200字）
- **分镜生成**: 返回JSON格式的3个场景分镜
- **运镜生成**: 返回JSON格式的运镜参数

### 2. Mock Text2Image Client

**用途**: 模拟文生图生成

```
名称: Mock Text2Image for E2E Test
类型: text2image
执行器: core.ai_client.mock_text2image_client.MockText2ImageClient
API URL: mock://localhost
```

**模拟响应**:
- 返回固定的图片URL（占位符）
- 模拟处理延迟（0.5秒）

### 3. Mock Image2Video Client

**用途**: 模拟图生视频生成

```
名称: Mock Image2Video for E2E Test
类型: image2video
执行器: core.ai_client.mock_image2video_client.MockImage2VideoClient
API URL: mock://localhost
```

**模拟响应**:
- 返回固定的视频URL（占位符）
- 模拟处理延迟（1.0秒）

---

## 配置步骤

### 方法1: 自动配置（推荐）

使用自动化脚本一键配置：

```bash
cd backend
uv run python scripts/setup_mock_env.py
uv run python scripts/create_test_project.py
```

**输出**:
```
============================================================
Mock环境配置
============================================================
✓ 创建 Mock LLM Provider: Mock LLM for E2E Test
✓ 创建 Mock Text2Image Provider: Mock Text2Image for E2E Test
✓ 创建 Mock Image2Video Provider: Mock Image2Video for E2E Test

============================================================
✓ Mock环境配置完成
============================================================
```

### 方法2: 手动配置

#### Step 1: 创建Mock LLM Provider

```python
from apps.models.models import ModelProvider

mock_llm = ModelProvider.objects.create(
    name='Mock LLM for E2E Test',
    provider_type='llm',
    executor_class='core.ai_client.mock_llm_client.MockLLMClient',
    api_url='mock://localhost',
    api_key='',
    model_name='mock-llm',
    max_tokens=2000,
    temperature=0.7,
    is_active=True,
    priority=10
)
```

#### Step 2: 创建Mock Text2Image Provider

```python
mock_t2i = ModelProvider.objects.create(
    name='Mock Text2Image for E2E Test',
    provider_type='text2image',
    executor_class='core.ai_client.mock_text2image_client.MockText2ImageClient',
    api_url='mock://localhost',
    api_key='',
    model_name='mock-t2i',
    is_active=True,
    priority=10
)
```

#### Step 3: 创建Mock Image2Video Provider

```python
mock_i2v = ModelProvider.objects.create(
    name='Mock Image2Video for E2E Test',
    provider_type='image2video',
    executor_class='core.ai_client.mock_image2video_client.MockImage2VideoClient',
    api_url='mock://localhost',
    api_key='',
    model_name='mock-i2v',
    is_active=True,
    priority=10
)
```

---

## 使用Mock环境

### 创建测试项目

```python
from apps.projects.models import Project, ProjectModelConfig
from apps.prompts.models import PromptTemplateSet, PromptTemplate
from apps.models.models import ModelProvider
from django.contrib.auth import get_user_model

User = get_user_model()

# 1. 创建用户
user, _ = User.objects.get_or_create(
    username='test_user',
    defaults={'email': 'test@example.com'}
)

# 2. 创建PromptTemplateSet
prompt_set = PromptTemplateSet.objects.create(
    name='Test Prompt Set',
    created_by=user
)

# 3. 创建提示词模板
for stage in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
    PromptTemplate.objects.create(
        template_set=prompt_set,
        stage_type=stage,
        template_content=f'Test template for {{{{ raw_text }}}}',
        is_active=True
    )

# 4. 获取Mock Providers
mock_llm = ModelProvider.objects.get(name='Mock LLM for E2E Test')
mock_t2i = ModelProvider.objects.get(name='Mock Text2Image for E2E Test')
mock_i2v = ModelProvider.objects.get(name='Mock Image2Video for E2E Test')

# 5. 创建项目
project = Project.objects.create(
    name='Mock Test Project',
    original_topic='宁静的小镇，年轻的画家',
    user=user,
    prompt_template_set=prompt_set,
    status='draft'
)

# 6. 配置模型
config = ProjectModelConfig.objects.create(project=project)
config.rewrite_providers.add(mock_llm)
config.storyboard_providers.add(mock_llm)
config.camera_providers.add(mock_llm)
config.image_providers.add(mock_t2i)
config.video_providers.add(mock_i2v)
```

### 执行工作流

#### API方式

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/execute_full_pipeline/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json"
```

**响应**:
```json
{
  "task_id": "xxx-xxx-xxx",
  "channel": "ai_story:project:xxx:pipeline",
  "message": "完整工作流已启动",
  "project_id": "xxx"
}
```

#### Python方式

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {token}"}

# 启动工作流
response = requests.post(
    f"{BASE_URL}/projects/{project_id}/execute_full_pipeline/",
    headers=headers
)

task_id = response.json()['task_id']
```

---

## 验证测试

### 检查Mock Providers

```bash
cd backend
uv run python manage.py shell
```

```python
from apps.models.models import ModelProvider

# 列出所有Mock Providers
mock_providers = ModelProvider.objects.filter(
    name__contains='Mock'
)

for provider in mock_providers:
    print(f"{provider.name} ({provider.provider_type})")
    print(f"  执行器: {provider.executor_class}")
    print(f"  状态: {'激活' if provider.is_active else '未激活'}")
    print()
```

### 运行端到端测试

```bash
cd backend
uv run python scripts/test_e2e_workflow.py
```

**预期输出**:
```
============================================================
端到端工作流测试
============================================================

1. 获取认证token...
✓ 登录成功

2. 获取测试项目...
✓ 找到测试项目: E2E Test Project

3. 启动工作流...
✓ 工作流已启动

4. 监控工作流进度...
  进度: [██████████] 5/5 | 状态: completed

✓ 工作流完成！

============================================================
✓ 端到端测试通过
============================================================
```

---

## 常见问题

### Q1: Mock响应不符合预期？

**A**: 检查Mock客户端的MOCK_RESPONSES配置

```python
# core/ai_client/mock_llm_client.py
class MockLLMClient(LLMClient):
    MOCK_RESPONSES = {
        "rewrite": "...",
        "storyboard": "...",
        "camera_movement": "...",
    }
```

修改这些响应模板即可自定义Mock输出。

### Q2: 如何模拟API失败？

**A**: 在Mock客户端中添加错误逻辑

```python
# core/ai_client/mock_llm_client.py
async def _generate_text(self, prompt, **kwargs):
    # 模拟失败
    if "error" in prompt.lower():
        raise Exception("模拟的API错误")

    # 正常返回
    return AIResponse(success=True, text="...")
```

### Q3: 切换到真实API？

**A**: 修改ModelProvider配置

```python
# 1. 停用Mock Provider
mock_llm.is_active = False
mock_llm.save()

# 2. 启用真实Provider
real_llm = ModelProvider.objects.get(name='GPT-4')
real_llm.is_active = True
real_llm.save()

# 3. 更新项目配置
config.rewrite_providers.clear()
config.rewrite_providers.add(real_llm)
```

### Q4: Mock响应太慢？

**A**: 减少模拟延迟

```python
# core/ai_client/mock_llm_client.py
async def _generate_text(self, prompt, **kwargs):
    # 减少延迟
    time.sleep(0.1)  # 原来是0.5秒

    # ...
```

---

## 故障排查

### 问题1: Provider未找到

**错误**: `ModelProvider matching query does not exist`

**原因**: Mock Provider未创建或名称不匹配

**解决**:
```bash
# 重新运行配置脚本
uv run python scripts/setup_mock_env.py

# 检查Provider是否存在
uv run python manage.py shell
>>> from apps.models.models import ModelProvider
>>> ModelProvider.objects.filter(name__contains='Mock').count()
# 应该返回3
```

### 问题2: 工作流卡在processing状态

**原因**: Celery Worker未运行或连接失败

**解决**:
```bash
# 检查Celery Worker
ps aux | grep celery

# 检查Redis
docker ps | grep redis
redis-cli ping  # 应返回PONG

# 重启Celery Worker
uv run celery -A config worker -Q llm,image,video -l info
```

### 问题3: 项目状态始终为draft

**原因**: execute_full_pipeline任务未触发

**解决**:
```bash
# 检查Django日志
tail -f logs/django.log

# 检查Celery任务
redis-cli -n 0
> LLEN celery  # 查看队列长度
> LRANGE celery 0 -1  # 查看任务
```

### 问题4: WebSocket连接失败

**原因**: ASGI服务器未运行或Redis配置错误

**解决**:
```bash
# 1. 确认ASGI服务器运行
ps aux | grep daphne

# 2. 检查Redis Channels配置
# config/settings/base.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}

# 3. 重启ASGI服务器
./run_asgi.sh
```

---

## 验收清单

使用Mock环境进行端到端测试前，请确认：

- [ ] 3个Mock ModelProvider已创建
- [ ] PromptTemplateSet和5个PromptTemplate已创建
- [ ] 测试项目已创建并关联Mock配置
- [ ] Redis运行中（`docker ps | grep redis`）
- [ ] Celery Worker运行中（`ps aux | grep celery`）
- [ ] Django ASGI运行中（`ps aux | grep daphne`）
- [ ] execute_full_pipeline API可访问（curl测试）
- [ ] WebSocket可连接（ws://localhost:8000/ws/projects/{id}/）

---

## 相关文档

- [Celery+Redis流式架构](../../CELERY_REDIS_STREAMING.md)
- [测试脚本使用指南](../../scripts/README.md)
- [项目管理域文档](../../apps/projects/CLAUDE.md)
- [AI客户端模块文档](../../core/ai_client/CLAUDE.md)

---

## 变更记录

### 2026-01-28
- 初始化Mock环境配置文档
- 添加3个Mock Provider说明
- 添加自动/手动配置步骤
- 添加故障排查指南
