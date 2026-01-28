# Enhanced Mock客户端使用指南

**版本**: 1.0
**更新时间**: 2026-01-28
**状态**: ✅ 已集成到factory.py

---

## 📋 概述

Enhanced Mock客户端是标准Mock客户端的增强版本，提供了更强大的测试和调试功能：

### 新增功能

1. **可配置响应延迟** - 模拟真实API响应时间
2. **错误场景模拟** - 模拟超时、限流、服务器错误
3. **请求日志记录** - 记录所有Mock请求详情
4. **自定义响应** - 覆盖默认Mock响应数据
5. **动态配置** - 运行时调整Mock行为

---

## 🚀 快速开始

### 1. 启用Enhanced Mock

有两种方式启用Enhanced Mock客户端：

#### 方式1: 环境变量（推荐）

```bash
# 启用Mock模式
export ENABLE_MOCK_AI=true

# 启用Enhanced Mock
export USE_ENHANCED_MOCK=true

# 可选：配置响应延迟（秒）
export MOCK_DELAY=0.5

# 可选：模拟错误类型
export MOCK_ERROR=timeout  # 可选: timeout, rate_limit, server_error
```

#### 方式2: Django Settings

在 `config/settings/base.py` 中添加：

```python
import os

# Mock配置
ENABLE_MOCK_AI = os.environ.get('ENABLE_MOCK_AI', 'false').lower() == 'true'
USE_ENHANCED_MOCK = os.environ.get('USE_ENHANCED_MOCK', 'false').lower() == 'true'
MOCK_DELAY = float(os.environ.get('MOCK_DELAY', '0.5'))
MOCK_ERROR = os.environ.get('MOCK_ERROR', '')
```

---

## 📖 使用示例

### 示例1: 基础使用（默认配置）

```python
from core.ai_client.factory import create_ai_client
from apps.models.models import ModelProvider

# 获取一个LLM Provider
provider = ModelProvider.objects.filter(provider_type='llm').first()

# 创建客户端（自动使用Enhanced Mock）
client = create_ai_client(provider)

# 调用生成
response = await client.generate(
    prompt="测试提示词",
    max_tokens=1000,
    temperature=0.7
)

print(f"成功: {response.success}")
print(f"文本: {response.text}")
print(f"元数据: {response.metadata}")
```

**输出**:
```
成功: True
文本: 这是一个模拟的 LLM 响应...
元数据: {
  'tokens_used': 250,
  'latency_ms': 500,
  'model': 'enhanced-mock-llm',
  'is_mock': True,
  'simulate_delay': 0.5
}
```

---

### 示例2: 模拟慢速API

```bash
# 设置延迟为2秒
export MOCK_DELAY=2.0
```

```python
import time

start = time.time()
response = await client.generate(prompt="测试")
end = time.time()

print(f"实际耗时: {end - start:.2f}秒")
# 输出: 实际耗时: 2.05秒
```

---

### 示例3: 模拟API错误

#### 3.1 模拟超时错误

```bash
export MOCK_ERROR=timeout
```

```python
response = await client.generate(prompt="测试")

print(f"成功: {response.success}")
print(f"错误: {response.error}")
```

**输出**:
```
成功: False
错误: 模拟超时错误: API请求超时（超过30秒）
```

#### 3.2 模拟限流错误

```bash
export MOCK_ERROR=rate_limit
```

**输出**:
```
成功: False
错误: 模拟限流错误: API调用频率超限，请稍后重试
```

#### 3.3 模拟服务器错误

```bash
export MOCK_ERROR=server_error
```

**输出**:
```
成功: False
错误: 模拟服务器错误: 500 Internal Server Error
```

---

### 示例4: 查看请求日志

Enhanced Mock客户端会自动记录所有请求：

```python
from core.ai_client.enhanced_mock_llm_client import EnhancedMockLLMClient

# 创建客户端
client = EnhancedMockLLMClient(
    api_url='mock://',
    api_key='mock',
    model_name='test',
    enable_logging=True
)

# 调用生成
await client.generate(prompt="测试1")
await client.generate(prompt="测试2")

# 查看日志
logs = client.get_request_log()
for log in logs:
    print(f"时间: {log['timestamp']}")
    print(f"模型: {log['model']}")
    print(f"提示词长度: {log['prompt_length']}")
    print(f"延迟: {log['simulate_delay']}s")
    print("---")
```

---

### 示例5: 运行时动态配置

```python
client = EnhancedMockLLMClient(...)

# 修改延迟
client.set_simulate_delay(1.5)

# 模拟错误
client.set_simulate_error("timeout")

# 恢复正常
client.set_simulate_error(None)

# 设置自定义响应
client.set_custom_response("这是我的自定义响应")

# 清空日志
client.clear_request_log()
```

---

## 🔧 高级配置

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `simulate_delay` | float | 0.5 | 模拟延迟（秒） |
| `simulate_error` | str | None | 错误类型: timeout, rate_limit, server_error |
| `enable_logging` | bool | True | 是否启用请求日志 |
| `custom_response` | str | None | 自定义响应内容 |

---

## 📊 性能对比

### 延迟对比

