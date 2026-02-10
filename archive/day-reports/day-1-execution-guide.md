---
project: AI Story Generation System
documentType: Phase 1 Execution Guide
version: 1.0
created: 2026-01-27
phase: Phase 1 - Day 1 Execution Guide
status: Ready for Execution
---

# AI Story - Phase 1 Day 1 执行指南

**目标:** 按照推荐方案A,并行启动3个Epic的第一天任务

**前提条件:**
- ✅ 项目规划文档完整
- ✅ 实施计划明确
- ⚠️ 需要在有Python/Django开发环境中执行

---

## 🚀 立即开始 (4个关键任务)

### 任务1: 验证pytest测试框架 (15分钟)

**目标:** 确保pytest测试框架可用

**执行步骤:**

```bash
# 1. 进入backend目录
cd /home/code/ai_story/backend

# 2. 检查pytest是否已安装
python3 -m pytest --version

# 如果未安装,安装依赖:
# 使用uv (如果已安装):
uv sync

# 或使用pip (如果uv不可用):
python3 -m pip install pytest pytest-django pytest-cov

# 3. 验证pytest配置
cat pytest.ini

# 4. 运行测试验证脚本
chmod +x verify_pytest.sh
./verify_pytest.sh

# 5. 预期结果:
# - pytest版本>=8.0.0
# - 所有配置文件存在
# - 测试框架可用
```

**验收标准:**
- ✅ pytest命令可正常运行
- ✅ pytest.ini配置正确加载
- ✅ tests/目录下的测试可被发现
- ✅ 覆盖率报告可生成

**故障排查:**
```bash
# 问题1: pytest未安装
解决: python3 -m pip install pytest pytest-django pytest-cov

# 问题2: Django配置错误
解决: 确保 DJANGO_SETTINGS_MODULE=config.settings.development

# 问题3: 数据库未初始化
解决: python3 manage.py migrate
```

---

### 任务2: Story 1.3 - 实现Mock AI客户端 (2-3小时)

**目标:** 实现Mock LLM/Image/Video客户端,支持离线测试

**文件位置:** `/home/code/ai_story/backend/core/ai_client/`

**步骤1: 查看现有基类**

```bash
cd /home/code/ai_story/backend/core/ai_client
cat base.py
```

**基类接口(参考):**
```python
class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> AsyncIterator[str] | str:
        pass

class BaseImageClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
```

**步骤2: 创建Mock LLM客户端**

**文件:** `backend/core/ai_client/mock_llm_client.py`

```python
"""
Mock LLM Client - 用于离线测试和开发环境验证
"""
import asyncio
from typing import AsyncIterator
from .base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Mock LLM客户端,模拟文本生成"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "mock_api_key"
        self.is_mock = True

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """生成文本(非流式)"""

        # 模拟API延迟(0.5-2秒)
        await asyncio.sleep(0.5 + (hash(prompt) % 15) / 10)

        # 返回Mock响应
        responses = [
            "这是一个关于{prompt}的详细故事。",
            "在阳光明媚的下午,故事开始了...",
            "经过一系列有趣的冒险,最后圆满结束。"
        ]

        import random
        return random.choice(responses)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncIterator[str]:
        """生成文本(流式)"""

        response = await self.generate(prompt, max_tokens)

        # 模拟流式输出(分块返回)
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)  # 模拟网络延迟

    async def health_check(self) -> bool:
        """健康检查"""
        await asyncio.sleep(0.1)
        return True
```

**步骤3: 创建Mock Image客户端**

**文件:** `backend/core/ai_client/mock_image_client.py`

```python
"""
Mock Image Client - 模拟文生图
"""
import asyncio
import random
from typing import Dict, Any
from .base import BaseImageClient


class MockText2ImageClient(BaseImageClient):
    """Mock文生图客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "mock_api_key"
        self.is_mock = True

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "vivid",
        **kwargs
    ) -> str:
        """生成图片,返回URL"""

        # 模拟API延迟(1-3秒)
        await asyncio.sleep(1 + (hash(prompt) % 20) / 10)

        # 返回占位图片URL
        mock_urls = [
            "https://placehold.co/1024x1024",
            "https://via.placeholder.com/1024x1024",
            "https://dummyimage.com/1024x1024.jpg"
        ]

        import random
        url = random.choice(mock_urls)
        return f"{url}?text={prompt[:20]}"

    async def health_check(self) -> bool:
        """健康检查"""
        await asyncio.sleep(0.1)
        return True
```

