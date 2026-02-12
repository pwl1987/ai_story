# 漫剧生成系统 - 最终设计文档 v3.1

> **最后更新:** 2026-02-11
> **状态:** 🎉 核心功能已完成 90% - 补充 Epic 12/13 中
> **版本:** v3.1 - 实现状态更新版

---

## 📌 版本更新说明

**v3.1 更新 (2026-02-11):**
- ✅ 标记所有已实现功能 (Epic 1-11)
- 📋 明确剩余待开发功能 (Epic 12/13)
- 📊 更新实施状态对照表

---

## 📊 实现状态总览

```
┌─────────────────────────────────────────────────────────┐
│ 🎉 AI Story 漫剧生成系统 - 实现状态                      │
├─────────────────────────────────────────────────────────┤
│ Epic 1-11   │ ✅ 100% 完成 (62 Stories)                 │
│ Epic 12     │ 🟡 待开发 - 章节推进工作流                  │
│ Epic 13     │ 🟡 待开发 - 转场与导出                      │
├─────────────────────────────────────────────────────────┤
│ 整体进度     │ 90% 完成 - 核心架构已就绪                  │
│ 生产就绪     │ 🟢 核心功能可用，补充工作流编排后完整        │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 项目定位

**项目类型:** 漫剧(动态漫画)生成平台
**核心功能:** 小说/剧本 → 漫剧视频自动化生成
**目标用户:** 漫画工作室、动画制作公司、短视频MCN

**核心工作流:** 文案改写 → 分镜生成 → 角色立绘 → 场景背景 → 漫剧画面 → 视频输出

---

## 一、核心概念层次

### 最终确定的结构

```
作品
 └─ 章节
     └─ 剧本场
         └─ 镜头
```

### 关键区分

| 英文 | 中文 | 说明 | 关系 | 实现状态 |
|------|------|------|------|---------|
| **ScriptScene** | **剧本场** | 故事单元 | 例如"纳米中心-日" | ✅ Epic 11.2 |
| **PhysicalScene** | **物理场景** | 环境类型(可复用) | 例如"实验室"模板 | ✅ Epic 10 |
| - | - | **关系** | 剧本场 → 继承 → 物理场景 | ✅ 已实现 |

---

## 二、功能模块定义

### 2.1 作品管理 (Artwork Management)

**功能状态:** ✅ **已实现** (Epic 10 + Epic 11)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 上传完整小说/剧本文件 | ✅ | `apps/artworks/models.py:70` |
| AI提炼全本故事情节 | ✅ | `apps/artworks/services/script_parser.py` |
| 自动划分章节 | ✅ | ScriptParserService |
| 作品元数据管理 | ✅ | Artwork Admin/API |

**数据模型:**
```python
class Artwork(models.Model):  # ✅ 已实现
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200)
    artwork_type = models.CharField(...)  # novel/script/webnovel/comic
    source_file = models.FileField(...)
    story_overview = models.TextField(blank=True)
    total_chapters = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=0)
    total_shots = models.IntegerField(default=0)
