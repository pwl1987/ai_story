# 漫剧生成系统 - 最终设计文档 v3.0

> **最后更新:** 2026-02-06
> **状态:** 讨论完成,准备开发
> **版本:** v3.0 - 集成本地LLM/TTS/ComfyUI

---

## 📌 文档说明

本文档记录了漫剧(动态漫画)生成系统的完整设计,包括:
- 核心概念层次
- 功能模块定义
- 数据模型设计
- UI界面设计
- 工作流程
- 技术实现方案
- 本地引擎集成方案

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

| 英文 | 中文 | 说明 | 关系 |
|------|------|------|------|
| **ScriptScene** | **剧本场** | 故事单元 | 例如"纳米中心-日" |
| **PhysicalScene** | **物理场景** | 环境类型(可复用) | 例如"实验室"模板 |
| - | - | **关系** | 剧本场 → 继承 → 物理场景 |

---

## 二、功能模块定义

### 2.1 作品管理 (Artwork Management)

**功能:**
- ✅ 上传完整小说/剧本文件
- ✅ AI提炼全本故事情节
- ✅ 自动划分章节
- ✅ 作品元数据管理

**数据模型:**
```python
class Artwork(models.Model):
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

### 2.2 角色管理 (Character Management) - 整合版

**核心创新: 角色形象 + 音色整合**

#### 功能列表:

1. **角色档案管理**
   - ✅ 提取全部人物角色信息
   - ✅ 按出现次数/重要性排序
   - ✅ 角色描述(外貌/性格/关系)

2. **角色造型管理** (CharacterPose - 新增)
   - ✅ 全身立绘(默认造型)
   - ✅ 多套服装造型
   - ✅ AI自动提取造型
   - ✅ 家庭装、宴会装、战斗装等
   - ✅ 适应不同场景需求

3. **角色音色配置** (CharacterVoiceConfig - 新增)
   - ✅ TTS引擎配置
   - ✅ 音色参数调整
   - ✅ 情感音色样本
   - ✅ 本地TTS (Edge-TTS) + 云端备份 (ElevenLabs)

4. **UI展示**
   - ✅ 整合式卡片展示
   - ✅ 立绘预览
   - ✅ 音色试听
   - ✅ 造型切换

**数据模型:**
```python
class CharacterProfile(models.Model):
    """角色档案"""
    artwork = models.ForeignKey(Artwork, ...)
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)

    # 统计
    appearance_count = models.IntegerField(default=0)
    dialogue_count = models.IntegerField(default=0)

    # AI描述
    description = models.TextField(blank=True)
    personality = models.TextField(blank=True)

    # 引擎偏好
    preferred_llm_engine = models.CharField(max_length=50, default='ollama')
    preferred_tts_engine = models.CharField(max_length=50, default='edge')
    preferred_image_engine = models.CharField(max_length=50, default='comfyui')

class CharacterPose(models.Model):
    """角色造型 - 同一角色的多套服装"""
    character = models.ForeignKey(CharacterProfile, ...)

    pose_name = models.CharField(max_length=200)  # "家庭装", "宴会装"
    pose_type = models.CharField(...)  # casual/formal/battle/school/custom
    pose_image = models.ImageField(upload_to='characters/poses/')

    # 适用场景
    suitable_for_scenes = models.JSONField(default=list)  # ["家", "宴会"]

    # AI提取信息
    extraction_source = models.CharField(max_length=50, blank=True)
    extracted_from_chapter = models.IntegerField(null=True)
    description = models.TextField(blank=True)

    # 使用统计
    usage_count = models.IntegerField(default=0)

class CharacterVoiceConfig(models.Model):
    """角色音色配置"""
    character = models.OneToOneField(CharacterProfile, ...)

    # TTS引擎
    tts_engine = models.CharField(...)  # elevenlabs/edge/baidu
    voice_id = models.CharField(max_length=100, blank=True)

    # 音色参数
    voice_type = models.CharField(max_length=100, blank=True)
    pitch = models.CharField(max_length=20, default='normal')
    speed = models.CharField(max_length=20, default='normal')
    volume = models.CharField(max_length=20, default='normal')

    # 情感配置
    emotion_mode = models.CharField(max_length=50, blank=True)
    emotion_intensity = models.CharField(max_length=20, default='medium')

    # 情感音色映射
    emotion_voices = models.JSONField(default=dict)

    # 试听样本
    voice_sample_url = models.URLField(blank=True)
