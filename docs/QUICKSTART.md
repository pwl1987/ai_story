# 🚀 AI Story - 快速开始指南

> 5分钟快速上手 AI Story视频生成系统

---

## ✨ 系统简介

AI Story是一个基于Django + Vue的AI驱动故事脚本到视频的自动化生成平台。

**核心工作流**:
```
文案改写 → 分镜生成 → 文生图 → 运镜生成 → 图生视频
```

**技术栈**:
- 后端: Django 5.2 LTS + DRF 3.16.1
- 前端: Vue 2.7 + daisyUI + Tailwind CSS
- 任务队列: Celery + Redis
- 实时通信: WebSocket (Channels)

---

## 🎯 快速开始（3步）

### 步骤1: 启动服务

```bash
# 终端1: 启动后端
cd backend
./run_asgi.sh

# 终端2: 启动前端
cd frontend
npm run dev

# 终端3: 启动Celery Worker
cd backend
uv run celery -A config worker -Q llm,image,video -l info
```

### 步骤2: 访问系统

打开浏览器访问: **http://localhost:3000/**

### 步骤3: 登录系统

使用Demo账户登录:
```
用户名: demo_user
密码: demo123456
```

---

## 📖 新手引导

### 1️⃣ 查看Demo项目

登录后，您会看到项目列表页面，里面有一个**Demo示例项目**。

**项目主题**: 宁静的小镇，清晨的阳光洒在石板路上，年轻的画家在溪边写生，远处的山峦若隐若现

点击项目卡片，查看：
- ✅ 5个工作流阶段配置
- ✅ 完整的提示词模板
- ✅ Mock AI模型配置

### 2️⃣ 执行完整工作流

1. 在项目详情页，点击 **"执行完整工作流"** 按钮
2. 观察5个阶段依次执行：
   - **Rewrite** - 文案改写
   - **Storyboard** - 分镜生成
   - **Image Generation** - 文生图
   - **Camera Movement** - 运镜生成
   - **Video Generation** - 图生视频
3. WebSocket实时推送进度更新

**使用Mock AI时，整个流程在1-2秒内完成！**

### 3️⃣ 查看结果

工作流完成后，可以查看：
- 每个阶段的输出结果
- 生成的分镜脚本
- AI生成的图片
- 运镜效果描述

---

## 🎨 创建自己的项目

### 方法1: 使用Demo模板（推荐）

1. 点击 **"创建项目"** 按钮
2. 输入项目主题，例如:
   ```
   科幻冒险：勇敢的宇航员在火星基地发现外星文明遗迹
   ```
3. 选择 **"Demo完整模板集"**
4. 选择 **"Demo Mock AI"** （快速体验）
5. 点击 **"创建"**
6. 创建成功后，点击 **"执行完整工作流"**

### 方法2: 配置真实AI

#### Step 1: 配置AI提供商

进入 **"模型管理"** → **"AI提供商"**，创建：

**LLM提供商**（用于文案改写、分镜生成、运镜生成）:
```
名称: OpenAI GPT-4
类型: LLM
执行器: core.ai_client.openai_llm_client.OpenAILLMClient
API URL: https://api.openai.com/v1
API密钥: sk-your-api-key
模型名称: gpt-4
```

**Text2Image提供商**（用于文生图）:
```
名称: Stable Diffusion
类型: Text2Image
执行器: core.ai_client.sd_text2image_client.SDText2ImageClient
API URL: http://localhost:7860
```

**Image2Video提供商**（用于图生视频）:
```
名称: Runway Gen-2
类型: Image2Video
执行器: core.ai_client.runway_i2v_client.RunwayI2VClient
API URL: https://api.runwayml.com/v1
API密钥: your-api-key
```

#### Step 2: 创建提示词模板

进入 **"提示词管理"** → **"模板集"**，创建新模板集：

**示例：文案改写模板**
```jinja2
你是一位专业的故事编剧。

原始文案：{{ raw_text }}

请改写为更生动的版本（不超过200字）：
```

**示例：分镜生成模板**
```jinja2
请根据以下文案生成分镜：

改写文案：{{ rewritten_text }}

要求：
1. 生成5-8个分镜
2. 包含场景描述、镜头角度、时长

输出JSON格式。
```

#### Step 3: 创建项目并关联配置

1. 创建项目时选择：
   - 提示词模板集
   - LLM提供商
   - Text2Image提供商
   - Image2Video提供商

2. 保存后执行工作流

---

## 📋 核心功能说明

### 项目管理

| 功能 | 说明 |
|------|------|
| 创建项目 | 输入主题，选择模板和AI提供商 |
| 查看项目 | 项目列表显示所有项目 |
| 项目详情 | 查看5个阶段配置和执行结果 |
| 删除项目 | 删除不需要的项目 |

### 工作流执行