| 客户端 | 平均响应时间 | 说明 |
|--------|------------|------|
| 标准Mock | ~0.01s | 立即返回 |
| Enhanced Mock (delay=0.5) | ~0.5s | 模拟快速API |
| Enhanced Mock (delay=2.0) | ~2.0s | 模拟慢速API |
| 真实API (GPT-4) | ~3-10s | 真实延迟 |

### 使用场景建议

**使用标准Mock**:
- 单元测试（追求速度）
- CI/CD管道（需要快速反馈）
- 性能基准测试

**使用Enhanced Mock**:
- 集成测试（模拟真实延迟）
- 负载测试（测试慢速API影响）
- 错误处理测试（模拟各种失败场景）
- 调试和开发（查看请求日志）

---

## 🧪 测试场景

### 场景1: 测试重试机制

```python
# 模拟间歇性失败
client.set_simulate_error("rate_limit")

for i in range(3):
    response = await client.generate(prompt=f"尝试{i+1}")
    if response.success:
        print(f"第{i+1}次尝试成功")
        break
    else:
        print(f"第{i+1}次尝试失败: {response.error}")
        await asyncio.sleep(1)
```

### 场景2: 测试超时处理

```python
import asyncio

try:
    # 设置极长的延迟
    client.set_simulate_delay(10.0)

    # 使用wait_for模拟超时
    response = await asyncio.wait_for(
        client.generate(prompt="测试"),
        timeout=5.0
    )
except asyncio.TimeoutError:
    print("请求超时！")
```

### 场景3: 测试日志记录

```python
# 清空旧日志
client.clear_request_log()

# 执行多个请求
for i in range(10):
    await client.generate(prompt=f"测试{i}")

# 分析日志
logs = client.get_request_log()
total_tokens = sum(log.get('tokens_used', 0) for log in logs)
avg_latency = sum(log.get('latency_ms', 0) for log in logs) / len(logs)

print(f"总请求数: {len(logs)}")
print(f"总tokens: {total_tokens}")
print(f"平均延迟: {avg_latency:.2f}ms")
```

---

## 🐛 故障排查

### 问题1: Enhanced Mock没有生效

**症状**: 仍然使用标准Mock客户端

**检查**:
```bash
# 检查环境变量
echo $ENABLE_MOCK_AI
echo $USE_ENHANCED_MOCK
```

**解决**:
```bash
export ENABLE_MOCK_AI=true
export USE_ENHANCED_MOCK=true
```

---

### 问题2: 延迟没有生效

**症状**: 响应仍然很快

**检查**:
```python
print(client.simulate_delay)  # 应该显示设置的延迟值
```

**解决**:
```python
client.set_simulate_delay(2.0)  # 设置2秒延迟
```

---

### 问题3: 错误模拟无效

**症状**: 所有请求都成功

**检查**:
```python
print(client.simulate_error)  # 应该显示错误类型
```

**解决**:
```python
client.set_simulate_error("timeout")  # 设置超时错误
```

---

## 📚 最佳实践

### 1. 开发环境配置

创建 `.env` 文件：

```bash
# .env
ENABLE_MOCK_AI=true
USE_ENHANCED_MOCK=true
MOCK_DELAY=0.5
MOCK_ERROR=
```

在Django settings中加载：

```python
from dotenv import load_dotenv
load_dotenv()
```

### 2. 测试固件（Fixture）

```python
@pytest.fixture
async def enhanced_mock_llm():
    """Enhanced Mock LLM客户端固件"""
    from core.ai_client.enhanced_mock_llm_client import EnhancedMockLLMClient

    client = EnhancedMockLLMClient(
        api_url='mock://',
        api_key='mock',
        model_name='test',
        simulate_delay=0.1,  # 测试时使用较短延迟
        enable_logging=True
    )

    yield client

    # 清理
    client.clear_request_log()
```

### 3. 条件配置

```python
import os

# 根据环境选择Mock模式
if os.environ.get('PYTEST_CURRENT_TEST'):
    # 测试环境：使用快速Mock
    MOCK_DELAY = 0.01
    MOCK_ERROR = None
elif os.environ.get('DJANGO_ENV') == 'development':
    # 开发环境：使用中等延迟
    MOCK_DELAY = 0.5
    MOCK_ERROR = None
else:
    # 生产环境：不使用Mock
    ENABLE_MOCK_AI = False
```

---

## 🎯 总结

Enhanced Mock客户端为开发和测试提供了强大的Mock能力：

✅ **灵活配置** - 通过环境变量或代码动态配置
✅ **真实模拟** - 模拟延迟、错误等真实场景
✅ **调试友好** - 请求日志记录，便于问题定位
✅ **易于集成** - 已集成到factory.py，零代码改动

**使用建议**:
- 开发阶段: Enhanced Mock (delay=0.5s)
- 单元测试: 标准Mock (快速)
- 集成测试: Enhanced Mock (delay=1.0s, 模拟错误)
- 生产环境: 真实API

---

**相关文档**:
- [Factory模式文档](./factory.md)
- [Mock客户端文档](./mock_clients.md)
- [测试最佳实践](./testing_best_practices.md)

**最后更新**: 2026-01-28
**维护者**: AI Story Backend Team