```

---

### 2.3 物理场景管理 (Physical Scene Management)

**概念区分:**
- **物理场景(PhysicalScene):** 可复用的环境类型模板
- **剧本场景(ScriptScene):** 具体的故事场景实例

**功能:**
- ✅ 提取场景信息
- ✅ 物理场景模板(可复用)
- ✅ 剧本场景(具体实例)
- ✅ 生成场景概念图
- ✅ 场景继承属性(光照/氛围)

**数据模型:**
```python
class PhysicalScene(models.Model):
    """物理场景模板"""
    category = models.CharField(...)  # living_room/laboratory/street
    name = models.CharField(max_length=200)  # "现代实验室"
    default_lighting = models.CharField(max_length=50, blank=True)
    default_atmosphere = models.CharField(max_length=50, blank=True)

    background_image = models.ImageField(upload_to='physical_scenes/', blank=True)
    prompt_template = models.TextField(blank=True)

    is_system_template = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)

class ScriptScene(models.Model):
    """剧本场景 - 具体实例"""
    chapter = models.ForeignKey(Chapter, ...)
    physical_scene = models.ForeignKey(PhysicalScene, ...)  # 继承模板

    scene_number = models.IntegerField()
    scene_name = models.CharField(max_length=200)
    description = models.TextField()

    # 覆盖模板属性
    atmosphere = models.CharField(max_length=50, blank=True)
    time_of_day = models.CharField(max_length=50, blank=True)
    weather = models.CharField(max_length=50, blank=True)

    # 首尾帧 (新增)
    head_frame = models.ImageField(upload_to='scenes/heads/', blank=True)
    tail_frame = models.ImageField(upload_to='scenes/tails/', blank=True)

    # 转场配置 (新增)
    transition_to_next = models.ForeignKey('self', ...)
    transition_type = models.CharField(max_length=20, blank=True)
    transition_duration = models.FloatField(default=1.5)
```

---

### 2.4 物品管理 (Item Management)

**功能:**
- ✅ 提取物品信息
- ✅ 生成常用物品图片
- ✅ 物品关联追踪

---

### 2.5 分镜排序功能 (Shot Sorting)

**功能:**
- ✅ 时间轴视图
- ✅ 拖拽排序
- ✅ 批量调整
- ✅ AI智能排序(情感递进)

---

### 2.6 首尾帧提取与转场 (Frame & Transition)

**功能:**
- ✅ 自动提取场景首帧(第一镜)
- ✅ 自动提取场景尾帧(最后一镜)
- ✅ 剧本场间转场配置
- ✅ 章节间转场配置

---

### 2.7 章节推进式工作流

**特点:**
- ✅ 按章节顺序处理
- ✅ 每场独立完成
- ✅ 支持暂停/继续
- ✅ 渐进式交付

---

## 三、本地引擎集成方案 (v3.0 新增)

### 3.1 引擎架构

```
核心引擎层 (可插拔)
├─ LLM Engine
│  ├─ Local: OllamaClient (llama2/llama3/qwen)
│  ├─ Cloud: OpenAIClient / ClaudeClient
│  └─ Fallback: 云端备份
│
├─ Image Engine
│  ├─ Local: ComfyUIClient (Stable Diffusion XL)
│  ├─ Cloud: DALL-E / SD API
│  └─ Fallback: 云端备份
│
└─ TTS Engine
   ├─ Local: EdgeTTSProvider (免费)
   ├─ Cloud: ElevenLabs / BaiduTTS
   └─ Fallback: 云端备份
```

### 3.2 配置文件

```yaml
# config/engines.yaml

llm:
  primary:
    provider: ollama
    config:
      base_url: http://localhost:11434
      model: llama2:7b
      temperature: 0.7
      max_tokens: 2000
  fallback:
    provider: openai
    config:
      api_key: ${OPENAI_API_KEY}
      model: gpt-4

