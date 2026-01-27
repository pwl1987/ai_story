# CLAUDE.md - AI客户端模块 (ai_client)

[根目录](../../../CLAUDE.md) > [backend](../../) > [core](../) > **ai_client**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

AI客户端模块是系统的**策略模式实现层**，负责：
- 定义统一的AI客户端抽象接口
- 实现各种AI服务提供商的客户端（OpenAI、Claude、Stable Diffusion、Runway等）
- 提供工厂模式动态创建客户端
- 统一响应格式（AIResponse）

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [base.py](./base.py) | 抽象基类（BaseAIClient、LLMClient、Text2ImageClient、Image2VideoClient） |
| [factory.py](./factory.py) | 客户端工厂（动态创建AI客户端） |
| [openai_client.py](./openai_client.py) | OpenAI兼容客户端实现 |
| [text2image_client.py](./text2image_client.py) | 文生图客户端实现 |
| [image2video_client.py](./image2video_client.py) | 图生视频客户端实现 |
| [comfyui_client.py](./comfyui_client.py) | ComfyUI客户端实现 |
| [mock_llm_client.py](./mock_llm_client.py) | Mock LLM客户端（测试用） |
| [mock_text2image_client.py](./mock_text2image_client.py) | Mock 文生图客户端（测试用） |
| [mock_image2video_client.py](./mock_image2video_client.py) | Mock 图生视频客户端（测试用） |
| [registry.py](./registry.py) | 客户端注册表 |

### 类层次结构

```
BaseAIClient (抽象基类)
    ├── LLMClient (抽象基类)
    │   ├── OpenAIClient (OpenAI/Claude)
    │   └── MockLLMClient (测试)
    ├── Text2ImageClient (抽象基类)
    │   ├── StableDiffusionClient
    │   ├── ComfyUIClient
    │   └── MockText2ImageClient (测试)
    └── Image2VideoClient (抽象基类)
        ├── RunwayClient
        ├── ComfyUIClient
        └── MockImage2VideoClient (测试)
```

---

## 对外接口

### 统一响应格式

所有AI客户端返回统一的 `AIResponse`：

```python
@dataclass
class AIResponse:
    """AI响应统一数据结构"""
    success: bool              # 是否成功
    text: str = ""             # 文本内容（LLM）
    data: Dict[str, Any]       # 额外数据（图片URL、视频URL等）
    metadata: Dict[str, Any]   # 元数据（tokens_used、model等）
    error: Optional[str]       # 错误信息
```

### BaseAIClient 接口

```python
class BaseAIClient(ABC):
    """所有AI客户端的基类"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """生成内容"""
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        return await self.validate_config()
```

### LLMClient 接口

```python
class LLMClient(BaseAIClient):
    """LLM客户端（文本生成）"""

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        """生成文本"""
        pass
```

### Text2ImageClient 接口

```python
class Text2ImageClient(BaseAIClient):
    """文生图客户端"""

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> AIResponse:
        """生成图片"""
        pass
```

### Image2VideoClient 接口

```python
class Image2VideoClient(BaseAIClient):
    """图生视频客户端"""

    async def generate(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        **kwargs
    ) -> AIResponse:
        """生成视频"""
        pass
```

---

## 关键依赖与配置

### 工厂模式使用

```python
from core.ai_client.factory import create_ai_client
from apps.models.models import ModelProvider

# 从数据库获取模型配置
provider = ModelProvider.objects.get(id=xxx)

# 动态创建客户端
client = create_ai_client(provider)

# 调用生成
response = await client.generate(prompt="...")
```

### 工厂实现

```python
# core/ai_client/factory.py

def create_ai_client(provider: ModelProvider) -> BaseAIClient:
    """
    1. 从 ModelProvider.executor_class 获取类路径
    2. 如果为空，调用 get_default_executor() 获取默认执行器
    3. 动态导入并实例化客户端类
    4. 传入 api_url, api_key, model_name 等配置
    """
    executor_class_path = provider.executor_class or provider.get_default_executor()
    executor_class = get_executor_class(executor_class_path)
    return executor_class(
        api_url=provider.api_url,
        api_key=provider.api_key,
        model_name=provider.model_name
    )
```

### 配置示例