**步骤4: 创建Mock Video客户端**

**文件:** `backend/core/ai_client/mock_video_client.py`

```python
"""
Mock Video Client - 模拟图生视频
"""
import asyncio
import random
from typing import Dict, Any
from .base import BaseImageClient  # Video客户端继承Image基类


class MockImage2VideoClient(BaseImageClient):
    """Mock图生视频客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or "mock_api_key"
        self.is_mock = True

    async def generate(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        **kwargs
    ) -> str:
        """生成视频,返回URL"""

        # 模拟API延迟(2-5秒)
        await asyncio.sleep(2 + (hash(image_url) % 30) / 10)

        # 返回占位视频URL
        mock_videos = [
            "https://sample-videos.com/video1.mp4",
            "https://samplelib.com/videos/sample.mp4"
        ]

        import random
        return random.choice(mock_videos)

    async def health_check(self) -> bool:
        """健康检查"""
        await asyncio.sleep(0.1)
        return True
```

**步骤5: 更新工厂类以支持Mock客户端**

**文件:** `backend/core/ai_client/factory.py`

添加Mock客户端注册:

```python
# 在文件顶部导入
from .mock_llm_client import MockLLMClient
from .mock_image_client import MockText2ImageClient
from .mock_video_client import MockImage2VideoClient

# 在create_ai_client函数中添加:
def create_ai_client(
    client_type: str,
    provider: str = "openai",
    api_key: str = None
):
    """创建AI客户端"""

    # 检查环境变量
    import os
    if os.getenv("ENABLE_MOCK_AI", "false").lower() == "true":
        # 返回Mock客户端
        if client_type == "llm":
            return MockLLMClient(api_key)
        elif client_type == "image":
            return MockText2ImageClient(api_key)
        elif client_type == "video":
            return MockImage2VideoClient(api_key)

    # 原有的真实客户端创建逻辑...
```

**步骤6: 测试Mock客户端**

创建测试文件验证Mock客户端:

**文件:** `backend/tests/test_mock_ai_clients.py`

```python
"""
测试Mock AI客户端
"""
import pytest
import asyncio
from core.ai_client.factory import create_ai_client
from core.ai_client.mock_llm_client import MockLLMClient


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mock_llm_client():
    """测试Mock LLM客户端"""
    client = MockLLMClient()

    # 测试非流式生成
    response = await client.generate("测试prompt")
    assert isinstance(response, str)
    assert len(response) > 0
    assert client.is_mock is True

    # 测试健康检查
    assert await client.health_check() is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mock_image_client():
    """测试Mock Image客户端"""
    from core.ai_client.mock_image_client import MockText2ImageClient

    client = MockText2ImageClient()

    # 测试图片生成
    url = await client.generate("测试prompt")
    assert isinstance(url, str)
    assert "http" in url
    assert client.is_mock is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mock_video_client():
    """测试Mock Video客户端"""
    from core.ai_client.mock_video_client import MockImage2VideoClient

    client = MockImage2VideoClient()

    # 测试视频生成
    url = await client.generate("http://example.com/image.jpg")
    assert isinstance(url, str)
    assert "http" in url
    assert client.is_mock is True
```

**步骤7: 运行测试验证**

```bash
cd /home/code/ai_story/backend

# 运行Mock客户端测试
python3 -m pytest tests/test_mock_ai_clients.py -v

# 预期结果: 所有测试通过
```

---

### 任务3: Story 2.1 - 配置结构化日志 (1小时)

**目标:** 实现JSON格式的结构化日志系统

**步骤1: 安装python-json-logger**

```bash
cd /home/code/ai_story/backend

# 安装依赖
# 使用uv:
uv add python-json-logger

# 或使用pip:
python3 -m pip install python-json-logger
```

**步骤2: 配置Django日志**

**文件:** `backend/config/settings/base.py`

添加或修改LOGGING配置:

```python
import os
import json

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.json.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s [%(module)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': 'logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

**步骤3: 创建日志目录**

```bash
cd /home/code/ai_story/backend
mkdir -p logs
```

**步骤4: 测试结构化日志**

```python
# 在Django shell中测试
python3 manage.py shell