```

---

### 2.2 角色管理 (Character Management)

**功能状态:** ✅ **已实现** (Epic 11.1)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 角色档案管理 `CharacterProfile` | ✅ | `apps/artworks/models.py:244` |
| 角色造型管理 `CharacterPose` | ✅ | `apps/artworks/models.py:507` |
| 角色音色配置 `CharacterVoiceConfig` | ✅ | `apps/artworks/models.py:629` |
| 整合式UI展示 | ✅ | `frontend/src/components/artworks/` |
| 批量生成造型 | ✅ | Epic 11.1-4 |

**核心创新: 角色形象 + 音色整合**

#### 功能列表:

1. **角色档案管理** ✅
   - ✅ 提取全部人物角色信息
   - ✅ 按出现次数/重要性排序
   - ✅ 角色描述(外貌/性格/关系)

2. **角色造型管理** ✅
   - ✅ 全身立绘(默认造型)
   - ✅ 多套服装造型
   - ✅ AI自动提取造型
   - ✅ 造型类型 (casual/formal/battle/school/custom)

3. **角色音色配置** ✅
   - ✅ TTS引擎配置 (edge/elevenlabs/baidu)
   - ✅ 音色参数调整 (pitch/speed/volume)
   - ✅ 情感音色样本
   - ✅ 本地TTS (Edge-TTS) + 云端备份

4. **UI展示** ✅
   - ✅ 整合式卡片展示
   - ✅ 立绘预览
   - ✅ 音色试听
   - ✅ 造型切换

---

### 2.3 物理场景管理 (Physical Scene Management)

**功能状态:** ✅ **已实现** (Epic 10)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 物理场景模板 `PhysicalScene` | ✅ | `apps/artworks/models.py:305` |
| 剧本场景 `ScriptScene` | ✅ | `apps/artworks/models.py:388` |
| 首尾帧字段 | ✅ | `head_frame`, `tail_frame` |
| 转场配置字段 | ✅ | `transition_*` 系列 |

**概念区分:**
- **物理场景(PhysicalScene):** ✅ 可复用的环境类型模板
- **剧本场景(ScriptScene):** ✅ 具体的故事场景实例

**功能:**
- ✅ 提取场景信息
- ✅ 物理场景模板(可复用)
- ✅ 剧本场景(具体实例)
- ✅ 场景继承属性(光照/氛围)

---

### 2.4 物品管理 (Item Management)

**功能状态:** ⚠️ **部分实现**

| 功能 | 状态 | 备注 |
|------|------|------|
| 提取物品信息 | ✅ | ScriptParserService 支持 |
| 生成物品图片 | 🟡 | ComfyUI 可用，待集成 |
| 物品关联追踪 | ❌ | 待实现 (Epic 13) |

---

### 2.5 分镜排序功能 (Shot Sorting)

**功能状态:** ✅ **已实现** (Epic 11.2)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 时间轴视图 | ✅ | StoryboardEditor.vue |
| 拖拽排序 | ✅ | ShotList.vue (sortablejs) |
| 批量调整 | ✅ | BatchOperationsBar.vue |
| 批量生成图片 | ✅ | 批量操作 API |
| 批量配音 | ✅ | 批量操作 API |

---

### 2.6 首尾帧提取与转场 (Frame & Transition)

**功能状态:** 🟡 **数据模型已实现，服务待开发**

| 功能 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| 首尾帧字段 | ✅ | ScriptScene 模型 | Epic 11.2.1 |
| 转场配置字段 | ✅ | ScriptScene 模型 | Epic 11.2.1 |
| 自动提取首帧 | 🟡 | 待实现 | Epic 12.2 |
| 自动提取尾帧 | 🟡 | 待实现 | Epic 12.2 |
| 转场效果应用 | 🟡 | 待实现 | Epic 13.1 |

---

### 2.7 章节推进式工作流

**功能状态:** 🟡 **待实现** (Epic 12)

| 功能 | 状态 | 备注 |
|------|------|------|
| 按章节顺序处理 | 🟡 | 需要编排器 |
| 每场独立完成 | 🟡 | 需要状态机 |
| 支持暂停/继续 | 🟡 | 需要持久化 |
| 渐进式交付 | 🟡 | 需要导出功能 |

---

## 三、本地引擎集成方案 (v3.0 新增)

### 3.1 引擎架构

**功能状态:** ✅ **已实现** (Epic 10)

```
核心引擎层 (可插拔) ✅
├─ LLM Engine ✅
│  ├─ Local: OllamaClient (llama2/llama3/qwen) ✅ Epic 10.1
│  ├─ Cloud: OpenAIClient / ClaudeClient ✅ 已有
│  └─ Fallback: 云端备份 ✅ 已有
│
├─ Image Engine ✅
│  ├─ Local: ComfyUIClient (Stable Diffusion XL) ✅ Epic 10.3
│  ├─ Cloud: DALL-E / SD API ✅ 已有
│  └─ Fallback: 云端备份 ✅ 已有
│
└─ TTS Engine ✅
   ├─ Local: EdgeTTSProvider (免费) ✅ Epic 10.2
   ├─ Cloud: ElevenLabs / BaiduTTS ✅ 已有
   └─ Fallback: 云端备份 ✅ 已有
