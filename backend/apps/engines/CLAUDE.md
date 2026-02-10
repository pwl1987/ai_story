# Engines App - 引擎监控与配置管理

## 概述

**Engines App** 是 AI Story 系统的引擎监控与配置管理模块（Epic 11 - Sub-Epic 11.3），负责统一管理三种 AI 引擎类型的配置、健康检查和成本追踪。

## 职责

1. **引擎配置管理** - 统一管理 LLM/Image/TTS 三种引擎的配置
2. **主备引擎切换** - 支持主引擎和备份引擎的自动故障切换
3. **健康状态监控** - 实时监控引擎健康状态
4. **使用统计** - 追踪请求统计和成本分析

## 数据模型

### EngineConfig
引擎配置主模型，存储引擎配置和状态信息。

**关键字段：**
- `engine_type` - 引擎类型 (llm/image/tts)
- `primary_provider` - 主引擎提供商
- `fallback_provider` - 备份引擎提供商
- `health_status` - 健康状态 (online/offline/error/unknown)
- `auto_fallback` - 是否自动切换

**核心方法：**
- `get_active_provider()` - 获取当前应使用的引擎
- `should_fallback()` - 判断是否需要切换
- `calculate_success_rate()` - 计算成功率
- `record_success()` - 记录成功请求
- `record_failure()` - 记录失败请求

### EngineHealthLog
健康检查日志，记录每次健康检查的详细信息。

### EngineUsageLog
使用日志，记录每次引擎调用的详细信息。

### FallbackEventLog
Fallback 事件日志，记录引擎自动切换事件。

## 支持的提供商

### LLM 提供商
- ollama - 本地 LLM 引擎
- openai - OpenAI GPT 系列
- anthropic - Claude 系列
- glm - 智谱 GLM 系列
- deepseek - DeepSeek 系列

### Image 提供商
- comfyui - 本地 ComfyUI
- dalle - DALL-E 3
- stable-diffusion - Stable Diffusion
- midjourney - Midjourney

### TTS 提供商
- edge-tts - 微软 Edge TTS
- elevenlabs - ElevenLabs
- azure-tts - 微软 Azure TTS
- google-tts - Google TTS

## 文件结构

```
apps/engines/
├── __init__.py              # App 定义
├── apps.py                  # AppConfig
├── models.py                # 数据模型 (4个模型)
├── admin.py                 # Django Admin 配置
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest fixtures
│   ├── test_models.py       # 模型测试
│   └── test_admin.py        # Admin 测试
├── migrations/              # 数据库迁移
└── CLAUDE.md                # 本文档
```

## Admin 界面

访问 `/admin/engines/` 可管理：

1. **引擎配置** - 查看、创建、编辑引擎配置
2. **健康日志** - 查看健康检查历史
3. **使用日志** - 查看引擎使用记录
4. **Fallback 日志** - 查看引擎切换事件

### Admin 操作

- **测试连接** - 测试引擎连接状态（占位符，Story 11.3.2 实现）
- **重置统计** - 重置引擎统计信息
- **启用/禁用自动 Fallback** - 切换自动故障切换
- **标记在线/离线** - 手动设置引擎状态

## 测试覆盖

- **单元测试**: 65 个测试全部通过
- **覆盖率**: 95%
- **模型测试**: 100% 覆盖
- **Admin 测试**: 98% 覆盖

运行测试：
```bash
cd backend
uv run pytest apps/engines/tests/ -v
uv run pytest apps/engines/tests/ --cov=apps.engines --cov-report=term-missing
```

## 相关架构模式

### 单一职责 (SRP)
- `EngineConfig` - 只负责配置存储
- `EngineHealthLog` - 只负责健康日志
- `EngineUsageLog` - 只负责使用日志

### 开闭原则 (OCP)
- 通过 JSON 配置支持新引擎，无需修改模型
- 提供商列表可通过类属性扩展

### 依赖倒置 (DIP)
- 依赖抽象的 provider 标识符
- 不依赖具体引擎实现

## 相关 Story

- **Story 11.3.1** - EngineConfig 数据模型 ✅ (当前)
- **Story 11.3.2** - 引擎健康检查 (待实施)
- **Story 11.3.3** - 引擎配置前端界面 (待实施)

## 相关模块

- `apps/models/` - AI 模型管理
- `apps/proxy/` - 代理管理系统（类似模式）
- `core/ai_client/` - AI 客户端抽象层

## 下一步

Story 11.3.2 将实现：
1. 健康检查服务
2. Celery 定时任务
3. Fallback 自动切换
4. WebSocket 实时推送
5. 成本计算逻辑