image:
  primary:
    provider: comfyui
    config:
      base_url: http://localhost:8188
      model: sdxl_base
  fallback:
    provider: openai
    config:
      api_key: ${OPENAI_API_KEY}
      model: dall-e-3

tts:
  primary:
    provider: edge
    config:
      voice_name: zh-CN-XiaoxiaoNeural
  fallback:
    provider: elevenlabs
    config:
      api_key: ${ELEVENLABS_API_KEY}
```

### 3.3 成本对比

| 功能 | 云端API | 本地引擎 | 节省 |
|------|---------|----------|------|
| LLM | $0.002/1K tokens | $0 | ~100% |
| Image | $0.04/张 | $0 | ~100% |
| TTS | $0.03/1K字符 | $0 | ~100% |
| **小项目** | **~$200** | **~$0** | **100%** |
| **大项目** | **~$2000** | **~$0** | **100%** |

**硬件投入:** GPU服务器 (~$2000-3000 一次性)

---

## 四、完整工作流程

### 阶段0: 系统配置 (一次性)

```
Step 0.1: 安装本地引擎
  ├─ 安装Ollama: docker run ollama/ollama
  ├─ 下载模型: ollama pull llama2:7b
  ├─ 安装ComfyUI
  ├─ 安装Edge-TTS: pip install edge-tts
  └─ 测试所有引擎连接

Step 0.2: 配置引擎参数
  ├─ 选择主引擎和备份引擎
  ├─ 配置Fallback机制
  └─ 测试引擎可用性

Step 0.3: 配置Artwork
  └─ 选择默认引擎策略
```

### 阶段1: 作品创建与解析

```
Step 1.1: 上传作品
  └─ 上传小说/剧本文件

Step 1.2: AI智能解析 (本地LLM - Ollama)
  ├─ 识别章节边界
  ├─ 提取角色清单
  ├─ 提取场景清单
  ├─ 提取物品清单
  └─ AI提取角色造型 (新增!)
     ├─ 分析场景描述
     ├─ 识别服装关键词
     └─ 推荐造型类型

Step 1.3: 生成作品概要
```

### 阶段2: 资产准备 (可复用)

```
Step 2.1: 角色资产准备
  ├─ 批量生成默认立绘 (ComfyUI本地)
  ├─ AI提取多套造型 (Ollama分析 + ComfyUI生成)
  │  ├─ 家庭装
  │  ├─ 宴会装
  │  ├─ 战斗装
  │  └─ 实验服
  ├─ 配置角色音色 (Edge-TTS本地)
  └─ 保存到角色库

Step 2.2: 场景资产准备
  ├─ 批量生成场景背景 (ComfyUI本地)
  └─ 保存到场景库

Step 2.3: 物品资产准备
  ├─ 生成物品图片 (ComfyUI本地)
  └─ 保存到物品库
```

### 阶段3: 剧本场景制作 (核心)

```
Step 3.1: 选择章节

Step 3.2: 选择剧本场
  ├─ 从角色库选择角色 (含多套造型)
  └─ 从场景库选择场景

Step 3.3: AI生成分镜脚本 (本地LLM)
  └─ 快速生成,无等待

Step 3.4: 完善分镜详情
  ├─ 选择角色造型 (默认/宴会装/战斗装等)
  ├─ 配置对话/旁白
  ├─ 选择音色 (Edge-TTS本地)
  └─ 配置运镜效果

Step 3.5: 生成漫剧画面 (ComfyUI本地)
  ├─ 自动应用角色立绘
  ├─ 自动应用场景背景
  ├─ 自动添加对话气泡
  └─ 自动添加运镜效果

Step 3.6: 合成语音 (Edge-TTS本地)
  └─ 为所有对话生成语音

Step 3.7: 预览与调整

Step 3.8: 提取首尾帧
  ├─ 自动提取首帧(第一镜)
  └─ 自动提取尾帧(最后一镜)
```

### 阶段4: 章节完成与转场

```
Step 4.1: 章节转场配置
  ├─ 自动检测首尾帧
  ├─ 配置转场效果 (fade/dissolve/wipe)
  └─ 预览转场

Step 4.2: 导出章节视频
  ├─ 拼接所有场景
  ├─ 应用转场效果
  └─ 导出最终视频