```

### 3.2 配置文件

**功能状态:** ✅ **已实现** (Epic 11.3)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 引擎配置模型 | ✅ | EngineConfiguration 等 4 个模型 |
| 主/备引擎配置 | ✅ | primary/fallback 字段 |
| 健康检查 | ✅ | EngineHealthCheckService |
| 配置 UI | ✅ | `/engines` 监控页面 |

### 3.3 成本对比

| 功能 | 云端API | 本地引擎 | 节省 | 实现状态 |
|------|---------|----------|------|---------|
| LLM | $0.002/1K tokens | $0 | ~100% | ✅ Epic 10.1 |
| Image | $0.04/张 | $0 | ~100% | ✅ Epic 10.3 |
| TTS | $0.03/1K字符 | $0 | ~100% | ✅ Epic 10.2 |
| **小项目** | **~$200** | **~$0** | **100%** | ✅ 已实现 |
| **大项目** | **~$2000** | **~$0** | **100%** | ✅ 已实现 |

---

## 四、完整工作流程

### 阶段0: 系统配置 (一次性)

**功能状态:** ✅ **已实现**

| 步骤 | 状态 | 实现位置 |
|------|------|---------|
| 安装本地引擎 | ✅ | Docker/文档 |
| 配置引擎参数 | ✅ | Epic 11.3 UI |
| 配置 Artwork | ✅ | Artwork 模型 |

### 阶段1: 作品创建与解析

**功能状态:** ✅ **已实现** (Epic 10.4)

| 步骤 | 状态 | 实现位置 |
|------|------|---------|
| 上传作品 | ✅ | Artwor
k API |
| AI智能解析 | ✅ | ScriptParserService |
| 识别章节边界 | ✅ | 自动解析 |
| 提取角色清单 | ✅ | CharacterProfile |
| 提取场景清单 | ✅ | PhysicalScene |
| 提取物品清单 | ✅ | ItemProfile |
| 生成作品概要 | ✅ | story_overview 字段 |

### 阶段2: 资产准备 (可复用)

**功能状态:** ✅ **已实现** (Epic 11.1)

| 步骤 | 状态 | 实现位置 |
|------|------|---------|
| 批量生成默认立绘 | ✅ | ComfyUI batch_generate |
| AI提取多套造型 | ✅ | CharacterPose 模型 |
| 配置角色音色 | ✅ | CharacterVoiceConfig |
| 保存到角色库 | ✅ | CharacterProfile 管理 |

### 阶段3: 剧本场景制作 (核心)

**功能状态:** 🟡 **部分实现**

| 步骤 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| 选择章节 | ✅ | Chapter API | |
| 选择剧本场 | ✅ | ScriptScene API | |
| AI生成分镜脚本 | ✅ | OllamaClient | Epic 10.1 |
| 完善分镜详情 | ✅ | Shot 编辑 UI | Epic 11.2 |
| 生成漫剧画面 | ✅ | ComfyUIService | Epic 10.3 |
| 合成语音 | ✅ | EdgeTTSClient | Epic 10.2 |
| 预览与调整 | ✅ | StoryboardEditor | Epic 11.2 |
| **提取首尾帧** | 🟡 | **待实现** | **Epic 12.2** |

### 阶段4: 章节完成与转场

**功能状态:** 🟡 **待实现** (Epic 13)

| 步骤 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| 章节转场配置 | 🟡 | 待实现 | **Epic 13.1** |
| 自动检测首尾帧 | 🟡 | 待实现 | **Epic 12.2** |
| 配置转场效果 | 🟡 | 待实现 | **Epic 13.1** |
| 预览转场 | 🟡 | 待实现 | **Epic 13.1** |
| **导出章节视频** | 🟡 | **待实现** | **Epic 13.2** |

---

## 五、数据模型实现状态

### 核心结构模型 ✅

| 模型 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| `Artwork` | ✅ | `apps/artworks/models.py:70` | |
| `Chapter` | ✅ | `apps/artworks/models.py:155` | |
| `ScriptScene` | ✅ | `apps/artworks/models.py:388` | Epic 11.2 增强 |
| `Shot` | ✅ | `apps/artworks/models.py:696` | Epic 11.2 增强 |

### 角色系统模型 ✅

| 模型 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| `CharacterProfile` | ✅ | `apps/artworks/models.py:244` | |
| `CharacterPose` | ✅ | `apps/artworks/models.py:507` | Epic 11.1 新增 |
| `CharacterVoiceConfig` | ✅ | `apps/artworks/models.py:629` | Epic 11.1 新增 |

### 物理场景模型 ✅

| 模型 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| `PhysicalScene` | ✅ | `apps/artworks/models.py:305` | Epic 10 新增 |
| `ScriptScene` | ✅ | `apps/artworks/models.py:388` | 首尾帧+转场 |

### 物品系统模型 🟡

| 模型 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| `ItemProfile` | ✅ | `apps/artworks/models.py` | 基础实现 |
| 物品关联追踪 | 🟡 | 待实现 | Epic 13 |

### 引擎配置模型 ✅

| 模型 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| `EngineConfiguration` | ✅ | `apps/artworks/models.py:749` | Epic 11.3 新增 |
| `GenerationProgress` | ✅ | `apps/artworks/models.py:837` | |
| `HealthCheckResult` | ✅ | `apps/artworks/models.py:883` | |

---

## 六、UI界面实现状态

### 6.1 角色管理界面

**功能状态:** ✅ **已实现** (Epic 11.1)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 整合式卡片展示 | ✅ | CharacterCard.vue |
| 立绘 + 音色 + 造型 | ✅ | 整合组件 |
| 造型预览和切换 | ✅ | PoseSelector.vue |
| 音色试听 | ✅ | VoicePlayer.vue |

### 6.2 引擎配置界面

**功能状态:** ✅ **已实现** (Epic 11.3)

| 功能 | 状态 | 实现位置 |
|------|------|---------|
| 主引擎 + 备份引擎配置 | ✅ | `/engines` 页面 |
| 实时状态监控 | ✅ | EngineMonitor.vue |
| Fallback策略设置 | ✅ | EngineDetailModal |
| 成本统计展示 | 🟡 | 部分实现 |

### 6.3 工作流优化界面

**功能状态:** 🟡 **部分实现**

| 功能 | 状态 | 实现位置 | 备注 |
|------|------|---------|------|
| 引擎状态实时显示 | ✅ | EngineMonitor | |
| 生成进度可视化 | ✅ | ProgressBar | Epic 11.4 |
| 错误处理和重试 | ✅ | 已有机制 | |
| 性能监控 | 🟡 | 基础实现 | |
| **章节工作室页面** | 🟡 | **待实现** | **Epic 12** |

---

## 七、实施计划更新

### ✅ Phase 1-4: 已完成 (Epic 1-11)

| Phase | 状态 | 完成时间 | 成就 |
|-------|------|---------|------|
| Phase 1: 核心集成 | ✅ | 2026-01-25~31 | Epic 1-9 |
| Phase 2: 漫剧系统 | ✅ | 2026-02-11 | Epic 10 |
| Phase 3: UI优化 | ✅ | 2026-02-10 | Epic 11 |

### 🟡 Phase 5: 待开发 (Epic 12-13)

| Epic | Stories | 预估时间 | 优先级 |
|------|---------|---------|--------|
| Epic 12: 章节推进工作流 | 3 | 1周 | P0 |
| Epic 13: 转场与导出 | 2 | 1周 | P0 |

---

## 八、剩余待开发功能清单

### Epic 12: 章节推进工作流 (P0)

| Story | 功能 | 预估时间 |
|-------|------|---------|
| 12-1 | 章节编排服务 | 3-5天 |
| 12-2 | 首尾帧自动提取服务 | 1-2天 |
| 12-3 | 章节工作室 UI | 2-3天 |

### Epic 13: 转场与导出 (P0)

| Story | 功能 | 预估时间 |
|-------|------|---------|
| 13-1 | 转场配置与预览 | 2-3天 |
| 13-2 | 视频合成与导出 | 3-5天 |

---

## 九、技术栈

### 后端 ✅
- Django 3.2.15
- DRF (API)
- Celery (异步任务)
- Redis (队列/缓存)
- Channels (WebSocket)
- Ollama (本地LLM) ✅ Epic 10.1
- ComfyUI (本地SD) ✅ Epic 10.3
- Edge-TTS (本地TTS) ✅ Epic 10.2

### 前端 ✅
- Vue 2.7.14
- Vuex (状态管理)
- daisyUI + Tailwind CSS

### 基础设施 ✅
- PostgreSQL
- Redis
- GPU Server (for ComfyUI)

---

## 十、命名规范

| 英文 | 中文 | 状态 |
|------|------|------|
| Artwork | 作品 | ✅ |
| Chapter | 章节 | ✅ |
| ScriptScene | 剧本场 | ✅ |
| Shot | 镜头 | ✅ |
| PhysicalScene | 物理场景 | ✅ |
| CharacterProfile | 角色档案 | ✅ |
| **CharacterPose** | **角色造型** | ✅ Epic 11.1 |
| **CharacterVoiceConfig** | **角色音色配置** | ✅ Epic 11.1 |
| ItemProfile | 物品档案 | ✅ |

---

## 十一、实现状态总结

### ✅ 已完成 (90%)

**核心架构:**
- ✅ 完整的数据模型层次
- ✅ 本地引擎集成 (Ollama/ComfyUI/Edge-TTS)
- ✅ 角色资产管理系统
- ✅ 分镜编辑器 (拖拽排序/批量操作)
- ✅ 引擎监控与配置
- ✅ 可视化进度系统

### 🟡 待完成 (10%)

**工作流编排:**
- 🟡 章节推进式工作流编排器 (Epic 12)
- 🟡 首尾帧自动提取服务 (Epic 12.2)
- 🟡 章节工作室页面 (Epic 12.3)

**导出功能:**
- 🟡 转场配置 UI (Epic 13.1)
- 🟡 视频合成与导出 (Epic 13.2)

---

**文档版本:** v3.1
**最后更新:** 2026-02-11
**状态:** 🎉 核心功能完成 90% - Epic 12/13 待开发
**下一步:** 创建 Epic 12 和 Epic 13 Stories