| 阶段 | 功能 | 使用的AI |
|------|------|---------|
| **Rewrite** | 文案改写 | LLM |
| **Storyboard** | 分镜生成 | LLM |
| **Image Generation** | 文生图 | Text2Image |
| **Camera Movement** | 运镜生成 | LLM |
| **Video Generation** | 图生视频 | Image2Video |

### 提示词管理

- **模板集**: 管理一组相关的提示词模板
- **提示词模板**: 每个工作流阶段的AI指令
- **全局变量**: 可复用的变量（如：风格、质量要求）

### 模型管理

- **AI提供商**: 配置LLM、Text2Image、Image2Video服务
- **项目模型配置**: 将提供商关联到项目

---

## 🎯 使用技巧

### 技巧1: 快速体验

使用**Demo Mock AI**可以快速体验完整流程，无需配置真实API。

### 技巧2: 批量处理

可以同时创建多个项目，Celery会自动排队处理。

### 技巧3: 实时监控

利用WebSocket实时监控进度，无需刷新页面。

### 技巧4: 模板复用

创建好用的提示词模板后，可以在多个项目中复用。

### 技巧5: 配额管理

在 **"文件管理"** 中查看文件配额使用情况。

---

## ❓ 常见问题

### Q1: 工作流执行失败怎么办？

**A**: 检查以下几点：
1. Celery Worker是否运行
2. Redis是否正常运行
3. AI提供商配置是否正确
4. 查看错误日志获取详细错误信息

### Q2: 如何查看执行日志？

**A**:
- 开发环境: 查看Celery Worker终端输出
- 生产环境: 查看日志文件 `backend/logs/celery.log`

### Q3: Mock AI和真实AI有什么区别？

**A**:
- **Mock AI**: 返回预设的模拟数据，速度快，适合测试
- **真实AI**: 调用真实API生成内容，质量高，需要API密钥

### Q4: 如何切换到真实AI？

**A**:
1. 在"模型管理"中配置真实的AI提供商
2. 在项目配置中选择真实AI提供商
3. 重新执行工作流

### Q5: 支持哪些AI服务？

**A**:
- **LLM**: OpenAI (GPT-4)、Claude、通义千问、文心一言等
- **Text2Image**: Stable Diffusion、DALL-E、Midjourney等
- **Image2Video**: Runway Gen-2、Pika等

### Q6: 文件存储在哪里？

**A**:
- 开发环境: `backend/media/files/`
- 生产环境: 配置云存储（如阿里云OSS、AWS S3）

### Q7: 如何提高生成质量？

**A**:
1. 优化提示词模板
2. 调整AI模型参数（temperature、top_p等）
3. 使用更强大的AI模型
4. 增加后处理步骤

### Q8: 系统要求是什么？

**A**:
- Python 3.11+
- Node.js 16+
- Redis 7+
- PostgreSQL 14+ (生产环境)
- 至少4GB内存

---

## 🔧 进阶配置

### 配置真实OpenAI API

1. 获取OpenAI API密钥: https://platform.openai.com/api-keys
2. 在"模型管理"中创建LLM提供商
3. 配置参数:
```python
执行器: core.ai_client.openai_llm_client.OpenAILLMClient
API URL: https://api.openai.com/v1
API密钥: sk-your-api-key
模型名称: gpt-4
最大Token: 2000
Temperature: 0.7
```

### 配置Stable Diffusion

1. 安装Stable Diffusion WebUI
2. 启动API服务: `webui.sh --api`
3. 在"模型管理"中创建Text2Image提供商
4. 配置参数:
```python
执行器: core.ai_client.sd_text2image_client.SDText2ImageClient
API URL: http://localhost:7860
模型名称: sd_v1.5
```

### 配置Runway Gen-2

1. 获取Runway API密钥
2. 在"模型管理"中创建Image2Video提供商
3. 配置参数:
```python
执行器: core.ai_client.runway_i2v_client.RunwayI2VClient
API URL: https://api.runwayml.com/v1
API密钥: your-api-key
```

---

## 📚 更多资源

### 文档

- [Django 5.2升级文档](backend/DJANGO_5.2_UPGRADE.md)
- [部署文档](backend/docs/deployment/)
- [API文档](http://localhost:8010/api/schema/)

### 示例

- [Demo项目](#) - 内置示例项目
- [提示词模板示例](backend/apps/prompts/fixtures/)
- [配置示例](backend/config/settings/)

### 支持

- GitHub Issues: [提交问题](#)
- 文档反馈: [联系我们](#)
- 技术讨论: [加入社区](#)

---

## 🎉 开始创作

现在您已经掌握了基本操作，可以开始创作自己的AI故事视频了！

**推荐流程**:
1. ✅ 使用Demo项目熟悉系统
2. ✅ 创建测试项目验证配置
3. ✅ 优化提示词模板
4. ✅ 配置真实AI API
5. ✅ 开始正式创作

---

**祝您使用愉快！** 🎊

---

> 最后更新: 2026-01-29
> Django版本: 5.2.10 LTS
> 文档版本: v1.0
