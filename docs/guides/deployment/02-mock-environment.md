# Mock环境配置指南

> Mock环境用于开发测试，避免调用真实AI API

---

## Mock环境概述

Mock环境提供3个Mock客户端：
- **Mock LLM Client** - 模拟文本生成
- **Mock Text2Image Client** - 模拟文生图
- **Mock Image2Video Client** - 模拟图生视频

---

## 快速配置

### 自动配置（推荐）

```bash
cd backend

# 运行Mock环境配置脚本
uv run python scripts/setup_mock_env.py

# 创建测试项目
uv run python scripts/create_test_project.py
```

### 手动配置

#### 1. 创建Mock Providers

```python
from apps.models.models import ModelProvider

# Mock LLM
mock_llm = ModelProvider.objects.create(
    name='Mock LLM',
    provider_type='llm',
    executor_class='core.ai_client.mock_llm_client.MockLLMClient',
    api_url='http://localhost:8000/api/mock/llm/',
    is_active=True
)

# Mock Text2Image
mock_t2i = ModelProvider.objects.create(
    name='Mock Text2Image',
    provider_type='text2image',
    executor_class='core.ai_client.mock_text2image_client.MockText2ImageClient',
    is_active=True
)

# Mock Image2Video
mock_i2v = ModelProvider.objects.create(
    name='Mock Image2Video',
    provider_type='image2video',
    executor_class='core.ai_client.mock_image2video_client.MockImage2VideoClient',
    is_active=True
)
```

#### 2. 创建项目并关联Mock配置

```python
from apps.projects.models import Project, ProjectModelConfig

project = Project.objects.create(
    name='Mock测试项目',
    original_topic='宁静的小镇'
)

# 配置模型
config = ProjectModelConfig.objects.create(project=project)
config.rewrite_providers.add(mock_llm)
config.storyboard_providers.add(mock_llm)
config.image_providers.add(mock_t2i)
config.video_providers.add(mock_i2v)
```

---

## Mock响应格式

### Mock LLM响应

```json
{
  "success": true,
  "text": "这是模拟的LLM响应...",
  "metadata": {
    "tokens_used": 33,
    "latency_ms": 500,
    "is_mock": true
  }
}
```

### Mock Text2Image响应

```json
{
  "success": true,
  "data": {
    "urls": ["https://picsum.photos/1024/1024"],
    "images": [
      {
        "url": "https://picsum.photos/1024/1024",
        "width": 1024,
        "height": 1024
      }
    ]
  }
}
```

### Mock Image2Video响应

```json
{
  "success": true,
  "data": {
    "video_url": "https://example.com/mock-video.mp4",
    "duration": 5
  }
}
```

---

## 测试Mock环境

### 端到端测试

```bash
cd backend

# 运行端到端测试
uv run python scripts/test_e2e_api.py
```

### 单元测试

```bash
cd backend

# 运行Mock客户端测试
uv run pytest tests/test_mock_clients.py -v
```

---

## 切换到真实API

```python
# 修改ModelProvider配置
provider = ModelProvider.objects.get(name='Mock LLM')
provider.executor_class = 'core.ai_client.openai_client.OpenAIClient'
provider.api_url = 'https://api.openai.com/v1'
provider.api_key = 'sk-xxx'  # 真实API Key
provider.model_name = 'gpt-4'
provider.save()
```

---

## 常见问题

### Q: Mock响应不符合预期？

A: 检查`core/ai_client/mock_*.py`中的响应配置

### Q: 如何模拟API失败？

A: 在Mock客户端中添加错误逻辑，或设置无效配置

### Q: Mock响应速度太快？

A: 在Mock客户端中添加延迟：
```python
import asyncio
await asyncio.sleep(1)  # 模拟网络延迟
```

---

## 下一步

- [快速启动指南](./01-quick-start.md)
- [故障排查](../troubleshooting/01-common-issues.md)