import logging
logger = logging.getLogger(__name__)
logger.info("测试结构化日志", extra={"context": "test"})
logger.error("错误测试", extra={"error_code": "TEST_001"})
```

**预期输出:**
```json
{"message": "测试结构化日志", "context": "test", "levelname": "INFO", ...}
```

---

### 任务4: Epic 3 - 验证WebSocket连接 (30分钟)

**目标:** 验证WebSocket连接稳定性,测量进度推送延迟

**步骤1: 启动所有服务**

```bash
# 终端1: Redis
docker run -d -p 6379:6379 redis:latest

# 终端2: Django ASGI
cd /home/code/ai_story/backend
./run_asgi.sh

# 终端3: 前端
cd /home/code/ai_story/frontend
npm run dev
```

**步骤2: 测试WebSocket连接**

**创建测试脚本:** `backend/test_websocket.py`

```python
"""
WebSocket连接测试
"""
import asyncio
import websockets
import time

async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/projects/1/"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")

            # 测试接收消息
            start_time = time.time()
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            end_time = time.time()

            latency = (end_time - start_time) * 1000  # 转换为毫秒
            print(f"📊 接收消息延迟: {latency:.2f}ms")

            print(f"📝 收到消息: {message}")

    except asyncio.TimeoutError:
        print("❌ WebSocket连接超时")
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
```

**步骤3: 运行测试**

```bash
cd /home/code/ai_story/backend
python3 test_websocket.py
```

**步骤4: 测试进度推送延迟**

```bash
# 启动一个测试项目,观察进度推送延迟
# 使用curl测试WebSocket连接
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Host: localhost:8000" \
  -H "Origin: http://localhost:3000" \
  http://localhost:8000/ws/projects/1/
```

---

## 📊 验收标准

### 任务1: pytest测试框架

- ✅ pytest命令可运行
- ✅ pytest.ini正确配置
- ✅ 测试可被发现和执行
- ✅ 覆盖率报告可生成

### 任务2: Mock AI客户端

- ✅ MockLLMClient可生成文本
- ✅ MockImageClient可生成图片URL
- ✅ MockVideoClient可生成视频URL
- ✅ 所有Mock客户端支持health_check()
- ✅ 可通过环境变量ENABLE_MOCK_AI=true启用
- ✅ 单元测试通过

### 任务3: 结构化日志

- ✅ 日志输出为JSON格式
- ✅ 日志文件正确轮转
- ✅ 敏感信息(API密钥)自动脱敏

### 任务4: WebSocket连接

- ✅ WebSocket可成功连接
- ✅ 连接延迟<1秒
- ✅ 进度推送延迟<500ms
- ✅ 连接稳定,无频繁断连

---

## 🎯 完成后的下一步

### 今天结束时(完成4个任务后):

**已达成:**
- ✅ 测试框架完全可用
- ✅ Mock AI客户端实现
- ✅ 结构化日志系统上线
- ✅ WebSocket连接验证通过

**明天开始(Day 2):**
- [ ] Epic 1: Story 1.4 核心模块单元测试
- [ ] Epic 2: Story 2.2 健康检查端点实现
- [ ] Epic 3: WebSocket自动重连机制

---

## 📝 执行日志

**执行者:** ____________ (请填写姓名)
**执行日期:** ____________
**环境:** _____________

**任务执行记录:**
- [ ] 任务1: pytest验证 - 状态:______ 用时:______
- [ ] 任务2: Mock客户端 - 状态:______ 用时:______
- [ ] 任务3: 结构化日志 - 状态:______ 用时:______
- [ ] 任务4: WebSocket验证 - 状态:______ 用时:______

**问题记录:**
- 问题1: ____________
- 解决方案: ____________

---

## 🔧 环境准备检查清单

在开始执行前,请确认:

- [ ] Python 3.11+已安装
- [ ] Django 3.2.15已安装
- [ ] 可连接到Redis (localhost:6379)
- [ ] 有权限安装Python包
- [ ] 浏览器可访问localhost:3000
- [ ] 终端可使用

---

**重要提醒:**
1. 遇到问题时,参考`backend/README.md`的"常见问题排查"章节
2. 所有服务必须按正确顺序启动(Redis → Celery → Django → 前端)
3. 测试前确保数据库已迁移(`python3 manage.py migrate`)

---

*本指南基于BMad实施计划文档(`implementation-plan.md`)生成,用于指导Phase 1 Day 1的并行执行任务。*

**下一步:** 完成今日4个任务后,更新`phase-1-progress.md`,并准备Day 2的工作计划。
