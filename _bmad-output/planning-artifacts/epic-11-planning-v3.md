# Epic 11: 流程和UI优化 - 完整规划文档

> **创建日期:** 2026-02-06
> **最后更新:** 2026-02-06 14:30 (Party Mode Round 5)
> **状态:** 📋 规划中
> **版本:** v3.0 (基于 Party Mode Round 1-5 讨论)
> **预计工期:** 5周
> **Story数量:** 25个 (5个Sub-Epic)

---

## 📋 文档版本历史

| 版本 | 日期 | 更新内容 | 更新人 |
|------|------|---------|--------|
| v1.0 | 2026-02-06 | Party Mode Round 1-3 基础方案 | Mary/Winston/Sally/Amelia |
| v2.0 | 2026-02-06 | Party Mode Round 4 UI/UX优化 | Round 4 专家团队 |
| **v3.0** | **2026-02-06** | **Party Mode Round 5 多维度优化** | **Round 5 专家团队** |

**备注:** 本文档为可迭代规划文档,后续 Party Mode 讨论将继续更新此文档。

---

## 📋 目录

- [概述](#概述)
- [业务价值](#业务价值)
- [主人工作流程和关键决策](#主人工作流程和关键决策)
- [Sub-Epic 11.1: 资源管理系统](#sub-epic-111-资源管理系统)
- [Sub-Epic 11.2: 层级式创作工作流](#sub-epic-112-层级式创作工作流)
- [Sub-Epic 11.3: 引擎监控与配置](#sub-epic-113-引擎监控与配置)
- [Sub-Epic 11.4: 可视化进度系统](#sub-epic-114-可视化进度系统)
- [Sub-Epic 11.5: 批量操作和版本管理](#sub-epic-115-批量操作和版本管理) **[Round 4新增]**
- [多维度优化方案](#多维度优化方案) **[Round 5新增]**
- [实施计划](#实施计划)
- [成功标准](#成功标准)

---

## 概述

### 背景

当前AI Story系统已完成核心功能开发(Epic 1-9),并基于设计文档v3.0确定了漫剧生成的核心数据模型。但针对"漫剧(动态漫画)生成"这一特定场景,仍存在以下流程和UI方面的痛点:

**痛点识别 (来自Party Mode Round 1-5讨论):**

1. **资源管理分散**
   - 角色资产(立绘、服装、音色)分散在不同界面,缺少统一管理
   - 同一角色有多套服装(家庭装、宴会装、战斗装等),缺少切换机制
   - 场景背景和物理场景缺少复用机制
   - 物品道具管理缺失

2. **工作流不直观**
   - 缺少章节 → 场景 → 分镜的层级式导航
   - 多步骤操作缺少引导,用户容易迷失
   - AI生成和手动创建模式没有清晰区分

3. **UI操作体验差**
   - 单页面显示内容过多,信息密度过高
   - 缺少双栏布局(目录树 + 工作区)
   - 目录树行为不一致
   - 缺少面包屑导航和快速切换

4. **引擎状态不可见**
   - 本地引擎(Ollama/ComfyUI/Edge-TTS)状态无监控
   - Fallback机制不可见
   - 成本统计缺失

5. **错误处理不友好** **[Round 5新增]**
   - AI生成失败时缺少降级策略
   - 批量操作部分失败时缺少详细错误报告
   - 用户不知道如何恢复错误

6. **性能问题** **[Round 5新增]**
   - 大型作品(100+场景)目录树加载缓慢
   - 图像加载阻塞界面
   - API响应慢

7. **用户学习曲线陡峭** **[Round 5新增]**
   - 复杂工作流缺少引导
   - 缺少上下文帮助
   - 新手上手困难

### 目标

Epic 11旨在通过以下改进提升用户体验和工作效率:

1. **建立统一的资源管理系统**
   - 整合角色、场景、物品资源于一体
   - 支持多套造型管理和智能推荐
   - 提供资源复用和配置界面

2. **实现层级式创作工作流**
   - 双栏布局:左侧目录树 + 右侧工作区
   - 章节 → 场景 → 分镜三级导航
   - AI生成模式与手动创建模式共存
   - 面包屑导航和快速切换

3. **增强引擎可观测性**
   - 实时监控本地引擎状态
   - 可视化Fallback机制
   - 统计成本和性能指标

4. **提升进度可视化**
   - 章节推进式工作流UI
   - 实时进度条和状态标识
   - 友好的错误处理和重试

5. **优化错误处理和性能** **[Round 5新增]**
   - 智能降级机制(本地→云端→手动)
   - 详细的错误报告和恢复建议
   - 懒加载、虚拟滚动等性能优化

6. **完善用户引导系统** **[Round 5新增]**
   - 交互式引导流程
   - 上下文帮助文档
   - 键盘快捷键支持

### 范围

**包含:**
- 资源管理系统 (角色/场景/物品)
- 层级式创作工作流 (双栏布局 + 目录树 + 面包屑)
- 引擎监控与配置 (健康检查 + 成本统计)
- 可视化进度系统 (章节推进UI + 进度条)
- 批量操作功能 **[Round 4新增]**
- 历史版本管理 **[Round 4新增]**
- 错误处理和降级机制 **[Round 5新增]**
- 性能优化(懒加载、缓存) **[Round 5新增]**
- 用户引导系统 **[Round 5新增]**
- 可访问性支持 **[Round 5新增]**
- 数据导入导出 **[Round 5新增]**

**不包含:**
- 全新的AI模型集成 (由Epic 10负责)
- 视频编辑功能 (由Epic 13负责)
- 多用户协作功能 (由Epic 14负责)

---

## 业务价值

### 用户价值

| 价值维度 | 改进前 | 改进后 | 提升 |
|---------|--------|--------|------|
| **资源管理效率** | 分散查找资源,需5分钟/次 | 统一界面管理,30秒/次 | **10倍** |
| **工作流导航效率** | 多页面跳转,需10次点击/场景 | 目录树导航,2次点击/场景 | **5倍** |
| **引擎故障排查** | 手动检查,需20分钟 | 实时监控面板,即时 | **10倍** |
| **进度感知** | 不知道还要等多久 | 实时进度条+预估时间 | **即时** |
| **错误恢复** | 失败后不知道怎么办 | 智能降级+错误报告 | **自动** |
| **大型作品性能** | 100场景加载10秒 | 懒加载,0.5秒 | **20倍** |

### 业务价值

1. **降低创作门槛**: 新用户通过引导2分钟快速上手
2. **提升创作效率**: 批量操作和快速切换节省50%时间
3. **减少技术债务**: 性能优化支持更大规模作品
4. **增强系统可靠性**: 智能降级保障创作流程不中断

---

## 主人工作流程和关键决策

### 完整工作流程 (基于主人描述)

```
起点: 上传剧本/小说
   ↓
阶段1: AI自动解析
   ├─ 识别章节边界
   ├─ 提取角色清单
   ├─ 提取场景清单
   ├─ 提取物品清单
   └─ 生成作品概要
   ↓
┌─────────────────────────────────────┐
│  两大核心模块                        │
├─────────────────────────────────────┤
│ 1. 资源管理 (保障一致性)             │
│    - 角色: 立绘 + 多套着装 + 音色   │
│    - 场景: 背景、光照、氛围          │
│    - 物品: 道具                      │
│    - 对话: 台词库                    │
├─────────────────────────────────────┤
│ 2. 创作流程 (三级层级)               │
│    章节 → 剧本场景 → 分镜头          │
│    (Chapter) → (Scene) → (Shot)     │
└─────────────────────────────────────┘
   ↓
阶段2: 章节级别规划
   ├─ 显示章节概要
   ├─ AI自动生成场景列表 (或手动创建)
   ├─ 配置出场角色
   └─ 管理场景顺序
   ↓
阶段3: 场景级别编辑
   ├─ 显示场景描述
   ├─ AI自动生成分镜列表 (或手动创建)
   ├─ 为每个分镜选择角色和造型
   └─ 配置运镜效果
   ↓
阶段4: 分镜级别生成
   ├─ 编辑对话和运镜
   ├─ 生成画面 (ComfyUI)
   ├─ 合成语音 (Edge-TTS)
   └─ 预览与调整
```

### UI结构 (主人描述)

```
┌─────────────────────┬──────────────────────────┐
│  左侧: 目录树       │  右侧: 功能区            │
│  📁 作品            │  [根据选中项动态变化]    │
│    📁 章节1         │                          │
│      📁 场景1.1     │  → 章节视图:             │
│      📁 场景1.2     │     · 概要               │
│    📁 章节2         │     · 生成场景           │
│      📁 场景2.1     │     · 管理场景           │
│        📁 分镜1    │                          │
│        📁 分镜2    │  → 场景视图:             │
│               │     · 场景描述            │
│               │     · 出场角色            │
│               │     · 生成分镜            │
└──────────────┴──────────────────────────┘
```

### 关键决策记录

**Round 1 - 基础决策:**

| 决策点 | 选项 | 主人选择 | 说明 |
|--------|------|---------|------|
| 资源复用策略 | A.自动更新<br>B.询问用户<br>C.创建副本 | **A** | 修改角色造型后,自动更新所有使用该造型的分镜 |
| AI生成模式 | A.AI推荐<br>B.手动创建<br>C.两者都支持 | **C** | AI推荐模式和手动创建模式都支持 |
| 目录树行为 | A.智能折叠<br>B.始终展开<br>C.可手动折叠 | **C** | 目录树可手动折叠/展开,最灵活 |

**Round 4 - UI增强决策:**

| 决策点 | 选项 | 主人选择 | 说明 |
|--------|------|---------|------|
| 面包屑导航 | A.必须做<br>B.可有可无<br>C.不需要 | **A** | 顶部面包屑+上一/下一场景切换,P0优先级 |
| 批量操作 | A.P0必须<br>B.P1最好<br>C.P2后续 | **B** | 批量删除/生成/移动,P1优先级 |
| 历史版本管理 | A.需要<br>B.暂时不需要<br>C.简化版 | **A** | 支持分镜回溯到历史版本 |
| 实施周期 | A.4周核心<br>B.砍功能<br>C.5周包含增强 | **C** | 延长到5周,包含增强功能 |

**Round 5 - 多维度决策:**

| 决策点 | 主人选择 | 说明 |
|--------|---------|------|
| 错误处理/降级 | **都需要** | 智能降级机制、错误报告系统 |
| 性能优化 | **都需要** | 懒加载、虚拟滚动、缓存策略 |
| 用户引导 | **都需要** | 交互式引导、上下文帮助 |
| 可访问性 | **都需要** | 键盘导航、屏幕阅读器 |
| 数据导入导出 | **都需要** | 多格式导入/导出 |

---

## Sub-Epic 11.1: 资源管理系统

### 目标

建立统一的角色、场景、物品资源管理系统,保障作品一致性。

### 用户故事

**Story 11.1.1: 角色资产统一管理**

```
作为 漫剧创作者
我想要 在一个界面管理角色的所有造型和音色
以便 保障角色在不同场景中的一致性

AC:
- ✅ 可以上传角色的默认立绘
- ✅ 可以为同一角色添加多套服装造型
  · 支持造型命名(家庭装/宴会装/战斗装等)
  · 支持设置适用场景
  · 支持造型预览
- ✅ 可以为角色配置TTS音色和参数
  · 选择TTS引擎(Edge-TTS/ElevenLabs)
  · 调整音色参数(语速/音调/音量)
  · 试听音色效果
- ✅ 修改角色造型后,自动更新所有使用该造型的分镜
  · 弹窗提示影响的分镜数量
  · 后台异步重新生成
- ✅ 显示角色使用统计(出现次数/分镜数)

优先级: P0 (核心功能)
工作量: 2天
```

**Story 11.1.2: 场景资产库**

```
作为 漫剧创作者
我想要 创建可复用的场景模板
以便 在多个剧本场景中保持环境一致

AC:
- ✅ 可以创建物理场景模板
  · 场景分类(实验室/客厅/街道等)
  · 默认光照(早晨/傍晚/夜晚)
  · 默认氛围(紧张/温馨/神秘)
- ✅ 可以为场景上传背景图
  · 支持图片裁剪和调整
  · 支持多张背景图(不同角度)
- ✅ 可以配置场景的Prompt模板
  · 为ComfyUI生成配置参数
  · 支持变量插值(如{{time_of_day}})
- ✅ 剧本场景可以继承物理场景
  · 自动应用场景属性
  · 可以覆盖特定属性

优先级: P0
工作量: 1.5天
```

**Story 11.1.3: 物品资产管理**

```
作为 漫剧创作者
我想要 管理道具物品的图片和属性
以便 在分镜中快速引用

AC:
- ✅ 可以上传物品图片
- ✅ 可以配置物品属性
  · 物品名称
  · 物品分类(武器/装饰/日常用品等)
  · 描述文本
- ✅ 显示物品使用统计
  · 出现次数
  · 关联分镜列表

优先级: P1
工作量: 1天
```

**Story 11.1.4: AI智能推荐造型**

```
作为 漫剧创作者
我想要 AI根据场景描述智能推荐角色造型
以便 减少手动选择时间

AC:
- ✅ 分析场景描述,识别场景类型(宴会/战斗等)
- ✅ 根据场景类型,推荐合适的造型
- ✅ 显示推荐理由("检测到'宴会'关键词,推荐宴会装")
- ✅ 用户可以一键应用推荐
- ✅ 用户可以忽略推荐,手动选择

优先级: P2
工作量: 2天
```

### 数据模型

```python
# 角色档案
class CharacterProfile(models.Model):
    """角色档案"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)  # "刘备"
    display_name = models.CharField(max_length=200)  # 显示名称

    # 统计
    appearance_count = models.IntegerField(default=0)  # 出现场次数
    dialogue_count = models.IntegerField(default=0)  # 对话数

    # AI描述
    description = models.TextField(blank=True)  # 角色描述
    personality = models.TextField(blank=True)  # 性格特点

    # 引擎偏好
    preferred_llm_engine = models.CharField(max_length=50, default='ollama')
    preferred_tts_engine = models.CharField(max_length=50, default='edge')
    preferred_image_engine = models.CharField(max_length=50, default='comfyui')

# 角色造型 (同一角色的多套服装)
class CharacterPose(models.Model):
    """角色造型"""
    character = models.ForeignKey(CharacterProfile, on_delete=models.CASCADE)

    pose_name = models.CharField(max_length=200)  # "宴会装"
    pose_type = models.CharField(max_length=50)  # casual/formal/battle/school/custom
    pose_image = models.ImageField(upload_to='characters/poses/')

    # 适用场景
    suitable_for_scenes = models.JSONField(default=list)  # ["家", "宴会"]

    # AI提取信息
    extraction_source = models.CharField(max_length=50, blank=True)
    extracted_from_chapter = models.IntegerField(null=True)
    description = models.TextField(blank=True)

    # 使用统计
    usage_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "角色造型"
        verbose_name_plural = "角色造型"

# 角色音色配置
class CharacterVoiceConfig(models.Model):
    """角色音色配置"""
    character = models.OneToOneField(CharacterProfile, on_delete=models.CASCADE)

    # TTS引擎
    tts_engine = models.CharField(max_length=50)  # 'edge', 'elevenlabs'
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

# 物理场景模板
class PhysicalScene(models.Model):
    """物理场景模板"""
    category = models.CharField(max_length=50)  # living_room/laboratory/street
    name = models.CharField(max_length=200)  # "现代实验室"
    default_lighting = models.CharField(max_length=50, blank=True)
    default_atmosphere = models.CharField(max_length=50, blank=True)

    background_image = models.ImageField(upload_to='physical_scenes/', blank=True)
    prompt_template = models.TextField(blank=True)

    is_system_template = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)

# 物品档案
class ItemProfile(models.Model):
    """物品档案"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    item_type = models.CharField(max_length=50)  # weapon/decoration/daily
    item_image = models.ImageField(upload_to='items/', blank=True)
    appearance_count = models.IntegerField(default=0)
    description = models.TextField(blank=True)
```

### UI设计

**角色资产管理界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 👤 角色资产管理                  [返回] [保存] [导出]    │
├─────────────────────────────────────────────────────────┤
│ 角色列表:                                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 刘备 (45场)  关羽 (32场)  张飞 (38场)              │ │
│ │ [点击查看详情]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 角色: 刘备                                           │ │
│ │ ├─ 基本信息                                         │ │
│ │ │  · 姓名: 刘备    性格: 仁德、宽厚              │ │
│ │ │  · 出现次数: 45场  对话数: 128句                │ │
│ │ │                                                   │ │
│ │ ├─ 造型管理 (多套服装)                              │ │
│ │ │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │ │
│ │ │  │ 默认造型 │ │ 宴会装   │ │ 战斗装   │           │ │
│ │ │  │ [预览]  │ │ [预览]  │ │ [预览]  │           │ │
│ │ │  │ 使用:12 │ │ 使用:8  │ │ 使用:25 │           │ │
│ │ │  │ [编辑]  │ │ [编辑]  │ │ [编辑]  │           │ │
│ │ │  └─────────┘ └─────────┘ └─────────┘           │ │
│ │ │  [+ 添加新造型]                                   │ │
│ │ │                                                   │ │
│ │ ├─ 音色配置                                         │ │
│ │ │  · TTS引擎: [Edge-TTS ▼]                         │ │
│ │ │  · 音色: zh-CN-YunxiNeural (温和男声)            │ │
│ │ │  · 语速: [====|====] 0%                         │ │
│ │ │  · 音调: [====|====] +0Hz                        │ │
│ │ │  · 音量: [====|====] +0%                         │ │
│ │ │  · [🔊 试听效果]                                  │ │
│ │ │                                                   │ │
│ │ └─ 使用统计                                         │ │
│ │    章节1: 12次  |  章节2: 18次  |  章节3: 15次     │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 自动更新机制 (主人决策A)

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CharacterPose)
def update_related_shots(sender, instance, created, **kwargs):
    """当 CharacterPose 更新时,标记相关分镜需要重新生成"""
    if not created:  # 只处理更新,不处理新建
        from apps.shots.models import Shot

        # 找到所有使用该造型的分镜
        related_shots = Shot.objects.filter(character_pose=instance)

        if related_shots.exists():
            # 弹窗提示用户
            # TODO: 通过WebSocket发送通知到前端

            # 标记为需要重新生成
            for shot in related_shots:
                shot.needs_regeneration = True
                shot.save()

            # 触发异步任务重新生成画面
            from apps.tasks import regenerate_shots
            regenerate_shots.delay([shot.id for shot in related_shots])
```

---

## Sub-Epic 11.2: 层级式创作工作流

### 目标

实现章节 → 场景 → 分镜的层级式创作流程,双栏布局,直观导航。

### 用户故事

**Story 11.2.1: 双栏布局框架**

```
作为 漫剧创作者
我想要 看到左侧目录树 + 右侧功能区的界面
以便 快速导航和编辑

AC:
- ✅ 左侧显示三级目录树: 章节 → 场景 → 分镜
- ✅ 目录树支持手动折叠/展开
- ✅ 选中节点时,右侧显示对应功能
- ✅ 面包屑导航显示当前位置 [Round 4新增]
- ✅ 支持上一/下一场景快速切换 [Round 4新增]

优先级: P0
工作量: 2天
```

**Story 11.2.2: 目录树组件**

```
作为 漫剧创作者
我想要的目录树可以:
- 展开和折叠节点
- 拖拽调整场景/分镜顺序
- 右键快速操作菜单
- 显示节点图标区分(📖章节/🎬场景/🎞️分镜) [Round 4新增]
- 智能默认展开行为 [Round 4新增]
- 状态持久化(记住展开/折叠状态) [Round 4新增]

AC:
- ✅ 支持点击三角形图标展开/折叠
- ✅ 支持拖拽节点调整顺序
- ✅ 右键菜单: 重命名/删除/复制
- ✅ 不同类型节点使用不同图标
- ✅ 进入场景编辑时,自动展开该场景,折叠其他场景
- ✅ 刷新页面后,目录树状态保持
- ✅ 大型作品(100+场景)使用懒加载,避免一次性加载 [Round 5新增]

优先级: P0
工作量: 2.5天 (Round 5增加0.5天用于懒加载)
```

**Story 11.2.3: 章节级别工作区**

```
作为 漫剧创作者
我想要 在章节级别配置场景和角色
以便 规划整章内容

AC:
- ✅ 显示章节内容概要
- ✅ 支持AI自动生成场景列表 (推荐模式)
  · AI分析章节文本
  · 推荐场景列表
  · 显示推荐理由
- ✅ 支持手动创建场景 (手动模式)
  · 填写场景名称和描述
  · 选择出场角色
- ✅ 可配置章节出场角色
- ✅ 场景列表支持拖拽排序
- ✅ 可批量操作场景 [Round 4新增]

优先级: P0
工作量: 2天
```

**Story 11.2.4: 场景级别工作区**

```
作为 漫剧创作者
我想要 在场景级别配置分镜和细节
以便 精细控制每一场戏

AC:
- ✅ 显示场景描述和属性
- ✅ 支持AI自动生成分镜列表 (推荐模式)
  · 分析场景对话
  · 推荐分镜列表
  · 自动分配镜头类型(特写/中景/远景)
- ✅ 支持手动创建分镜 (手动模式)
- ✅ 可从角色库选择角色和造型
  · 显示角色所有可用造型
  · 一键应用造型
- ✅ 可配置场景属性(时间/天气/氛围)

优先级: P0
工作量: 2天
```

**Story 11.2.5: 分镜级别工作区**

```
作为 漫剧创作者
我想要 在分镜级别编辑画面和音效
以便 完成最终内容生成

AC:
- ✅ 显示分镜详情 (对话、运镜、时长)
- ✅ 可选择角色造型
- ✅ 可生成预览画面
- ✅ 可合成语音
- ✅ 可预览最终效果
- ✅ 支持保存历史版本 [Round 4新增]
- ✅ 可回溯到历史版本 [Round 4新增]

优先级: P0
工作量: 2天
```

**Story 11.2.6: 面包屑导航和快速切换** [Round 4新增]

```
作为 漫剧创作者
我想要 快速在场景之间切换
以便 提高编辑效率

AC:
- ✅ 顶部显示面包屑导航
  · 格式: 作品 > 章节 > 场景 > 分镜
- ✅ 支持点击面包屑快速跳转
- ✅ 支持键盘快捷键切换
  · Ctrl+←: 上一场景
  · Ctrl+→: 下一场景
- ✅ 记住最近访问的3个位置
- ✅ 支持"返回上一次编辑位置"

优先级: P0
工作量: 1天
```

### UI设计

**主界面 - 双栏布局:**
```
┌─────────────────────────────────────────────────────────┐
│ 🏠 三国演义 > 第一章 > 场景1.1  [← 上一场景] [下一场景 →]│
├──────────────┬──────────────────────────────────────────┤
│ 目录树        │ 功能区 (动态内容)                         │
│              │                                          │
│ 📁 三国演义   │ ┌──────────────────────────────────────┐ │
│   📁 第一章   │ │ [章节视图] 第一章: 桃园结义          │ │
│     📁 场景1.1│ │                                      │ │
│     📁 场景1.2│ │ 📝 章节概要:                        │ │
│   📁 第二章   │ │ 刘关张桃园三结义,共誓生死...        │ │
│     📁 场景2.1│ │                                      │ │
│       📁 分镜1│ │ [快速操作]                           │ │
│       📁 分镜2│ │ · ✨ AI生成场景 (推荐)             │ │
│              │ │ · ➕ 手动创建场景                    │ │
│ [+] 新建章节 │ │ · ⚙️ 配置出场角色                   │ │
│              │ │                                      │ │
│              │ │ 📋 场景列表:                         │ │
│              │ │ ┌────────────────────────────────┐  │ │
│              │ │ │ 🎬 场景1.1: 桃园               │  │ │
│              │ │ │ 角色: 刘备,关羽,张飞           │  │ │
│              │ │ │ 分镜数: 5                      │  │ │
│              │ │ │ [编辑] [删除] [上移] [下移]    │  │ │
│              │ │ └────────────────────────────────┘  │ │
│              │ │ ┌────────────────────────────────┐  │ │
│              │ │ │ 🎬 场景1.2: 宴饮               │  │ │
│              │ │ │ 角色: 刘备,关羽,张飞           │  │ │
│              │ │ │ 分镜数: 3                      │  │ │
│              │ │ │ [编辑] [删除] [上移] [下移]    │  │ │
│              │ │ └────────────────────────────────┘  │ │
│              │ └──────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────┘
```

**场景管理 - 卡片预览视图** [Round 4新增]:
```
┌─────────────────────────────────────────────────────────┐
│ 场景管理: 第一章 场景1.1          [列表视图] [卡片视图]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [☐] 全选                              [批量生成] [删除]  │
│                                                          │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│ │ 🎬 场景1.1   │ │ 🎬 场景1.2   │ │ 🎬 场景1.3   │    │
│ │ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │    │
│ │ │[缩略图]  │ │ │ │[缩略图]  │ │ │ │[缩略图]  │ │    │
│ │ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │    │
│ │ 桃园        │ │ 宴饮厅      │ │ 校场        │    │
│ │ 角色:3      │ │ 角色:3      │ │ 角色:2      │    │
│ │ 分镜:5      │ │ 分镜:3      │ │ 分镜:4      │    │
│ │ [编辑] [预览]│ │ [编辑] [预览]│ │ [编辑] [预览]│    │
│ └──────────────┘ └──────────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

```python
# 用户目录树状态配置 [Round 4新增]
class UserTreeState(models.Model):
    """用户的目录树状态配置"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    # 存储展开的节点ID列表
    expanded_nodes = models.JSONField(default=list)

    # 存储当前选中的节点
    selected_node_type = models.CharField(max_length=20)  # 'chapter'/'scene'/'shot'
    selected_node_id = models.IntegerField()

    class Meta:
        unique_together = [['user', 'artwork']]
```

### API设计

**目录树API:**
```python
# 获取完整目录树
GET /api/v1/artworks/{id}/tree/
→ {
    "type": "artwork",
    "id": 1,
    "name": "三国演义",
    "children": [
        {
            "type": "chapter",
            "id": 1,
            "name": "第一章",
            "expanded": True,
            "children": [...]
        }
    ]
}

# 切换节点展开/折叠状态
PUT /api/v1/tree/nodes/{id}/toggle/
→ {"expanded": true/false}

# 拖拽排序
POST /api/v1/tree/nodes/{id}/move/
→ {"new_parent_id": 5, "new_position": 2}

# 面包屑导航 [Round 4新增]
GET /api/v1/tree/breadcrumb/?node_type=scene&node_id=1
→ {
    "breadcrumbs": [...],
    "navigation": {"prev": {...}, "next": {...}}
}

# 懒加载子节点 [Round 5新增]
GET /api/v1/tree/nodes/{id}/children/
→ {"children": [...]}
```

---

## Sub-Epic 11.3: 引擎监控与配置

### 目标

实时监控Ollama/ComfyUI/Edge-TTS引擎状态,可视化Fallback机制。

### 用户故事

**Story 11.3.1: EngineConfig数据模型**

```
作为 系统管理员
我想要 统一配置所有AI引擎
以便 切换主引擎和备份引擎

AC:
- ✅ 支持配置引擎类型(LLM/Image/TTS)
- ✅ 可以设置主引擎和备份引擎
- ✅ 可以配置引擎参数
- ✅ 可以设置Fallback策略
  · 自动切换条件
  · 切换阈值(失败次数/超时时间)
- ✅ 导出/导入引擎配置

优先级: P1
工作量: 1.5天
```

**Story 11.3.2: 实时健康监控**

```
作为 系统管理员
我想要 实时监控所有引擎的健康状态
以便 快速发现和解决问题

AC:
- ✅ 显示引擎在线状态(在线/离线/异常)
- ✅ 显示引擎响应时间
- ✅ 显示引擎使用统计(请求数/成功率)
- ✅ 每5分钟自动检查一次
- ✅ 支持手动刷新
- ✅ 异常时发送通知

优先级: P1
工作量: 1.5天
```

**Story 11.3.3: 引擎监控面板**

```
作为 系统管理员
我想要 在可视化面板查看所有引擎状态
以便 直观掌握系统状况

AC:
- ✅ 卡片式展示每个引擎
- ✅ 显示引擎类型、提供商、状态
- ✅ 实时更新(WebSocket推送)
- ✅ 显示成本统计(本月花费/节省金额)
- ✅ 显示Fallback事件日志

优先级: P1
工作量: 1.5天
```

### UI设计

**引擎监控面板:**
```
┌─────────────────────────────────────────────────────────┐
│ ⚙️  引擎监控                            [刷新] [配置]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ LLM 引擎                                          │ │
│ │ ├─ 主引擎: Ollama (llama2:7b)                     │ │
│ │ │   状态: 🟢 在线 | 响应: 1.2s | 成功率: 98.5%     │ │
│ │ ├─ 备份引擎: OpenAI (gpt-4)                        │ │
│ │ │   状态: 🟢 在线 | 响应: 0.8s                    │ │
│ │ ├─ 今日请求数: 1,234 | 节省: $24.50              │ │
│ │ └─ [查看详情]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Image 引擎                                        │ │
│ │ ├─ 主引擎: ComfyUI (SDXL)                         │ │
│ │ │   状态: 🟢 在线 | 响应: 15.3s | 成功率: 92.1%    │ │
│ │ ├─ 备份引擎: DALL-E 3                               │ │
│ │ │   状态: 🟢 在线                                 │ │
│ │ ├─ 今日请求数: 456 | 节省: $18.24                │ │
│ │ └─ [查看详情]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TTS 引擎                                           │ │
│ │ ├─ 主引擎: Edge-TTS (免费)                         │ │
│ │ │   状态: 🟢 在线 | 响应: 0.3s | 成功率: 99.9%     │ │
│ │ ├─ 备份引擎: ElevenLabs                             │ │
│ │ │   状态: 🟡 配置中                                │ │
│ │ ├─ 今日请求数: 3,456 | 节省: $103.68              │ │
│ │ └─ [查看详情]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 📊 本月总计: 请求数 15,234 | 节省: $298.12              │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

```python
class EngineConfig(models.Model):
    """引擎配置"""
    engine_type = models.CharField(max_length=20)  # 'llm'/'image'/'tts'

    # 主引擎配置
    primary_provider = models.CharField(max_length=50)  # 'ollama'/'comfyui'/'edge'
    primary_config = models.JSONField(default=dict)

    # 备份引擎配置
    fallback_provider = models.CharField(max_length=50, blank=True)
    fallback_config = models.JSONField(default=dict, blank=True)

    # Fallback策略
    fallback_threshold = models.IntegerField(default=3)  # 失败3次后切换
    fallback_timeout = models.IntegerField(default=30)  # 30秒超时

    is_active = models.BooleanField(default=True)
    health_status = models.CharField(max_length=20, default='unknown')  # 'online'/'offline'/'error'
    last_check = models.DateTimeField(auto_now=True)

    # 统计
    total_requests = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)

    # 成本追踪
    total_cost = models.FloatField(default=0.0)  # 实际花费
    saved_cost = models.FloatField(default=0.0)  # 节省金额(相比纯云端)
```

---

## Sub-Epic 11.4: 可视化进度系统

### 目标

实时显示生成进度,让用户不再焦虑等待。

### 用户故事

**Story 11.4.1: 实时进度条组件**

```
作为 漫剧创作者
我想要 看到实时进度条
以便 知道还要等多久

AC:
- ✅ 显示当前阶段(文案改写/分镜生成/图像生成/语音合成)
- ✅ 显示总体进度百分比
- ✅ 显示预估剩余时间
- ✅ 支持取消操作
- ✅ WebSocket实时推送更新

优先级: P1
工作量: 1.5天
```

**Story 11.4.2: 章节推进式工作流UI**

```
作为 漫剧创作者
我想要 按章节顺序推进创作流程
以便 渐进式完成作品

AC:
- ✅ 显示章节进度列表
- ✅ 标记完成状态(待处理/进行中/已完成/失败)
- ✅ 支持暂停/继续
- ✅ 完成后自动进入下一章
- ✅ 支持跳过某个场景

优先级: P1
工作量: 2天
```

**Story 11.4.3: 错误处理和重试**

```
作为 漫剧创作者
我想要的系统可以:
- 友好的错误提示
- 自动重试(指数退避)
- 手动重试按钮
- 跳过错误继续

AC:
- ✅ 显示清晰的错误信息
- ✅ 说明错误原因
- ✅ 提供恢复建议
- ✅ 支持手动重试
- ✅ 支持跳过错误继续

优先级: P1
工作量: 1.5天
```

### UI设计

**进度条组件:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎬 生成进度: 第一章 - 场景1.1                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 阶段1: 文案改写                    ✅ 已完成           │
│ 阶段2: 分镜生成                    ✅ 已完成           │
│ 阶段3: 图像生成                    🔄 进行中 (60%)    │
│ 阶段4: 语音合成                    ⏳ 待处理           │
│                                                          │
│ 总体进度: ████████░░░░░░░░░░░░ 60%                         │
│ 预计剩余时间: 2分30秒                                      │
│                                                          │
│ 当前: 正在生成分镜#3的画面...                             │
│                                                          │
│ [取消生成]                                               │
└─────────────────────────────────────────────────────────┘
```

---

## Sub-Epic 11.5: 批量操作和版本管理

**[Round 4新增]**

### 目标

提供批量操作功能,支持历史版本管理,提升编辑效率。

### 用户故事

**Story 11.5.1: 批量操作功能**

```
作为 漫剧创作者
我想要 批量操作多个场景/分镜
以便 提高编辑效率

AC:
- ✅ 支持批量选择场景/分镜(复选框)
- ✅ 支持批量删除
- ✅ 支持批量重新生成
- ✅ 支持批量移动(移动到其他场景)
- ✅ 支持批量调整出场角色
- ✅ 显示操作进度
- ✅ 批量操作失败时显示详细错误报告

优先级: P1
工作量: 2天
```

**Story 11.5.2: 历史版本管理**

```
作为 漫剧创作者
我想要 查看分镜的历史版本
以便 回溯到之前的版本

AC:
- ✅ 每次保存分镜时自动创建版本快照
- ✅ 显示版本历史列表
  · 版本号
  · 保存时间
  · 修改说明(可选)
  · 预览缩略图
- ✅ 支持预览历史版本
- ✅ 支持一键恢复到历史版本
- ✅ 支持版本对比(显示差异)
- ✅ 保留最近10个版本

优先级: P1
工作量: 2天
```

### UI设计

**批量操作界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 场景管理: 第一章                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [☐] 全选                                    [批量操作]   │
│                                                          │
│ [☐] 🎬 场景1.1: 桃园      角色:3    分镜:5    [编辑]  │
│ [☐] 🎬 场景1.2: 宴饮      角色:3    分镜:3    [编辑]  │
│ [☑] 🎬 场景1.3: 校场      角色:2    分镜:4    [编辑]  │
│ [☑] 🎬 场景1.4: 对峙      角色:2    分镜:2    [编辑]  │
│                                                          │
│ 选中: 2个场景                                            │
│                                                          │
│ [批量生成] [批量移动] [批量删除]                          │
└─────────────────────────────────────────────────────────┘
```

**批量生成进度:**
```
┌─────────────────────────────────────────────────────────┐
│ 🚀 批量生成进度                                [后台运行]  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 总数: 50个分镜                                            │
│                                                          │
│ ✅ 成功: 47个 (94%)                                       │
│ ⏳ 进行中: 2个 (4%)                                      │
│ ❌ 失败: 1个 (2%)                                        │
│                                                          │
│ ████████████████████░░░░░░░ 96%                         │
│ 预计剩余: 30秒                                            │
│                                                          │
│ 失败列表:                                                 │
│ · 分镜#23: 网络超时     [重试] [跳过]                   │
│ · 分镜#45: 内存不足     [重试] [跳过]                   │
│ · 分镜#78: API限流      [重试] [跳过]                   │
│                                                          │
│ [重新生成失败的] [导出错误日志] [关闭]                   │
└─────────────────────────────────────────────────────────┘
```

**版本管理界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 📜 版本历史: 场景1.1 - 分镜#3                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 当前版本: v5 (2026-02-06 14:20)                          │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v5 (当前)     2026-02-06 14:20  [预览] [恢复]     │ │
│ │ ┌─────────┐                                       │ │
│ │ │[缩略图] │  修改: 调整运镜从左到右               │ │
│ │ └─────────┘                                       │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v4            2026-02-06 13:45  [预览] [对比] [恢复] │ │
│ │ ┌─────────┐                                       │ │
│ │ │[缩略图] │  修改: 更换角色造型为"宴会装"         │ │
│ │ └─────────┘                                       │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v3            2026-02-06 11:20  [预览] [对比] [恢复] │ │
│ │ ┌─────────┐                                       │ │
│ │ │[缩略图] │  修改: 初始版本                       │ │
│ │ └─────────┘                                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [查看更多历史版本]                                       │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

```python
# 批量操作任务
class BatchOperationTask(models.Model):
    """批量操作任务"""
    OPERATION_TYPES = (
        ('delete', '批量删除'),
        ('regenerate', '批量生成'),
        ('move', '批量移动'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)

    # 操作目标
    target_ids = models.JSONField()  # [1, 2, 3, ...]

    # 状态
    status = models.CharField(max_length=20)  # 'pending'/'running'/'completed'/'failed'
    total_count = models.IntegerField()
    success_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)

    # 错误详情
    errors = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# 版本快照
class ShotVersionSnapshot(models.Model):
    """分镜版本快照"""
    shot = models.ForeignKey('Shot', on_delete=models.CASCADE)

    version_number = models.IntegerField()
    saved_at = models.DateTimeField(auto_now_add=True)
    saved_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # 快照数据
    snapshot_data = models.JSONField()  # 完整的分镜数据副本
    change_description = models.TextField(blank=True)  # 修改说明

    # 预览
    thumbnail = models.ImageField(upload_to='shots/versions/', blank=True)

    class Meta:
        verbose_name = "分镜版本快照"
        ordering = ['-version_number']
```

---

## 多维度优化方案

**[Round 5新增]**

### 1. 错误处理和质量保障

#### 1.1 智能降级机制

**三层降级策略:**
```
层级1: 本地引擎 (Ollama + ComfyUI + Edge-TTS)
  ↓ 失败 (3次重试,指数退避)
层级2: 云端备份 (OpenAI + DALL-E + ElevenLabs)
  ↓ 失败 (1次重试)
层级3: 手动模式 + 友好错误提示
```

**实现:**
```python
class SmartDegradationService:
    """智能降级服务"""

    async def generate_with_fallback(self, shot_id):
        """带降级的生成"""
        # 尝试1: 本地引擎
        try:
            return await self._generate_local(shot_id)
        except Exception as e:
            logger.warning(f"本地引擎失败: {e}")

        # 尝试2: 云端备份
        try:
            return await self._generate_cloud(shot_id)
        except Exception as e:
            logger.error(f"云端引擎也失败: {e}")

        # 降级3: 手动模式
        return {
            'success': False,
            'error': '所有引擎均不可用',
            'suggestion': '请检查引擎配置或稍后重试',
            'manual_mode': True
        }
```

#### 1.2 批量操作错误报告

**详细错误信息:**
```javascript
// 错误报告组件
const ErrorReport = {
  success: 47,
  failed: 3,
  errors: [
    {
      shot_id: 23,
      shot_name: "刘备特写",
      error_type: "Timeout",
      error_message: "图像生成超时(>120秒)",
      suggestion: "检查ComfyUI服务状态",
      can_retry: true,
      can_skip: true
    },
    // ...
  ]
}
```

### 2. 性能优化

#### 2.1 目录树懒加载 [Round 5新增]

**虚拟滚动组件:**
```javascript
import { VirtualScroller } from 'vue-virtual-scroller'
import { Tree } from 'element-ui'

<Tree>
  <VirtualScroller
    :items="treeNodes"
    :item-height="32"
    :visible-count="20"
    :buffer="200"
  >
    <template #default="{ node }">
      <TreeNode :node="node" />
    </template>
  </VirtualScroller>
</Tree>
```

#### 2.2 图像懒加载和缓存

```javascript
// 懒加载
import VueLazyload from 'vue-lazyload'

Vue.use(VueLazyload, {
  lazyComponent: true,
  loading: '/static/loading.gif',
  error: '/static/error.png'
})

// 响应式图片
<picture>
  <source :srcset="shot.thumbnail_webp" type="image/webp">
  <img :src="shot.thumbnail_jpg" loading="lazy" />
</picture>

// Service Worker缓存
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
}
```

#### 2.3 API分页和字段裁剪

```python
# 分页查询
class TreePaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(default=1)
    per_page = serializers.IntegerField(default=50)
    fields = serializers.ListField(default=['id', 'name', 'type'])

class TreeView(View):
    def get(self, request, artwork_id):
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))
        fields = request.GET.get('fields', 'id,name,type').split(',')

        # 只返回需要的字段
        queryset = Node.objects.filter(artwork_id=artwork_id)
        data = queryset.values(*fields)[(page-1)*per_page : page*per_page]

        return Response({'data': data, 'total': queryset.count()})
```

### 3. 用户引导系统

#### 3.1 首次使用引导

```javascript
// 引导流程
const onboardingSteps = [
  {
    target: '#tree-panel',
    header: '目录导航',
    body: '左侧是作品的目录树,可以快速导航到章节、场景和分镜',
    params: {
      placement: 'right'
    }
  },
  {
    target: '#workspace-panel',
    header: '工作区域',
    body: '右侧是工作区,会根据选中的节点显示不同的功能',
    params: {
      placement: 'left'
    }
  },
  // ...更多步骤
]
```

#### 3.2 上下文帮助

```vue
<template>
  <div>
    <h3>角色造型管理</h3>
    <HelpIcon @click="showHelp = true" />

    <ContextHelpModal v-if="showHelp" @close="showHelp = false">
      <h4>角色造型管理帮助</h4>
      <p>角色造型是指同一角色在不同场景下的不同装扮...</p>

      <video width="400" controls>
        <source src="/help/character-pose.mp4" type="video/mp4">
      </video>

      <button @click="openFullDocs">查看完整文档</button>
    </ContextHelpModal>
  </div>
</template>
```

### 4. 可访问性

#### 4.1 键盘导航

**完整快捷键列表:**
```
全局快捷键:
Ctrl+N          新建章节
Ctrl+S          保存
Ctrl+Z          撤销
Ctrl+Y          重做
Ctrl+F          搜索
Ctrl+,          打开设置

目录树快捷键:
↑↓←→           在目录树中导航
Space/Enter     展开/折叠节点
Delete          删除选中节点
F2              重命名
Ctrl+C          复制
Ctrl+V          粘贴
Ctrl+X          剪切

场景切换快捷键:
Ctrl+←          上一场景
Ctrl+→          下一场景
Ctrl+Shift+←    上一章
Ctrl+Shift+→    下一章

分镜操作快捷键:
Ctrl+G          生成当前分镜
Ctrl+R          重新生成
Ctrl+E          编辑
Ctrl+P          预览
```

#### 4.2 屏幕阅读器支持

```html
<!-- 目录树节点 -->
<div
  role="treeitem"
  aria-expanded="true"
  aria-label="第一章"
  aria-level="2"
  tabindex="0"
>
  第一章
</div>

<!-- 进度条 -->
<div
  role="progressbar"
  aria-valuenow="60"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="生成进度"
>
  60%
</div>
```

#### 4.3 色彩对比度

```css
/* ✅ 好: 图标 + 颜色 */
.status-success::before {
  content: "✓";
  color: green;
}
.status-error::before {
  content: "✗";
  color: red;
}

/* 遵循WCAG 2.1 AA标准: 对比度至少4.5:1 */
```

### 5. 数据导入导出

#### 5.1 多格式导入

**支持格式:**
- `.txt` (纯文本)
- `.docx` (Word文档)
- `.xlsx` (Excel表格)
- `.md` (Markdown)
- `.pdf` (PDF - OCR识别)

**导入向导:**
```python
class ScriptImportWizard:
    """剧本导入向导"""

    def step1_upload(self, file):
        """上传文件"""
        # 验证文件格式
        # 保存到临时位置
        return {'step': 2, 'file_path': temp_path}

    def step2_parse(self, file_path):
        """解析文件"""
        if file_path.endswith('.txt'):
            return self._parse_txt(file_path)
        elif file_path.endswith('.docx'):
            return self._parse_docx(file_path)
        # ...

    def step3_confirm(self, parsed_data):
        """确认解析结果"""
        # 显示AI解析的结构
        # 用户可以手动调整
        return {'step': 4}

    def step4_import(self, confirmed_data):
        """导入到系统"""
        # 创建Artwork/Chapter/Scene
        return {'success': True, 'artwork_id': 1}
```

#### 5.2 多格式导出

**导出选项:**
```python
class ScriptExportService:
    """剧本导出服务"""

    def export_to_pdf(self, shot_id):
        """导出为PDF"""
        # 生成排版好的PDF
        pass

    def export_to_word(self, shot_id):
        """导出为Word"""
        # 生成.docx文件
        pass

    def export_images(self, shot_ids):
        """导出图像序列(ZIP)"""
        # 打包所有生成的图像
        pass

    def export_to_xml(self, project_id):
        """导出时间轴(Final Cut Pro XML)"""
        # 导出为可编辑的视频项目文件
        pass
```

---

## 实施计划

### 时间线 (5周)

**Week 1: 资源管理 + 错误处理**
- Day 1-2: CharacterPose/CharacterVoiceConfig 数据模型
- Day 3-4: 角色资产管理后端 API
- Day 5: 角色资产管理前端界面
- Day 6-7: 智能降级机制 (Murat)
- **里程碑:** 资源管理系统可使用

**Week 2: 双栏布局 + 性能优化**
- Day 1: 双栏布局框架
- Day 2-3: 目录树组件(含懒加载) (Barry)
- Day 4: 章节级别工作区
- Day 5: 场景级别工作区
- Day 6: 面包屑导航 (Sally)
- Day 7: 集成测试
- **里程碑:** 双栏布局基础功能完成

**Week 3: AI生成 + 批量操作**
- Day 1-2: AI生成接口(场景+分镜)
- Day 3: 分镜级别工作区
- Day 4-5: 批量操作功能 (Mary)
- Day 6: 批量操作错误报告 (Murat)
- Day 7: 测试和修复
- **里程碑:** 创作工作流可使用

**Week 4: 分镜编辑 + 版本管理 + 用户引导**
- Day 1-2: 分镜编辑完善
- Day 3-4: 历史版本管理
- Day 5: 用户引导系统 (Paige)
- Day 6: 交互式引导流程
- Day 7: 测试和优化
- **里程碑:** 编辑和版本管理完成

**Week 5: 数据导入导出 + 可访问性 + 集成测试**
- Day 1-2: 多格式导入/导出 (John)
- Day 3: 键盘导航 (Sally)
- Day 4: 屏幕阅读器支持
- Day 5: 性能优化(缓存、CDN)
- Day 6: 端到端测试
- Day 7: Bug修复和文档
- **里程碑:** Epic 11 完成

### 依赖关系

```
Epic 10 (本地引擎集成) ← 必须先完成
    ↓
Epic 11.1 (资源管理)
    ↓
Epic 11.2 (层级式工作流) ← 依赖 11.1
    ↓
Epic 11.3 (引擎监控) ← 可并行
    ↓
Epic 11.4 (可视化进度) ← 依赖 11.2
    ↓
Epic 11.5 (批量操作) ← 依赖 11.2
```

### 风险分析

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 性能问题(大型作品) | 高 | 中 | 懒加载、虚拟滚动、分页 |
| AI生成质量不稳定 | 中 | 中 | 提供手动模式作为备选 |
| 自动更新导致冲突 | 中 | 低 | 弹窗确认+异步任务 |
| 批量操作复杂度高 | 中 | 中 | 渐进式实现,先支持简单操作 |
| 浏览器兼容性 | 低 | 低 | 使用现代浏览器,优雅降级 |

---

## 成功标准

### 验收标准

**Sub-Epic 11.1: 资源管理**
- ✅ 可以在统一界面管理角色、场景、物品
- ✅ 支持同一角色多套造型
- ✅ 修改造型后自动更新所有使用该造型的分镜
- ✅ 角色使用统计准确

**Sub-Epic 11.2: 层级式创作工作流**
- ✅ 双栏布局正常工作
- ✅ 目录树支持三级导航
- ✅ 章节场景分镜三级工作区功能完整
- ✅ AI生成和手动创建模式都可用
- ✅ 面包屑导航和快速切换工作正常
- ✅ 批量操作功能可用

**Sub-Epic 11.3: 引擎监控**
- ✅ 可以统一配置所有引擎
- ✅ 实时监控引擎状态
- ✅ 监控面板正确显示统计数据
- ✅ Fallback机制可视化

**Sub-Epic 11.4: 可视化进度**
- ✅ 实时进度条显示正确
- ✅ 预估剩余时间准确(误差<20%)
- ✅ 章节推进式工作流UI完整
- ✅ 错误处理友好,重试机制可用

**Sub-Epic 11.5: 批量操作和版本管理**
- ✅ 批量操作功能可用
- ✅ 批量操作错误报告详细
- ✅ 历史版本管理功能完整
- ✅ 版本对比和恢复功能可用

### 性能指标

| 指标 | 目标 | 测试方法 |
|------|------|---------|
| 目录树初始加载时间 | <0.5秒 (100场景) | 性能测试 |
| 图像懒加载触发 | 滚动到可视区域内 | 视觉检查 |
| AI生成响应时间 | <5秒(场景),<30秒(分镜) | 计时测试 |
| 批量操作吞吐量 | 100个分镜/批 | 负载测试 |
| 引擎健康检查延迟 | <2秒 | API测试 |

### 用户满意度指标

| 指标 | 目标 |
|------|------|
| 新手上手时间 | <10分钟(完成第一次场景创建) |
| 资源查找效率 | 从5分钟降低到30秒 |
| 工作流导航效率 | 从10次点击降低到2次点击 |
| 错误恢复成功率 | >90%(用户自助恢复) |

---

## 附录

### A. 代码示例

#### A.1 数据模型 - CharacterPose

```python
from django.db import models
from django.core.exceptions import ValidationError

class CharacterPose(models.Model):
    """角色造型"""
    character = models.ForeignKey(
        'CharacterProfile',
        on_delete=models.CASCADE,
        related_name='poses'
    )

    pose_name = models.CharField(max_length=200)
    pose_type = models.CharField(
        max_length=50,
        choices=[
            ('casual', '家庭装'),
            ('formal', '宴会装'),
            ('battle', '战斗装'),
            ('school', '校园装'),
            ('custom', '自定义'),
        ]
    )
    pose_image = models.ImageField(upload_to='characters/poses/')

    suitable_for_scenes = models.JSONField(default=list)
    description = models.TextField(blank=True)
    usage_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "角色造型"
        verbose_name_plural = "角色造型"
        ordering = ['-usage_count', 'pose_name']

    def __str__(self):
        return f"{self.character.name} - {self.pose_name}"

    def clean(self):
        """验证数据"""
        if not self.pose_name:
            raise ValidationError("造型名称不能为空")
```

#### A.2 前端组件 - 目录树

```vue
<template>
  <div class="tree-panel">
    <div class="tree-header">
      <h3>{{ artwork.title }}</h3>
      <button @click="expandAll">全部展开</button>
      <button @click="collapseAll">全部折叠</button>
    </div>

    <el-tree
      :data="treeData"
      :props="defaultProps"
      node-key="id"
      :default-expanded-keys="expandedKeys"
      :expand-on-click-node="false"
      @node-click="handleNodeClick"
      @node-expand="handleNodeExpand"
      @node-collapse="handleNodeCollapse"
      :render-content="renderContent"
      lazy
      :load="loadNode"
    >
      <template #default="{ node, data }">
        <span class="custom-tree-node">
          <i :class="getNodeIcon(data.type)"></i>
          <span class="node-label">{{ data.name }}</span>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<script>
export default {
  data() {
    return {
      treeData: [],
      expandedKeys: [],
      defaultProps: {
        children: 'children',
        label: 'name',
        isLeaf: (data) => !data.children || data.children.length === 0
      }
    }
  },
  methods: {
    async loadNode(node, resolve) {
      // 懒加载子节点
      if (node.level === 0) {
        // 加载章节
        const chapters = await this.loadChapters(node.data.id)
        resolve(chapters)
      } else if (node.level === 1) {
        // 加载场景
        const scenes = await this.loadScenes(node.data.id)
        resolve(scenes)
      }
      },

    getNodeIcon(type) {
      const icons = {
        'artwork': 'el-icon-folder-opened',
        'chapter': 'el-icon-document',
        'scene': 'el-icon-video-camera',
        'shot': 'el-icon-picture'
      }
      return icons[type] || 'el-icon-file'
    },

    handleNodeClick(data, node) {
      // 更新工作区内容
      this.$emit('node-selected', data)
    },

    async loadChapters(artworkId) {
      const response = await this.$http.get(`/api/v1/artworks/${artworkId}/chapters/`)
      return response.data.map(chapter => ({
        id: chapter.id,
        name: chapter.title,
        type: 'chapter',
        children: []  // 延迟加载
      }))
    },

    async loadScenes(chapterId) {
      const response = await this.$http.get(`/api/v1/chapters/${chapterId}/scenes/`)
      return response.data.map(scene => ({
        id: scene.id,
        name: scene.scene_name,
        type: 'scene',
        children: []
      }))
    }
  }
}
</script>
```

### B. API端点完整列表

```
资源管理:
POST   /api/v1/artworks/{id}/characters/
GET    /api/v1/artworks/{id}/characters/
PUT    /api/v1/characters/{id}/
DELETE /api/v1/characters/{id}/

POST   /api/v1/characters/{id}/poses/
GET    /api/v1/characters/{id}/poses/
PUT    /api/v1/poses/{id}/
DELETE /api/v1/poses/{id}/

POST   /api/v1/characters/{id}/voice-config/
GET    /api/v1/characters/{id}/voice-config/
PUT    /api/v1/voice-configs/{id}/

目录树:
GET    /api/v1/artworks/{id}/tree/
PUT    /api/v1/tree/nodes/{id}/toggle/
POST   /api/v1/tree/nodes/{id}/move/
GET    /api/v1/tree/breadcrumb/

场景/分镜:
POST   /api/v1/chapters/{id}/generate-scenes/
POST   /api/v1/chapters/{id}/scenes/
GET    /api/v1/scenes/{id}/
PUT    /api/v1/scenes/{id}/
DELETE /api/v1/scenes/{id}/

POST   /api/v1/scenes/{id}/generate-shots/
POST   /api/v1/scenes/{id}/shots/
GET    /api/v1/shots/{id}/
PUT    /api/v1/shots/{id}/
DELETE /api/v1/shots/{id}/

批量操作:
POST   /api/v1/scenes/batch-delete/
POST   /api/v1/scenes/batch-move/
POST   /api/v1/shots/batch-regenerate/

版本管理:
GET    /api/v1/shots/{id}/versions/
POST   /api/v1/shots/{id}/versions/
POST   /api/v1/shots/{id}/versions/{version_id}/restore/

引擎监控:
GET    /api/v1/engines/status/
GET    /api/v1/engines/{id}/health/
PUT    /api/v1/engines/{id}/config/

数据导入导出:
POST   /api/v1/artworks/import/
POST   /api/v1/artworks/{id}/export/pdf/
POST   /api/v1/artworks/{id}/export/zip/
```

---

**文档维护:** 本文档为可迭代规划文档,后续 Party Mode 讨论将继续更新此文档。

**最后更新:** 2026-02-06 14:35
**更新内容:** Round 5 多维度优化(错误处理/性能/用户引导/可访问性/数据导入导出)

---

## Sub-Epic 11.6: 模板系统和快速创建

**[Round 6新增]**

### 目标

提供场景模板和分镜模板,支持拖拽创建和快速对话输入,大幅提升创作效率。

### 用户故事

**Story 11.6.1: 拖拽创建分镜**

```
作为 漫剧创作者
我想要 从角色库拖拽角色到场景中快速创建分镜
以便 提高创建效率

AC:
- ✅ 支持从角色库拖拽角色到场景工作区
- ✅ 拖拽时显示角色预览和默认造型
- ✅ 放下后自动创建分镜
  · 自动使用角色的默认造型
  · 或使用该角色最近使用的造型
- ✅ 支持批量拖拽多个角色
  · 创建多个分镜,每个角色一个
- ✅ 拖拽放置后可以继续编辑(对话、运镜等)

优先级: P1
工作量: 2天
```

**Story 11.6.2: 快速对话输入模式**

```
作为 漫剧创作者
我想要 批量输入对话,系统自动识别角色并创建分镜
以便 高效处理大量对话内容

AC:
- ✅ 提供文本输入框支持批量输入对话
- ✅ AI自动识别每句对话的说话角色
  · 基于角色名称匹配
  · 基于对话模式分析(Llama 3)
  · 显示识别结果供用户确认
- ✅ 自动分配角色造型
  · 使用角色的默认造型
  · 或使用该角色最近使用的造型
- ✅ 自动生成默认分镜类型(中景)
- ✅ 支持预览即将创建的分镜列表
- ✅ 确认后批量创建分镜
- ✅ 创建后可以继续编辑每个分镜

优先级: P1
工作量: 2.5天
```

**Story 11.6.3: 场景模板库**

```
作为 漫剧创作者
我想要 保存常用的场景配置为模板
以便 快速创建类似场景

AC:
- ✅ 可以将当前场景保存为模板
  · 包含场景描述、氛围、时间等
  · 包含出场角色列表
  · 包含背景和光照配置
- ✅ 可以为模板命名和分类
  · 分类: "室内对话"/"室外战斗"/"宴会"等
  · 添加描述
- ✅ 可以从模板创建新场景
  · 自动应用模板的所有配置
  · 可以修改部分配置
- ✅ 模板列表支持管理
  · 查看所有模板
  · 编辑模板
  · 删除模板
- ✅ 系统提供预置模板
  · "室内对话"
  · "室外战斗"
  · "宴会"

优先级: P2
工作量: 2天
```

**Story 11.6.4: 分镜模板系统**

```
作为 漫剧创作者
我想要 保存常用的分镜配置为模板
以便 快速创建相似分镜

AC:
- ✅ 可以将当前分镜保存为模板
  · 包含对话格式
  · 包含运镜参数(类型、时长、方向)
  · 包含画面构图参数
- ✅ 可以为模板命名和分类
  · 分类: "特写"/"中景"/"远景"/"推镜头"
  · 添加描述和使用示例
- ✅ 可以从模板创建新分镜
- ✅ 支持应用模板到批量分镜
- ✅ 系统提供预置分镜模板

优先级: P2
工作量: 1.5天
```

**Story 11.6.5: 右键上下文菜单**

```
作为 漫剧创作者
我想要的目录树支持右键快捷菜单
以便 快速进行常用操作

AC:
- ✅ 右键点击目录树节点显示上下文菜单
- ✅ 菜单项根据节点类型动态变化
  · 章节: "编辑标题"/"AI生成场景"/"删除"/"设为封面"
  · 场景: "编辑"/"复制"/"粘贴"/"删除"/"设为封面"/"查看统计"
  · 分镜: "编辑"/"复制"/"删除"/"设为封面"/"预览"
- ✅ 支持"复制"和"粘贴"
  · 复制场景/分镜到剪贴板
  · 粘贴到其他章节/场景
- ✅ 支持"设为封面"
  · 将该场景/分镜的预览图设为章节封面
- ✅ 菜单项支持键盘快捷键提示

优先级: P1
工作量: 1.5天
```

### UI设计

**拖拽创建分镜界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎬 场景1.1: 桃园                                         │
├──────────────────────┬──────────────────────────────────┤
│ 角色库               │ 工作区                              │
│                      │                                      │
│ [拖拽] 刘备-宴会装     │ ┌─────────────────────────────────────┐│
│ [拖拽] 关羽-战斗装     │ │ 拖拽角色到此处创建分镜            ││
│ [拖拽] 张飞-战斗装     │ │                                     ││
│                      │ │ 👤 刘备-宴会装                      ││
│                      │ │ 💭 "二位贤弟,今日..."              ││
│                      │ │                                     ││
│                      │ │ 分镜类型: [中景 ▼]                  ││
│ │ 时长: [3秒 ▼]                         ││
│ │                                     ││
│ │ [快速创建分镜]                       ││
│ └─────────────────────────────────────┘│
└──────────────────────┴──────────────────────────────────┘
```

**快速对话输入界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 📝 快速输入分镜 - 场景1.1: 桃园                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 角色选择: [刘备 ▼]  造型: [宴会装 ▼]  场景: [桃园 ▼]    │
│                                                          │
│ 对话输入框:                                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 刘备: "二位贤弟,今日桃园相会,..."                │ │
│ │ 关羽: "某虽不才,愿随大哥扫荡中原..."            │ │
│ │ 张飞: "俺老张也没什么,就是..."                    │ │
│ │                                                  │ │
│ │ [AI识别角色] 🔍                                    │ │
│ │                                                  │ │
│ │ 识别结果:                                         │ │
│ │ ✅ 刘备 - 宴会装  ✅ 关羽 - 战斗装  ✅ 张飞 - 战斗装  │ │
│ │                                                  │ │
│ │ [清空] [批量创建分镜]                               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 预览: 将创建3个分镜                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 分镜#1: 刘备-宴会装-中景-3秒                     │ │
│ │   对话: "二位贤弟,今日..."                         │ │
│ │ 分镜#2: 关羽-战斗装-中景-3秒                     │ │
│ │   对话: "某虽不才,愿随大哥..."                     │ │
│ │ 分镜#3: 张飞-战斗装-中景-3秒                     │ │
│ │   对话: "俺老张也没什么,就是..."                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [确认创建] [继续编辑] [取消]                             │
└─────────────────────────────────────────────────────────┘
```

**场景模板管理界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 📚 场景模板库                            [新建模板]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 分类筛选: [全部 ▼] [室内对话 ▼] [室外战斗 ▼]        │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🏠 室内对话 - 宴会厅                            │ │
│ │ 描述: 适合室内角色对话、密谋等场景              │ │
│ │ 包含: 场景氛围、光照、背景配置                    │ │
│ │ 使用次数: 12                                       │
│ │ [应用模板] [编辑] [删除]                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⚔️ 室外战斗 - 校场                                │ │
│ │ 描述: 适合角色对峙、战斗等场景                      │ │
│ │ 使用次数: 8                                        │
│ │ [应用模板] [编辑] [删除]                            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🍷 宴会 - 宴会厅                                  │ │
│ │ 描述: 系统预置模板                                │ │
│ │ 使用次数: 5                                        │
│ │ [应用模板] [编辑] [删除]                            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**右键上下文菜单:**
```
右键点击场景节点:
┌─────────────────┐
│ 编辑场景          │ Ctrl+E
│ AI生成分镜      │
│ ───────────────── │
│ 复制场景          │ Ctrl+C
│ 粘贴场景          │ Ctrl+V
│ 删除场景          │ Delete
│ ───────────────── │
│ 设为封面          │
│ 查看统计          │
└─────────────────┘

快捷键提示显示在菜单项右侧
```

### 数据模型

```python
# 场景模板
class SceneTemplate(models.Model):
    """场景模板"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)  # "室内对话"
    category = models.CharField(max_length=50)  # 'indoor'/'outdoor'/'banquet'
    description = models.TextField(blank=True)

    # 模板配置
    template_config = models.JSONField(default=dict)
    # {
    #   "atmosphere": "温馨",
    #   "time_of_day": "早晨",
    #   "weather": "晴朗",
    #   "background_id": 123,
    #   "default_characters": [1, 2, 3]
    # }

    # 统计
    usage_count = models.IntegerField(default=0)

    # 系统预置
    is_system_template = models.BooleanField(default=False)

    class Meta:
        verbose_name = "场景模板"
        verbose_name_plural = "场景模板"
        ordering = ['-usage_count', 'name']

# 分镜模板
class ShotTemplate(models.Model):
    """分镜模板"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)  # "特写"
    category = models.CharField(max_length=50)  # 'close-up'/'medium'/'wide'/'pan'
    description = models.TextField(blank=True)

    # 模板配置
    template_config = models.JSONField(default=dict)
    # {
    #   "shot_type": "medium",
    #   "duration": 3.0,
    #   "camera_movement": {
    #     "type": "static",
    #     "direction": "front"
    #   },
    #   "dialogue_format": "{角色}: {对话}"
    # }

    # 统计
    usage_count = models.IntegerField(default=0)

    is_system_template = models.BooleanField(default=False)

# 快速对话输入任务
class QuickInputTask(models.Model):
    """快速对话输入任务"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scene = models.ForeignKey(ScriptScene, on_delete=models.CASCADE)

    # 输入的对话文本
    dialogue_text = models.TextField()

    # AI识别结果
    recognized_dialogues = models.JSONField(default=list)
    # [
    #   {"character_id": 1, "pose_id": 2, "dialogue": "..."},
    #   {"character_id": 2, "pose_id": 3, "dialogue": "..."}
    # ]

    # 状态
    status = models.CharField(max_length=20)  # 'draft'/'recognized'/'confirmed'/'created'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### API设计

```
模板管理:
POST   /api/v1/scene-templates/
GET    /api/v1/scene-templates/
PUT    /api/v1/scene-templates/{id}/
DELETE /api/v1/scene-templates/{id}/

POST   /api/v1/shot-templates/
GET    /api/v1/shot-templates/
PUT    /api/v1/shot-templates/{id}/
DELETE /api/v1/shot-templates/{id}/

POST   /api/v1/scenes/{id}/apply-template/
POST   /api/v1/shots/{id}/apply-template/

快速创建:
POST   /api/v1/scenes/{id}/quick-create/
  {
    "character_pose_id": 1,
    "dialogue": "...",
    "shot_type": "medium",
    "duration": 3.0
  }

POST   /api/v1/scenes/{id}/quick-input/
  {
    "dialogue_text": "刘备: ...\n关羽: ...",
    "auto_recognize": true
  }
→ {
    "recognized_dialogues": [...],
    "preview_shots": [...]
  }

POST   /api/v1/scenes/{id}/quick-input/confirm/
  {
    "task_id": 123,
    "confirmed_dialogues": [...]
  }
```

### 前端组件示例

**拖拽组件:**
```vue
<template>
  <div class="quick-create-panel">
    <h3>快速创建分镜</h3>

    <!-- 角色库 -->
    <div class="character-library">
      <div
        v-for="character in characters"
        :key="character.id"
        draggable="true"
        @dragstart="onDragStart(character)"
        class="character-card"
      >
        <img :src="character.default_pose.thumbnail" />
        <span>{{ character.name }}</span>
        <span class="pose-name">{{ character.default_pose.pose_name }}</span>
      </div>
    </div>

    <!-- 工作区 -->
    <div
      class="workspace"
      @drop.prevent="onDrop"
      @dragover.prevent
    >
      <p v-if="!droppedCharacter">拖拽角色到此处创建分镜</p>
      <div v-else class="shot-preview">
        <img :src="droppedCharacter.pose_image" />
        <h4>{{ droppedCharacter.name }} - {{ droppedCharacter.pose_name }}</h4>

        <div class="shot-config">
          <div class="form-group">
            <label>对话:</label>
            <textarea v-model="dialogue" rows="3"></textarea>
          </div>

          <div class="form-group">
            <label>分镜类型:</label>
            <select v-model="shotType">
              <option value="close-up">特写</option>
              <option value="medium">中景</option>
              <option value="wide">远景</option>
            </select>
          </div>

          <div class="form-group">
            <label>时长(秒):</label>
            <input type="number" v-model="duration" step="0.5" />
          </div>
        </div>

        <button @click="createShot">快速创建分镜</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      characters: [],
      droppedCharacter: null,
      dialogue: '',
      shotType: 'medium',
      duration: 3.0
    }
  },
  methods: {
    onDragStart(character) {
      // 传递拖拽数据
      event.dataTransfer.setData('character', JSON.stringify(character))
    },

    onDrop(event) {
      const character = JSON.parse(event.dataTransfer.getData('character'))
      this.droppedCharacter = character
    },

    async createShot() {
      await this.$http.post(`/api/v1/scenes/${this.sceneId}/quick-create/`, {
        character_pose_id: this.droppedCharacter.pose_id,
        dialogue: this.dialogue,
        shot_type: this.shotType,
        duration: this.duration
      })

      this.$message.success('分镜创建成功!')
      this.$emit('shot-created')
    }
  }
}
</script>
```

**右键菜单组件:**
```vue
<template>
  <vue-context-menu
    :context="contextMenuData"
    :local="local"
    @open="onMenuOpen"
    @close="onMenuClose"
  >
    <vue-context-menu-item
      :icon="'el-icon-edit'"
      @click="handleAction('edit')"
    >
      编辑
      <span>Ctrl+E</span>
    </vue-context-menu-item>

    <vue-context-menu-item
      :icon="'el-icon-document-copy'"
      @click="handleAction('copy')"
    >
      复制
      <span>Ctrl+C</span>
    </vue-context-menu-item>

    <vue-context-menu-item
      :icon="'el-icon-delete'"
      @click="handleAction('delete')"
    >
      删除
      <span>Delete</span>
    </vue-context-menu-item>
  </vue-context-menu>
</template>

<script>
export default {
  data() {
    return {
      contextMenuData: null,
      selectedNode: null
    }
  },
  methods: {
    onMenuOpen(event) {
      const { type, id, name } = event
      this.selectedNode = { type, id, name }
    },

    handleAction(action) {
      switch(action) {
        case 'edit':
          this.$emit('edit-node', this.selectedNode)
          break
        case 'copy':
          this.$emit('copy-node', this.selectedNode)
          break
        case 'delete':
          this.$confirm('确定删除?', '警告').then(() => {
            this.$emit('delete-node', this.selectedNode)
          })
          break
      }
    }
  }
}
</script>
```

---

## 实施计划 (更新后)

### 时间线 (5周 - 保持不变)

**Week 1: 资源管理 + 错误处理**
- Day 1-2: CharacterPose/CharacterVoiceConfig 数据模型
- Day 3-4: 角色资产管理后端 API
- Day 5: 角色资产管理前端界面
- Day 6-7: 智能降级机制
- **里程碑:** 资源管理系统可使用

**Week 2: 双栏布局 + 性能优化 + 模板系统**
- Day 1: 双栏布局框架
- Day 2-3: 目录树组件(含懒加载)
- Day 4: 章节级别工作区
- Day 5: 场景级别工作区
- Day 6: 面包屑导航
- **新增: Day 6.5: 拖拽创建分镜 (Round 6)**
- Day 7: 集成测试
- **里程碑:** 双栏布局基础功能完成

**Week 3: AI生成 + 批量操作 + 快速创建**
- Day 1: AI生成接口(场景+分镜)
- Day 2: 分镜级别工作区
- Day 3-4: 批量操作功能
- Day 5: **快速对话输入模式 (Round 6)**
- Day 6: 批量操作错误报告
- Day 7: 测试和修复
- **里程碑:** 创作工作流可使用

**Week 4: 分镜编辑 + 版本管理 + 用户引导 + 模板管理**
- Day 1-2: 分镜编辑完善
- Day 3-4: 历史版本管理
- Day 5: 用户引导系统
- **新增: Day 5.5: 场景模板库 (Round 6)**
- Day 6: 交互式引导流程
- Day 7: 测试和优化
- **里程碑:** 编辑和版本管理完成

**Week 5: 数据导入导出 + 可访问性 + 右键菜单 + 集成测试**
- Day 1-2: 多格式导入/导出
- Day 3: 键盘导航
- Day 4: 屏幕阅读器支持
- **新增: Day 4.5: 右键上下文菜单 (Round 6)**
- Day 5: 性能优化(缓存、CDN)
- Day 6: 端到端测试
- Day 7: Bug修复和文档
- **里程碑:** Epic 11 完成

**新增Story统计:**
- 原计划: 25个Story
- Round 6新增: 5个Story (11.6.1-11.6.5)
- **总计: 30个Story**

---

## 成功标准 (更新)

### 新增验收标准

**Sub-Epic 11.6: 模板系统和快速创建**
- ✅ 可以从角色库拖拽角色到场景中创建分镜
- ✅ 快速对话输入模式工作正常,角色识别准确率>90%
- ✅ 场景模板库提供至少5个预置模板
- ✅ 分镜模板库提供至少3个预置模板
- ✅ 可以保存自定义模板
- ✅ 可以从模板创建场景/分镜
- ✅ 右键菜单正常工作,菜单项根据节点类型动态变化
- ✅ 支持复制/粘贴场景和分镜

---

---

## Sub-Epic 11.7: 智能模板系统和版本管理

**[Round 7新增]**

### 目标

基于用户决策,设计完整的场景模板库和分镜模板系统,支持智能推荐、团队分享和版本管理。

### 用户决策总结

**Round 7 决策:**
- **Q1: 场景模板库设计** → C. 混合方案（推荐）- 平衡易用性和灵活性
- **Q2: 分镜模板系统** → C. 场景感知模板（推荐）- 智能适配场景
- **Q3: 模板管理界面** → C. 混合界面（推荐）- 双重入口
- **Q4: 模板分享机制** → B. P1 最好做 - 团队内分享
- **Q5: 模板版本管理** → A. 需要版本管理（保存历史、支持回滚）

### 用户故事

**Story 11.7.1: 混合场景模板库**

```
作为 漫剧创作者
我想要 既有系统预设模板又能自定义和智能推荐
以便 快速创建常见场景类型

AC:
- ✅ 系统预设80%常见场景模板
  · 对话场景: 双人对话-正面/侧面/群体对话-圆桌
  · 动作场景: 战斗/追逐/体育竞技
  · 环境场景: 室内-卧室/办公室,室外-街道/自然风景
  · 特殊场景: 梦境/回忆/时间跳跃/情感特写
- ✅ 每个预设模板包含默认配置
  · 默认背景/环境
  · 建议角色数量
  · 默认运镜方式
  · 推荐音效类型
  · 典型灯光效果
- ✅ AI智能推荐场景模板
  · 基于剧本内容自动推荐
  · 学习用户使用习惯优化推荐
  · 显示推荐理由和匹配度
- ✅ 用户可以保存当前场景为模板
  · 基于系统模板创建变体
  · 完全自定义模板
  · 添加描述和标签
- ✅ 模板继承机制
  · 继承系统模板配置
  · 覆盖部分参数
  · 保留继承关系

优先级: P0
工作量: 2.5天
```

**Story 11.7.2: 场景感知分镜模板**

```
作为 漫剧创作者
我想要的分镜模板能智能适配场景类型
以便 减少手动调整工作

AC:
- ✅ 基础镜头模板库
  · 远景-交代环境
  · 全景-展示全身动作
  · 中景-上半身对话
  · 近景-面部表情
  · 特写-细节强调
- ✅ 运镜模板库
  · 推镜头/拉镜头
  · 摇镜头/跟随镜头
- ✅ 叙事模式模板
  · 三镜头法则: 建立→动作→反应
  · 对话序列: A说话→B说话→A反应
  · 动作序列: 准备→执行→结果
  · 情感递进: 平静→冲突→高潮→解决
- ✅ 场景感知智能推荐
  · 根据场景类型推荐镜头组合
  · 根据对话长度调整分镜数量
  · 根据角色数量自动分配镜头
- ✅ 示例推荐
  · 场景: 双人对话
  · 推荐5个分镜:
    1. 中景-A角色说话(2秒)
    2. 近景-B角色倾听(1秒)
    3. 中景-B角色说话(2秒)
    4. 近景-A角色反应(1秒)
    5. 双人全景(2秒)

优先级: P0
工作量: 2天
```

**Story 11.7.3: 双重入口模板管理**

```
作为 漫剧创作者
我想要 既能快速选择模板又能深度管理
以便 平衡效率和灵活性

AC:
- ✅ 创建时内联选择器
  · 创建场景/分镜时弹出
  · 快速预览模板效果
  · 最近使用模板置顶
  · 搜索和筛选功能
  · 一键应用模板
- ✅ 独立模板管理页面
  · 分类浏览所有模板
  · 模板详情和预览
  · 批量导入导出模板
  · 模板使用统计
  · 模板评分和反馈
- ✅ 两个界面数据同步
  · 在管理页面编辑模板
  · 立即在创建选择器中生效
- ✅ 模板收藏功能
  · 收藏常用模板
  · 在选择器中优先显示收藏项

优先级: P1
工作量: 1.5天
```

**Story 11.7.4: 团队内模板分享**

```
作为 团队成员
我想要 与团队成员分享自定义模板
以便 提升团队整体效率

AC:
- ✅ 模板可见性设置
  · 私有模板(仅自己可见)
  · 团队模板(团队内可见)
  · 公共模板(所有用户可见 - 未来)
- ✅ 团队模板库
  · 查看团队成员分享的模板
  · 显示创建者和创建时间
  · 对模板进行评分和评论
- ✅ 模板申请使用
  · 对私有模板发送使用申请
  · 模板创建者批准后可见
- ✅ 模板版本同步
  · 更新模板时通知使用者
  · 支持选择是否采用新版本
- ✅ 模板使用统计
  · 显示每个模板的使用次数
  · 显示最受欢迎的模板

优先级: P1
工作量: 2天
```

**Story 11.7.5: 模板版本管理**

```
作为 漫剧创作者
我想要的模板支持版本管理
以便 安全地迭代优化模板

AC:
- ✅ 保存版本历史
  · 每次修改模板自动创建版本
  · 保留最近10个版本
  · 可添加版本说明
- ✅ 版本对比功能
  · 对比两个版本的配置差异
  · 高亮显示变更内容
  · 并排查看配置对比
- ✅ 版本恢复
  · 一键恢复到历史版本
  · 恢复前确认提示
  · 支持基于旧版本创建新模板
- ✅ 版本发布管理
  · 标记稳定版本
  · 版本号管理(v1.0, v1.1...)
  · 发布说明
- ✅ 版本通知
  · 模板更新时通知使用者
  · 显示版本变更摘要
  · 支持延迟更新

优先级: P1
工作量: 1.5天
```

### UI设计

**混合场景模板选择器（内联）:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎬 创建场景 - 选择模板                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 推荐模板:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⭐ AI推荐: 室内对话 (匹配度: 95%)                  │ │
│ │ 理由: 剧本包含3个角色对话,适合室内场景              │ │
│ │ [使用模板]                                           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 系统模板:                                                │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│ │ 🏠 室内   │ │ ⚔️ 战斗  │ │ 🍷 宴会  │                │
│ │ 对话     │ │ 场景     │ │          │                │
│ │ [预览]   │ │ [预览]   │ │ [预览]   │                │
│ │ [使用]   │ │ [使用]   │ │ [使用]   │                │
│ └──────────┘ └──────────┘ └──────────┘                │
│                                                          │
│ 我的模板:                                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📁 自定义-三国战场 ⭐收藏                            │ │
│ │ 使用: 12次 | [使用] [编辑] [删除]                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [搜索模板...] [筛选: 全部 ▼]                            │
│                                                          │
│ [跳过模板] [管理所有模板 →]                              │
└─────────────────────────────────────────────────────────┘
```

**独立模板管理页面:**
```
┌─────────────────────────────────────────────────────────┐
│ 📚 场景模板库                    [新建模板] [导入] [导出]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 分类: [全部 ▼] [系统预设 ▼] [我的模板 ▼] [团队模板 ▼]  ││
│ 排序: [使用最多 ▼] [最新创建 ▼] [评分最高 ▼]            │
│ 搜索: [________________________] 🔍                    │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🏠 室内对话 - 系统模板 ⭐ v2.1 稳定版              │ │
│ │ ┌─────────┐                                       │ │
│ │ │[预览图] │  使用: 156次 | 评分: ⭐⭐⭐⭐⭐ 4.8  │ │
│ │ └─────────┘                                       │ │
│ │ 描述: 适合室内角色对话、密谋等场景                  │ │
│ │ 包含: 温馨氛围、柔和光照、室内背景                  │ │
│ │                                                       │ │
│ │ 标签: #室内 #对话 #温馨                              │ │
│ │                                                       │ │
│ │ [使用模板] [预览详情] [基于此创建变体] [分享] [历史] │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📁 三国战场 - 我的模板 ⭐ v1.0                      │ │
│ │ ┌─────────┐                                       │ │
│ │ │[预览图] │  使用: 12次 | 团队模板 | [编辑]       │ │
│ │ └─────────┘                                       │ │
│ │ 描述: 三国题材战争场景,适合多人战斗                 │ │
│ │ 创建者: 我 | 2026-02-05                             │ │
│ │                                                       │ │
│ │ [使用模板] [编辑] [分享设置] [版本历史] [删除]       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 显示 1-10 / 共 42 个模板    [< 1] [2] [3] [>]          │
└─────────────────────────────────────────────────────────┘
```

**场景感知分镜推荐界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎯 智能分镜推荐 - 场景1.1: 桃园结义                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 场景类型: [AI识别: 双人对话场景]  置信度: 92%           │
│                                                          │
│ 推荐分镜方案:                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 方案A: 经典对话模式 (推荐 ⭐)                        │ │
│ │                                                       │ │
│ │ 分镜#1: 中景-刘备说话 (2秒)                          │ │
│ │   "二位贤弟,今日桃园相会..."                         │ │
│ │                                                       │ │
│ │ 分镜#2: 近景-关羽倾听 (1秒)                          │ │
│ │   关羽点头,目光坚定                                  │ │
│ │                                                       │ │
│ │ 分镜#3: 中景-关羽说话 (2秒)                          │ │
│ │   "某虽不才,愿随大哥..."                             │ │
│ │                                                       │ │
│ │ 分镜#4: 近景-张飞反应 (1秒)                          │ │
│ │   张飞握拳,热血沸腾                                  │ │
│ │                                                       │ │
│ │ 分镜#5: 双人全景 (2秒)                               │ │
│ │   三人举杯,结义宣誓                                  │ │
│ │                                                       │ │
│ │ 总时长: 8秒 | 分镜数: 5 | 角色: 3人                  │ │
│ │ [应用此方案] [预览效果]                              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 方案B: 情感递进模式                                  │ │
│ │                                                       │ │
│ │ 分镜#1: 远景-环境 (2秒)                              │ │
│ │   桃园环境,春暖花开                                  │ │
│ │                                                       │ │
│ │ 分镜#2: 中景-三人入场 (2秒)                          │ │
│ │   刘关张三人走入桃园                                │ │
│ │                                                       │ │
│ │ ... (共7个分镜)                                      │ │
│ │                                                       │ │
│ │ 总时长: 12秒 | 分镜数: 7 | 情感起伏: 明显           │ │
│ │ [应用此方案] [预览效果]                              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [自定义分镜] [查看其他方案]                              │
└─────────────────────────────────────────────────────────┘
```

**模板版本管理界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 📜 版本历史 - 室内对话模板                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 当前版本: v2.1 (稳定版)  2026-02-06                     │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v2.1 (当前) ⭐  2026-02-06 14:20                    │ │
│ │ 说明: 调整光照参数,更适合日间场景                    │ │
│ │ 变更: +光照强度+10%, +阴影柔和度                    │ │
│ │ [发布说明] [标记为稳定] [回滚到此版本]              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v2.0 (稳定) ⭐   2026-02-05 10:15                   │ │
│ │ 说明: 新增双人对话模板                              │ │
│ │ 变更: +角色数量2, +默认运镜类型                      │ │
│ │ [对比] [基于此创建] [回滚到此版本]                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v1.1 (测试)     2026-02-04 16:30                    │ │
│ │ 说明: 修复背景配置bug                               │ │
│ │ 变更: ~修复背景ID错误                               │ │
│ │ [对比] [基于此创建] [回滚到此版本]                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ v1.0 (初始)     2026-02-01 09:00                    │ │
│ │ 说明: 初始版本                                      │ │
│ │ [对比] [基于此创建] [回滚到此版本]                  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [查看更多历史版本]                                       │
│                                                          │
│ 版本对比: [v2.1] vs [v2.0]                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 配置项          v2.0              v2.1              │ │
│ │ ─────────────────────────────────────────────────   │ │
│ │ 光照强度        80%              90% ⬆️ +10%       │ │
│ │ 阴影柔和度      中               高 ⬆️             │ │
│ │ 背景ID          123              123 (=)            │ │
│ │ 角色数量        2                2 (=)              │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**团队模板分享界面:**
```
┌─────────────────────────────────────────────────────────┐
│ 👥 团队模板库                            [我的分享]     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 团队: 三国制作组  成员: 8人  模板数: 15个                │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📁 三国战场 - 战斗场景模板                         │ │
│ │ ┌─────────┐                                       │ │
│ │ │[预览图] │  创建者: 张三 | 2026-02-05             │ │
│ │ └─────────┘                                       │ │
│ │ 使用: 23次 (团队) | 评分: ⭐⭐⭐⭐ 4.5              │ │
│ │ 描述: 三国题材战争场景,适合多人战斗                 │ │
│ │                                                       │ │
│ │ [使用模板] [添加到收藏] [联系作者] [反馈]            │ │
│ │                                                       │ │
│ │ 评论区:                                              │ │
│ │ · 李四: 很好用,谢谢分享! (2026-02-06) ⭐⭐⭐⭐⭐     │ │
│ │ · 王五: 能否增加夜间版本? (2026-02-06)              │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🏰 宫殿 - 室内场景模板                             │ │
│ │ 创建者: 李四 | 2026-02-04                           │ │
│ │ 使用: 18次 | 评分: ⭐⭐⭐⭐⭐ 5.0                    │ │
│ │ [使用模板] [添加到收藏] [联系作者] [反馈]            │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ [加载更多...]                                            │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

```python
# 场景模板（增强版 - 支持继承和分享）
class SceneTemplate(models.Model):
    """场景模板 v2.0"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    # 基本信息
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    # 模板配置
    template_config = models.JSONField(default=dict)

    # 继承关系 [Round 7新增]
    parent_template = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_templates'
    )
    inherited_fields = models.JSONField(default=list)  # 继承的字段列表

    # 分享设置 [Round 7新增]
    VISIBILITY_CHOICES = (
        ('private', '私有'),
        ('team', '团队'),
        ('public', '公共'),
    )
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')

    # 统计
    usage_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)  # 平均评分
    rating_count = models.IntegerField(default=0)

    # 系统预置
    is_system_template = models.BooleanField(default=False)

    # 创建者 [Round 7新增]
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "场景模板"
        verbose_name_plural = "场景模板"
        ordering = ['-usage_count', 'name']


# 模板版本历史 [Round 7新增]
class SceneTemplateVersion(models.Model):
    """场景模板版本历史"""
    template = models.ForeignKey(SceneTemplate, on_delete=models.CASCADE, related_name='versions')

    version_number = models.CharField(max_length=20)  # "v1.0", "v1.1"
    version_type = models.CharField(max_length=20)  # 'draft'/'stable'/'deprecated'

    # 版本数据快照
    config_snapshot = models.JSONField()

    # 元数据
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_description = models.TextField(blank=True)

    # 发布标记
    is_stable = models.BooleanField(default=False)
    release_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "场景模板版本"
        ordering = ['-created_at']


# 分镜模板（增强版 - 场景感知）
class ShotTemplate(models.Model):
    """分镜模板 v2.0"""
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    # 模板配置
    template_config = models.JSONField(default=dict)

    # 场景感知配置 [Round 7新增]
    applicable_scene_types = models.JSONField(default=list)  # ['dialogue', 'action']
    recommended_character_count = models.IntegerField(default=0)  # 0=不限
    min_dialogue_length = models.IntegerField(default=0)  # 最短对话长度(字数)
    max_dialogue_length = models.IntegerField(default=0)  # 0=不限

    # 推荐权重 [Round 7新增]
    recommendation_weight = models.FloatField(default=1.0)  # AI推荐时的权重

    # 统计
    usage_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)

    is_system_template = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


# 分镜模板版本 [Round 7新增]
class ShotTemplateVersion(models.Model):
    """分镜模板版本历史"""
    template = models.ForeignKey(ShotTemplate, on_delete=models.CASCADE, related_name='versions')

    version_number = models.CharField(max_length=20)
    version_type = models.CharField(max_length=20)

    config_snapshot = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_description = models.TextField(blank=True)

    is_stable = models.BooleanField(default=False)
    release_notes = models.TextField(blank=True)


# 模板使用记录 [Round 7新增]
class TemplateUsageLog(models.Model):
    """模板使用记录"""
    template_type = models.CharField(max_length=20)  # 'scene'/'shot'
    template_id = models.IntegerField()
    template_version = models.CharField(max_length=20)  # 使用时的版本

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    # 应用目标
    applied_to_type = models.CharField(max_length=20)  # 'scene'/'shot'
    applied_to_id = models.IntegerField()

    used_at = models.DateTimeField(auto_now_add=True)


# 模板评分和反馈 [Round 7新增]
class TemplateRating(models.Model):
    """模板评分"""
    template_type = models.CharField(max_length=20)  # 'scene'/'shot'
    template_id = models.IntegerField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1-5星
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['template_type', 'template_id', 'user']]


# 模板分享申请 [Round 7新增]
class TemplateShareRequest(models.Model):
    """模板分享申请"""
    template_type = models.CharField(max_length=20)  # 'scene'/'shot'
    template_id = models.IntegerField()

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_requests')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')

    message = models.TextField(blank=True)

    status = models.CharField(max_length=20)  # 'pending'/'approved'/'rejected'
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
```

### API设计

```
智能模板推荐:
POST   /api/v1/scenes/{id}/recommend-template/
→ {
    "recommended_template": {...},
    "match_score": 0.95,
    "reason": "剧本包含3个角色对话,适合室内场景"
  }

POST   /api/v1/shots/batch/recommend-templates/
  {
    "scene_id": 1,
    "dialogues": [...]
  }
→ {
    "recommendations": [
      {
        "scheme": "经典对话模式",
        "shots": [...],
        "total_duration": 8.0,
        "reason": "适合双人对话场景"
      }
    ]
  }

模板版本管理:
GET    /api/v1/scene-templates/{id}/versions/
POST   /api/v1/scene-templates/{id}/versions/
  {
    "version_number": "v2.0",
    "change_description": "调整光照参数",
    "is_stable": true
  }

GET    /api/v1/scene-templates/{id}/versions/compare/
  ?version1=v2.1&version2=v2.0
→ {
    "differences": [...]
  }

POST   /api/v1/scene-templates/{id}/versions/{version}/rollback/

模板分享:
GET    /api/v1/team-templates/
  ?visibility=team&artwork_id=1

PUT    /api/v1/scene-templates/{id}/share-settings/
  {
    "visibility": "team"
  }

POST   /api/v1/scene-templates/{id}/share-requests/
  {
    "message": "希望能使用这个模板"
  }

PUT    /api/v1/template-share-requests/{id}/respond/
  {
    "status": "approved"
  }

模板评分:
POST   /api/v1/scene-templates/{id}/rate/
  {
    "rating": 5,
    "comment": "很好用"
  }

GET    /api/v1/scene-templates/{id}/comments/
```

### 前端组件示例（Round 7增强）

**AI模板推荐组件:**
```vue
<template>
  <div class="template-recommendation">
    <div class="recommendation-card" v-if="recommendation">
      <div class="recommendation-header">
        <span class="badge">⭐ AI推荐</span>
        <span class="match-score">匹配度: {{ recommendation.match_score }}%</span>
      </div>

      <div class="template-preview">
        <img :src="recommendation.template.thumbnail" />
        <h4>{{ recommendation.template.name }}</h4>
      </div>

      <div class="recommendation-reason">
        <strong>推荐理由:</strong>
        <p>{{ recommendation.reason }}</p>
      </div>

      <div class="template-details">
        <div class="detail-item">
          <span>✓ 适用场景:</span>
          <span>{{ recommendation.template.applicable_scenes.join(', ') }}</span>
        </div>
        <div class="detail-item">
          <span>✓ 推荐角色数:</span>
          <span>{{ recommendation.template.character_count }}人</span>
        </div>
      </div>

      <div class="actions">
        <button @click="applyTemplate" class="btn-primary">
          使用此模板
        </button>
        <button @click="viewDetails" class="btn-secondary">
          查看详情
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    sceneId: Number
  },

  data() {
    return {
      recommendation: null
    }
  },

  async mounted() {
    await this.loadRecommendation()
  },

  methods: {
    async loadRecommendation() {
      const response = await this.$http.post(
        `/api/v1/scenes/${this.sceneId}/recommend-template/`
      )
      this.recommendation = response.data
    },

    async applyTemplate() {
      await this.$http.post(
        `/api/v1/scenes/${this.sceneId}/apply-template/`,
        {
          template_id: this.recommendation.template.id
        }
      )
      this.$message.success('模板应用成功!')
      this.$emit('template-applied')
    },

    viewDetails() {
      this.$emit('view-template-details', this.recommendation.template)
    }
  }
}
</script>
```

**版本历史组件:**
```vue
<template>
  <div class="version-history">
    <div class="version-header">
      <h3>版本历史</h3>
      <span class="current-version">当前版本: {{ currentVersion }}</span>
    </div>

    <div class="version-list">
      <div
        v-for="version in versions"
        :key="version.id"
        class="version-item"
        :class="{ active: version.version_number === currentVersion }"
      >
        <div class="version-info">
          <span class="version-number">{{ version.version_number }}</span>
          <span class="version-date">{{ formatDate(version.created_at) }}</span>
          <span v-if="version.is_stable" class="badge stable">稳定版</span>
        </div>

        <div class="version-description">
          <strong>{{ version.change_description }}</strong>
        </div>

        <div class="version-actions">
          <button
            v-if="version.version_number !== currentVersion"
            @click="rollbackToVersion(version)"
            class="btn-rollback"
          >
            回滚到此版本
          </button>
          <button
            @click="compareVersions(version)"
            class="btn-compare"
          >
            对比
          </button>
          <button
            v-if="!version.is_stable"
            @click="markAsStable(version)"
            class="btn-stable"
          >
            标记为稳定
          </button>
        </div>
      </div>
    </div>

    <!-- 版本对比弹窗 -->
    <el-dialog
      v-if="comparison"
      title="版本对比"
      :visible.sync="showComparison"
      width="800px"
    >
      <div class="comparison-table">
        <table>
          <thead>
            <tr>
              <th>配置项</th>
              <th>{{ comparison.version1 }}</th>
              <th>{{ comparison.version2 }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(diff, key) in comparison.differences" :key="key">
              <td>{{ key }}</td>
              <td :class="getDiffClass(diff.v1, diff.v2)">
                {{ diff.v1 }}
              </td>
              <td :class="getDiffClass(diff.v2, diff.v1)">
                {{ diff.v2 }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-dialog>
  </div>
</template>

<script>
export default {
  props: {
    templateId: Number,
    templateType: String  // 'scene'/'shot'
  },

  data() {
    return {
      versions: [],
      currentVersion: null,
      comparison: null,
      showComparison: false
    }
  },

  async mounted() {
    await this.loadVersions()
  },

  methods: {
    async loadVersions() {
      const response = await this.$http.get(
        `/api/v1/${this.templateType}-templates/${this.templateId}/versions/`
      )
      this.versions = response.data
      this.currentVersion = this.versions.find(v => v.is_current)?.version_number
    },

    async rollbackToVersion(version) {
      await this.$confirm(
        `确定回滚到版本 ${version.version_number}?`,
        '确认回滚'
      )

      await this.$http.post(
        `/api/v1/${this.templateType}-templates/${this.templateId}/versions/${version.id}/rollback/`
      )

      this.$message.success('回滚成功!')
      await this.loadVersions()
    },

    async compareVersions(version) {
      const response = await this.$http.get(
        `/api/v1/${this.templateType}-templates/${this.templateId}/versions/compare/`,
        {
          params: {
            version1: this.currentVersion,
            version2: version.version_number
          }
        }
      )

      this.comparison = response.data
      this.showComparison = true
    },

    getDiffClass(value, otherValue) {
      if (value === otherValue) return ''
      return value > otherValue ? 'increased' : 'decreased'
    }
  }
}
</script>
```

---

## 实施计划 (再次更新)

### 时间线 (5周 - 保持不变)

**Week 1: 资源管理 + 错误处理**
- Day 1-2: CharacterPose/CharacterVoiceConfig 数据模型
- Day 3-4: 角色资产管理后端 API
- Day 5: 角色资产管理前端界面
- Day 6-7: 智能降级机制
- **里程碑:** 资源管理系统可使用

**Week 2: 双栏布局 + 性能优化 + 模板系统**
- Day 1: 双栏布局框架
- Day 2-3: 目录树组件(含懒加载)
- Day 4: 章节级别工作区
- Day 5: 场景级别工作区
- Day 6: 面包屑导航
- Day 6.5: 拖拽创建分镜 (Round 6)
- **新增: Day 6.5-7: 混合场景模板库 (Round 7)**
- Day 7: 集成测试
- **里程碑:** 双栏布局基础功能完成

**Week 3: AI生成 + 批量操作 + 快速创建 + 智能分镜**
- Day 1: AI生成接口(场景+分镜)
- Day 2: 分镜级别工作区
- Day 3-4: 批量操作功能
- Day 5: 快速对话输入模式 (Round 6)
- **新增: Day 5.5: 场景感知分镜模板 (Round 7)**
- Day 6: 批量操作错误报告
- Day 7: 测试和修复
- **里程碑:** 创作工作流可使用

**Week 4: 分镜编辑 + 版本管理 + 用户引导 + 模板管理**
- Day 1-2: 分镜编辑完善
- Day 3-4: 历史版本管理
- Day 5: 用户引导系统
- Day 5.5: 场景模板库 (Round 6)
- **新增: Day 5.5-6: 双重入口模板管理 (Round 7)**
- Day 6: 交互式引导流程
- **新增: Day 6.5: 模板版本管理 (Round 7)**
- Day 7: 测试和优化
- **里程碑:** 编辑和版本管理完成

**Week 5: 数据导入导出 + 可访问性 + 右键菜单 + 团队分享 + 集成测试**
- Day 1-2: 多格式导入/导出
- Day 3: 键盘导航
- Day 4: 屏幕阅读器支持
- Day 4.5: 右键上下文菜单 (Round 6)
- **新增: Day 4.5-5: 团队模板分享 (Round 7)**
- Day 5: 性能优化(缓存、CDN)
- Day 6: 端到端测试
- Day 7: Bug修复和文档
- **里程碑:** Epic 11 完成

**Story统计更新:**
- 原计划: 25个Story
- Round 6新增: 5个Story (11.6.1-11.6.5)
- Round 7新增: 5个Story (11.7.1-11.7.5)
- **总计: 35个Story**

---

**文档维护:** 本文档为可迭代规划文档,后续 Party Mode 讨论将继续更新此文档。

**最后更新:** 2026-02-06 15:20 (Party Mode Round 7)
**更新内容:**
- Round 7 智能模板系统和版本管理
- 混合场景模板库（系统+自定义+AI推荐）
- 场景感知分镜模板（智能适配）
- 双重入口模板管理（内联+独立页面）
- 团队内模板分享（P1优先级）
- 模板版本管理（历史+对比+回滚）

---

## 🎭 Party Mode Round 8: 其他流程和UI优化

基于主人要求"继续优化其他流程和UI细节"，现在开始Round 8讨论！

### 📋 讨论主题：协作功能优化

**协作场景识别：**
- 多人协作编辑同一作品
- 角色分工（编剧/分镜/配音）
- 审阅和批准流程

#### 方案 A: 实时协作编辑

**核心特性：**
- WebSocket实时同步编辑状态
- 显示在线用户和光标位置
- 锁定机制防止冲突
- 编辑冲突自动合并

#### 方案 B: 异步审阅流程

**核心特性：**
- 提交审阅请求
- 批注和评论系统
- 审阅状态追踪
- 批准/拒绝工作流

#### 方案 C: 混合协作模式（推荐）⭐

**核心特性：**
1. **实时协作** - 章节级别锁定，场景/分镜可同时编辑
2. **审阅模式** - 场景提交审阅，分镜级批注
3. **角色权限** - 编剧/分镜师/配音员不同权限
4. **版本追踪** - 谁在何时修改了什么

---

### 📋 讨论主题：移动端支持

#### 方案 A: 响应式Web

**特点：**
- 自适应布局
- 触摸手势支持
- 移动端优化UI

#### 方案 B: 原生App

**特点：**
- iOS/Android独立开发
- 原生性能
- 离线编辑

#### 方案 C: PWA渐进式Web应用（推荐）⭐

**特点：**
- 安装到桌面
- 离线缓存
- 推送通知
- 跨平台一致体验

---

### 📋 讨论主题：国际化（i18n）

#### 方案 A: 中文为主

**特点：**
- 仅支持简体中文
- 降低复杂度

#### 方案 B: 多语言支持（推荐）⭐

**支持语言：**
- 简体中文（默认）
- 繁体中文
- 英文
- 日文

**技术方案：**
- Vue I18n前端国际化
- Django后端国际化
- 用户可切换语言

---

### 📋 讨论主题：高级搜索功能

#### 方案 A: 基础搜索

**功能：**
- 按名称搜索场景/分镜
- 按角色搜索

#### 方案 B: 高级筛选（推荐）⭐

**功能：**
- 全文搜索（对话内容）
- 筛选器：时间/地点/角色
- 标签搜索
- 保存搜索条件
- 搜索历史

---

### 📋 讨论主题：智能助手（AI Chatbot）

#### 方案 A: 内嵌AI助手

**功能：**
- 右下角聊天窗口
- 问答帮助
- 操作指导

#### 方案 B: 上下文AI建议（推荐）⭐

**功能：**
- 基于当前操作提供智能建议
- "这个场景对话过长，建议拆分为2个场景"
- "检测到角色造型不一致，建议统一"
- AI自动优化建议

---

### ❓ 决策问题

**Q1: 协作功能优先级**
- A. P0 必须做 - 实时协作
- B. P1 最好做 - 异步审阅
- C. P2 未来考虑 - 混合协作模式

**Q2: 移动端支持策略**
- A. P1 最好做 - 响应式Web
- B. P2 未来考虑 - 原生App
- C. P1 最好做 - PWA渐进式Web应用

**Q3: 国际化支持**
- A. 不需要 - 仅中文
- B. P2 未来考虑 - 多语言支持

**Q4: 高级搜索功能**
- A. P0 必须做 - 基础搜索
- B. P1 最好做 - 高级筛选

**Q5: AI助手功能**
- A. P1 最好做 - 内嵌AI助手
- B. P2 未来考虑 - 上下文AI建议
- C. 不需要 - 不做AI助手

**Q6: 其他优化方向**
- A. 数据分析和报表
- B. 自动保存和恢复
- C. 快捷键面板
- D. 其他（请说明）

---

请主人做出决策，我将根据您的选择继续深入设计并更新规划文档！🎯

