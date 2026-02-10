# Story 10.3: ComfyUI本地图像生成集成

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为系统开发者,
我想要集成 ComfyUI 本地 Stable Diffusion 引擎,
以便为漫剧生成高质量图像,同时将图像生成成本降低到接近零。

## 接受标准

1. 系统能够使用 ComfyUI 生成图像文件 (PNG/JPEG)
2. 创建 ComfyUIClient 类实现图像生成接口
3. 支持文生图 (text-to-image) 和图生图 (image-to-image)
4. 支持图像参数调节 (width, height, steps, cfg_scale, seed)
5. 实现 Fallback 机制: ComfyUI 失败时自动切换到 StableDiffusionClient
6. 添加图像生成健康检查和工作流列表获取
7. 编写单元测试覆盖 ComfyUIClient 核心功能
8. 更新 AI 客户端工厂支持 ComfyUI 提供商

## 任务 / 子任务

- [ ] Task 1: 重构现有 ComfyUIClient 实现 (AC: #1, #2)
  - [ ] Subtask 1.1: 分析现有 comfyui_client.py (588行) 代码结构
  - [ ] Subtask 1.2: 重构为符合 SOLID 原则的类结构
  - [ ] Subtask 1.3: 实现 Text2ImageClient 抽象基类接口
  - [ ] Subtask 1.4: 实现图生图 (Image2Image) 功能支持
  - [ ] Subtask 1.5: 添加完整的类型注解和文档字符串

- [ ] Task 2: 实现图像生成核心功能 (AC: #3, #4)
  - [ ] Subtask 2.1: 实现文生图工作流 (_generate_image 方法)
  - [ ] Subtask 2.2: 实现图生图工作流 (_generate_image_with_input 方法)
  - [ ] Subtask 2.3: 支持参数调节 (width, height, steps, cfg_scale, seed)
  - [ ] Subtask 2.4: 实现 WebSocket 实时进度监听
  - [ ] Subtask 2.5: 支持批量生成 (num_images > 1)

- [ ] Task 3: 实现 Fallback 机制 (AC: #5)
  - [ ] Subtask 3.1: 添加 fallback_to_stable_diffusion 配置参数
  - [ ] Subtask 3.2: 实现自动降级逻辑 (ComfyUI → StableDiffusionClient)
  - [ ] Subtask 3.3: 添加 fallback 事件日志记录
  - [ ] Subtask 3.4: 配置 ModelProvider 支持主备引擎

- [ ] Task 4: 健康检查和工作流管理 (AC: #6, #8)
  - [ ] Subtask 4.1: 实现 health_check() 验证 ComfyUI 服务可用性
  - [ ] Subtask 4.2: 实现 get_workflows() 获取可用工作流列表
  - [ ] Subtask 4.3: 实现 validate_workflow() 验证工作流 JSON 格式
  - [ ] Subtask 4.4: 更新 AI 客户端工厂注册 ComfyUI 提供商

- [ ] Task 5: 单元测试和集成测试 (AC: #7)
  - [ ] Subtask 5.1: 测试文生图功能 (Mock ComfyUI API)
  - [ ] Subtask 5.2: 测试图生图功能 (Mock ComfyUI API)
  - [ ] Subtask 5.3: 测试 Fallback 机制 (使用 Mock)
  - [ ] Subtask 5.4: 测试健康检查和工作流管理
  - [ ] Subtask 5.5: 集成测试: 验证与真实 ComfyUI 服务连接 (可选)

## 开发者注意事项

### 相关架构模式和约束

- **SOLID 原则**: ComfyUIClient 必须继承自 Text2ImageClient 和 Image2ImageClient 抽象基类
- **策略模式**: ComfyUI 作为图像生成提供商的一个具体策略实现
- **工厂模式**: 通过 AIClientFactory 动态创建 ComfyUIClient 实例
- **开闭原则**: 对扩展开放 (新图像生成提供商), 对修改封闭
- **依赖倒置**: 依赖 Text2ImageClient 抽象, 不依赖具体实现

**现有代码参考:**
- `core/ai_client/base.py` - Text2ImageClient 和 Image2ImageClient 抽象基类定义
- `core/ai_client/comfyui_client.py` - 现有 ComfyUI 客户端实现 (需要重构)
- `core/ai_client/text2image_client.py` - Stable Diffusion 客户端实现参考
- `core/ai_client/factory.py` - 客户端工厂模式

### ComfyUI API 参考

**基本工作流:**
```python
# 1. 提交任务到队列
POST /prompt
{
  "prompt": { workflow_json },
  "client_id": "uuid",
  "prompt_id": "uuid"
}

# 2. 通过 WebSocket 监听进度
WS /ws?clientId=uuid
# 消息类型: progress, executing, status

# 3. 获取任务历史
GET /history/{prompt_id}

# 4. 下载生成的图像
GET /view?filename=xxx.png&subfolder=&type=output
```

**工作流 JSON 格式:**
```json
{
  "1": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 123456,
      "steps": 20,
      "cfg": 7.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0
    }
  },
  "2": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "sdxl-base-1.0.safetensors"
    }
  }
}
```

**主要参数:**
- `workflow`: 工作流 JSON (包含所有节点配置)
- `prompt_id`: 任务 ID (UUID)
- `client_id`: 客户端 ID (UUID)
- `width/height`: 图像尺寸 (默认 512x512)
- `steps`: 采样步数 (默认 20)
- `cfg`: CFG 强度 (默认 7.0)
- `seed`: 随机种子 (None 则随机生成)
- `num_images`: 批量生成数量 (默认 1)

### 需要接触的源代码树组件

**修改文件:**
- `backend/core/ai_client/comfyui_client.py` - 重构现有实现 (588行)
- `backend/pyproject.toml` - 验证依赖 (websocket-client, requests, Pillow)
- `backend/core/ai_client/factory.py` - 更新工厂注册 ComfyUIClient
- `backend/apps/models/models.py` - 在 TEXT2IMAGE_EXECUTORS 添加 ComfyUIClient

**新增文件:**
- `backend/tests/test_comfyui_client.py` - ComfyUIClient 单元测试

### 测试标准摘要

- **单元测试覆盖率**: >90% (核心逻辑)
- **Mock 使用**: 使用 responses 库模拟 ComfyUI API 响应
- **集成测试**: 验证与真实 ComfyUI 服务连接 (可选)
- **错误处理测试**: 覆盖网络超时、服务不可用、工作流无效等场景

### 项目结构说明

- **遵循统一项目结构**: 图像生成客户端放在 `core/ai_client/` 目录
- **检测到的冲突或变体**:
  - 现有 comfyui_client.py 已实现但需要重构 (588行, 缺少图生图支持)
  - 需要同时实现 Text2ImageClient 和 Image2VideoClient 接口

### 重构要点

**现有实现问题:**
1. ❌ 缺少类型注解和完整文档字符串
2. ❌ 未实现图生图 (image-to-image) 功能
3. ❌ Fallback 机制未实现
4. ❌ 工作流管理功能缺失 (get_workflows, validate_workflow)
5. ❌ 单元测试覆盖不足

**重构目标:**
1. ✅ 完整的类型注解 (Type hinting)
2. ✅ 实现图生图功能 (Image2Image)
3. ✅ 实现 Fallback 到 StableDiffusionClient
4. ✅ 添加工作流管理 API
5. ✅ 完整的单元测试覆盖

### 参考资料

- **设计文档**: [Source: docs/manhua-production-system-v3.md#本地引擎集成方案]
- **ComfyUI GitHub**: https://github.com/comfyanonymous/ComfyUI
- **ComfyUI API 文档**: https://docs.comfy.org/
- **现有 Ollama 客户端**: backend/core/ai_client/ollama_client.py (参考 Fallback 实现)
- **现有 Edge-TTS 客户端**: backend/core/ai_client/edge_tts_client.py (参考健康检查实现)
- **现有 ComfyUI 客户端**: backend/core/ai_client/comfyui_client.py (需要重构)

## 开发者代理记录

### 使用的代理模型

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### 调试日志引用

无 (新功能开发)

### 完成注意事项列表

**待实施:**

**Phase 1: 代码重构 (Day 1)**
- 分析现有 comfyui_client.py 代码结构
- 重构为符合 SOLID 原则的类结构
- 添加完整的类型注解和文档字符串

**Phase 2: 功能实现 (Day 2-3)**
- 实现图生图 (Image2Image) 功能
- 实现 Fallback 机制
- 添加工作流管理 API

**Phase 3: 测试和集成 (Day 4)**
- 编写单元测试 (>90% 覆盖率)
- 集成测试 (可选)
- 更新 AI 客户端工厂

**依赖版本:**
- websocket-client: >=1.0.0 (已安装)
- requests: >=2.28.0 (已安装)
- Pillow: >=9.0.0 (已安装)

**遗留任务:**
- ComfyUI 安装文档 (Docker 方式)
- 环境变量配置文档 (低优先级)

### 文件列表

**修改:**
- core/ai_client/comfyui_client.py (重构, 588行 → ~700行)
- pyproject.toml (验证依赖)
- core/ai_client/factory.py (更新工厂注册)
- apps/models/models.py (TEXT2IMAGE_EXECUTORS 添加 ComfyUIClient)

**新增:**
- backend/tests/test_comfyui_client.py (单元测试, ~300行)

---

**生成时间**: 2026-02-06
**设计文档版本**: v3.0
**Epic**: Epic 10 - 漫剧生产系统
**上一个Story**: 10.2 - Edge-TTS本地语音合成集成 (DONE)
**下一个Story**: 10.4 - 本地引擎统一健康检查和监控