```

---

## 五、数据模型 (完整版)

```python
# ============ 核心结构 ============

class Artwork(models.Model):
    """作品"""
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200)
    artwork_type = models.CharField(...)
    source_file = models.FileField(...)
    story_overview = models.TextField(blank=True)

    # 引擎配置
    preferred_llm_engine = models.CharField(max_length=50, default='ollama')
    preferred_image_engine = models.CharField(max_length=50, default='comfyui')
    preferred_tts_engine = models.CharField(max_length=50, default='edge')

class Chapter(models.Model):
    """章节"""
    artwork = models.ForeignKey(Artwork, ...)
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=500)
    original_text = models.TextField()
    plot_summary = models.TextField(blank=True)

class ScriptScene(models.Model):
    """剧本场景"""
    chapter = models.ForeignKey(Chapter, ...)
    physical_scene = models.ForeignKey(PhysicalScene, ...)

    scene_number = models.IntegerField()
    scene_name = models.CharField(max_length=200)
    description = models.TextField()

    # 覆盖属性
    atmosphere = models.CharField(max_length=50, blank=True)
    time_of_day = models.CharField(max_length=50, blank=True)

    # 首尾帧
    head_frame = models.ImageField(upload_to='scenes/heads/', blank=True)
    tail_frame = models.ImageField(upload_to='scenes/tails/', blank=True)

    # 转场
    transition_to_next = models.ForeignKey('self', ...)
    transition_type = models.CharField(max_length=20, blank=True)
    transition_duration = models.FloatField(default=1.5)

class Shot(models.Model):
    """镜头"""
    script_scene = models.ForeignKey(ScriptScene, ...)

    shot_number = models.IntegerField()
    shot_type = models.CharField(...)  # wide/medium/close-up
    visual_description = models.TextField()
    duration_seconds = models.FloatField()

    # 对话
    dialogue = models.TextField(blank=True)
    character_name = models.CharField(max_length=100, blank=True)
    dialogue_type = models.CharField(max_length=20, blank=True)

    # 关联资源
    character_pose = models.ForeignKey('CharacterPose', ...)

    # 生成状态
    generated_image = models.ImageField(upload_to='shots/', blank=True)
    generated_audio = models.FileField(upload_to='audio/', blank=True)

    # 运镜
    camera_movement = models.CharField(max_length=50, blank=True)

    # 首尾帧标记
    is_head_frame = models.BooleanField(default=False)
    is_tail_frame = models.BooleanField(default=False)

# ============ 角色系统 ============

class CharacterProfile(models.Model):
    """角色档案"""
    artwork = models.ForeignKey(Artwork, ...)
    name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)

    appearance_count = models.IntegerField(default=0)
    dialogue_count = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    personality = models.TextField(blank=True)

class CharacterPose(models.Model):
    """角色造型"""
    character = models.ForeignKey(CharacterProfile, ...)

    pose_name = models.CharField(max_length=200)
    pose_type = models.CharField(...)  # casual/formal/battle
    pose_image = models.ImageField(upload_to='characters/poses/')

    suitable_for_scenes = models.JSONField(default=list)
    extraction_source = models.CharField(max_length=50, blank=True)
    extracted_from_chapter = models.IntegerField(null=True)
    description = models.TextField(blank=True)

    usage_count = models.IntegerField(default=0)

class CharacterVoiceConfig(models.Model):
    """角色音色配置"""
    character = models.OneToOneField(CharacterProfile, ...)

    tts_engine = models.CharField(...)  # elevenlabs/edge/baidu
    voice_id = models.CharField(max_length=100, blank=True)

    voice_type = models.CharField(max_length=100, blank=True)
    pitch = models.CharField(max_length=20, default='normal')
    speed = models.CharField(max_length=20, default='normal')
    volume = models.CharField(max_length=20, default='normal')

    emotion_mode = models.CharField(max_length=50, blank=True)
    emotion_voices = models.JSONField(default=dict)

    voice_sample_url = models.URLField(blank=True)

# ============ 物理场景系统 ============