```python
# OpenAI 兼容客户端配置
provider = ModelProvider(
    name="GPT-4",
    provider_type="llm",
    executor_class="core.ai_client.openai_client.OpenAIClient",
    api_url="https://api.openai.com/v1",
    api_key="sk-xxx",
    model_name="gpt-4",
    max_tokens=2000,
    temperature=0.7
)

# Stable Diffusion 配置
provider = ModelProvider(
    name="Stable Diffusion XL",
    provider_type="text2image",
    executor_class="core.ai_client.text2image_client.Text2ImageClient",
    api_url="http://localhost:7860",
    api_key="",
    model_name="sdxl-base-1.0"
)
```

---

## 数据模型

### 无独立数据模型

本模块不包含Django模型，依赖 `apps.models.models.ModelProvider` 存储配置。

---

## 测试与质量

### 当前测试覆盖 (Day 6更新)

- ✅ **Registry 100%覆盖** - `test_ai_client_registry.py` (25个测试) 🏆
- ✅ **Factory 95%覆盖** - `test_core_ai_client_factory.py` (143行测试)
- ✅ **Base 86%覆盖** - `test_core_ai_client_base.py` (95%覆盖)
- ✅ **Mock客户端测试** - `test_mock_ai_clients.py` (149行测试)
- ✅ **集成测试** - `tests/integration/` (30个测试，验证端到端流程)

### 测试文件清单

```
tests/
├── test_ai_client_registry.py        # 25个测试，100%覆盖 🏆
├── test_core_ai_client_factory.py    # 143行测试
├── test_core_ai_client_base.py       # 95%覆盖
└── test_mock_ai_clients.py           # Mock客户端完整测试
```

### Mock 客户端使用

```python
from core.ai_client.mock_llm_client import MockLLMClient

# 创建 Mock 客户端
client = MockLLMClient(
    api_url="mock://",
    api_key="mock",
    model_name="mock-model"
)

# 调用生成
response = await client.generate("测试提示词")
# 返回: AIResponse(success=True, text="Mock 响应...")
```

---

## 常见问题 (FAQ)

### Q1: 如何添加新的AI客户端？

**A:** 步骤：
1. 继承合适的基类（LLMClient/Text2ImageClient/Image2VideoClient）
2. 实现 `generate()` 和 `validate_config()` 方法
3. 返回标准的 `AIResponse` 对象
4. 在 `ModelProvider` 模型中添加 `executor_class` 选项

示例：
```python
from core.ai_client.base import LLMClient

class MyLLMClient(LLMClient):
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        # 实现你的逻辑
        return AIResponse(success=True, text="...")

    async def validate_config(self) -> bool:
        # 验证配置
        return True
```

### Q2: 如何处理API限流？

**A:** 在 `ModelProvider` 中配置：
```python
provider = ModelProvider(
    ...
    rate_limit_rpm=60,  # 每分钟60次
    rate_limit_rpd=1000  # 每天1000次
)
```

### Q3: 如何切换模型提供商？

**A:** 修改 `ModelProvider.executor_class`：
```python
# 从 OpenAI 切换到 Claude
provider.executor_class = "core.ai_client.openai_client.OpenAIClient"
provider.api_url = "https://api.anthropic.com/v1"
provider.model_name = "claude-3-opus-20240229"
provider.save()
```

### Q4: 支持负载均衡吗？

**A:** 是的，在 `ProjectModelConfig` 中配置：
```python
config.load_balance_strategy = 'weighted'  # 权重策略
config.model_providers.add(provider1)  # priority=10
config.model_providers.add(provider2)  # priority=20
```

---

## 相关文件清单

### 核心文件

```
backend/core/ai_client/
├── __init__.py
├── base.py                    # 抽象基类
├── factory.py                 # 工厂模式
├── registry.py                # 客户端注册表
├── openai_client.py           # OpenAI兼容客户端
├── text2image_client.py       # 文生图客户端
├── image2video_client.py      # 图生视频客户端
├── comfyui_client.py          # ComfyUI客户端
├── mock_llm_client.py         # Mock LLM客户端
├── mock_text2image_client.py  # Mock 文生图客户端
└── mock_image2video_client.py # Mock 图生视频客户端
```

### 关键依赖

```
# 领域依赖
apps/models/models.py         # ModelProvider 模型

# 外部依赖
httpx                         # 异步HTTP客户端
```

---

## 变更记录 (Changelog)

### 2026-01-26 12:08:52
- 初始化AI客户端模块文档
- 添加导航面包屑
- 完成接口、工厂模式、测试覆盖分析