class PhysicalScene(models.Model):
    """物理场景模板"""
    category = models.CharField(...)  # living_room/laboratory
    name = models.CharField(max_length=200)
    default_lighting = models.CharField(max_length=50, blank=True)
    default_atmosphere = models.CharField(max_length=50, blank=True)

    background_image = models.ImageField(upload_to='physical_scenes/', blank=True)
    prompt_template = models.TextField(blank=True)

    is_system_template = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)

# ============ 物品系统 ============

class ItemProfile(models.Model):
    """物品档案"""
    artwork = models.ForeignKey(Artwork, ...)
    name = models.CharField(max_length=200)
    item_type = models.CharField(...)
    item_image = models.ImageField(upload_to='items/', blank=True)
    appearance_count = models.IntegerField(default=0)
    description = models.TextField(blank=True)

# ============ 引擎配置 ============

class EngineConfig(models.Model):
    """引擎配置"""
    engine_type = models.CharField(...)  # llm/image/tts
    primary_provider = models.CharField(max_length=50)
    primary_config = models.JSONField(default=dict)

    fallback_provider = models.CharField(max_length=50, blank=True)
    fallback_config = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    health_status = models.CharField(max_length=20, default='unknown')
    last_check = models.DateTimeField(auto_now=True)

    total_requests = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    avg_response_time = models.FloatField(default=0.0)
```

---

## 六、UI界面设计要点

### 6.1 角色管理界面

**特点:**
- 整合式卡片展示
- 立绘 + 音色 + 造型一体化
- 造型预览和切换
- 音色试听

### 6.2 引擎配置界面

**特点:**
- 主引擎 + 备份引擎配置
- 实时状态监控
- Fallback策略设置
- 成本统计展示

### 6.3 工作流优化界面

**特点:**
- 引擎状态实时显示
- 生成进度可视化
- 错误处理和重试
- 性能监控

---

## 七、实施计划

### Phase 1: 核心集成 (2周)
- Week 1: 本地LLM集成 (Ollama)
- Week 2: 本地TTS集成 (Edge-TTS)

### Phase 2: ComfyUI集成 (2周)
- Week 3: ComfyUI基础集成
- Week 4: 优化与测试

### Phase 3: UI优化 (1周)
- Week 5: 引擎配置UI

### Phase 4: 测试与优化 (1周)
- Week 6: 集成测试 + 性能优化

---

## 八、技术栈总结

### 后端
- Django 3.2.15
- DRF (API)
- Celery (异步任务)
- Redis (队列/缓存)
- Channels (WebSocket)
- Ollama (本地LLM)
- ComfyUI (本地SD)
- Edge-TTS (本地TTS)

### 前端
- Vue 2.7.14
- Vuex (状态管理)
- daisyUI + Tailwind CSS

### 基础设施
- PostgreSQL
- Redis
- GPU Server (for ComfyUI)

---

## 九、命名规范

| 英文 | 中文 | 说明 |
|------|------|------|
| Artwork | 作品 | 顶层容器 |
| Chapter | 章节 | 中层划分 |
| ScriptScene | 剧本场 | 故事单元 |
| Shot | 镜头 | 最小单位 |
| PhysicalScene | 物理场景 | 环境类型 |
| CharacterProfile | 角色档案 | 角色信息 |
| **CharacterPose** | **角色造型** | **同角色多套服装** |
| **CharacterVoiceConfig** | **角色音色配置** | **语音配置** |
| ItemProfile | 物品档案 | 道具信息 |

---

## 十、待开发功能清单

### P0 (核心功能 - 必须实现)
- [ ] Artwork CRUD
- [ ] Chapter AI解析
- [ ] CharacterPose CRUD (角色造型)
- [ ] CharacterVoiceConfig CRUD (音色配置)
- [ ] ScriptScene CRUD (剧本场景)
- [ ] Shot CRUD (镜头)
- [ ] 首尾帧提取
- [ ] 转场配置

### P1 (重要功能)
- [ ] OllamaClient集成
- [ ] EdgeTTSProvider集成
- [ ] ComfyUIClient集成
- [ ] Fallback机制
- [ ] AI提取角色造型

### P2 (增强功能)
- [ ] 智能造型推荐
- [ ] 情感音色映射
- [ ] 口型同步(基础版)

---

**文档版本:** v3.0
**最后更新:** 2026-02-06
**状态:** 准备开发
