# 步骤 3: 架构设计

**基于已确认的需求和关键决策**:
- 资源克隆机制（项目级独立）
- 生成后检查（快速迭代）
- 平衡辅助模式（可配置）
- SQLite数据库（可扩展到PostgreSQL）

---

## 📋 架构设计文档

### 文档信息
- **版本**: v1.0
- **状态**: 草案
- **最后更新**: 2026-01-29
- **架构师**: AI Assistant

---

## Part 1: 系统架构总览

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 2.7)                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │资源管理器  │  │分镜编辑器  │  │时间轴编辑  │  │工作流控制  │    │
│  │Resource   │  │Storyboard │  │Timeline   │  │Workflow   │    │
│  │ Manager   │  │  Editor   │  │  Editor   │  │ Controller│    │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                        API层 (DRF)                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │资源ViewSet│  │项目ViewSet│  │工作流ViewSet│ │一致性ViewSet│ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      业务逻辑层 (Services)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │资源管理服务  │  │一致性检查  │  │AI辅助服务  │                 │
│  │Resource    │  │Consistency │  │AI Assist   │                 │
│  │Service     │  │Checker     │  │Service     │                 │
│  └────────────┘  └────────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                        领域模型层 (Models)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Character│ │  Scene   │ │   Prop   │ │StylePreset│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                         │
│  │Project   │ │StoryScene│ │AssetClone│                         │
│  └──────────┘ └──────────┘ └──────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      基础设施层 (Infrastructure)                  │
│  SQLite/PostgreSQL │ Redis │ Celery │ Channels │ FileStorage    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 分层职责

#### 前端层 (Vue 2.7)
- **职责**: 用户交互、状态管理、UI渲染
- **技术栈**: Vue 2.7 + Vuex + daisyUI + Tailwind CSS
- **核心组件**:
  - ResourceManager: 资源浏览、克隆、编辑
  - StoryboardEditor: 分镜编辑、AI辅助、批量操作
  - WorkflowController: 分阶段执行、进度监控
  - ConsistencyChecker: 一致性问题展示和修复

#### API层 (DRF)
- **职责**: 请求验证、权限控制、序列化
- **核心ViewSet**:
  - `ResourceViewSet`: 角色管理、场景管理、道具管理
  - `ProjectViewSet`: 项目资源关联、工作流触发
  - `ConsistencyViewSet`: 一致性检查触发、问题查询

#### 业务逻辑层 (Services)
- **职责**: 业务规则执行、跨模型协调
- **核心服务**:
  - `ResourceService`: 资源克隆逻辑、三级继承
  - `ConsistencyService`: 一致性检查算法
  - `AIAssistantService`: 智能推荐、AI辅助模式

#### 领域模型层 (Models)
- **职责**: 数据持久化、领域规则
- **核心模型**: Character, Scene, Prop, StylePreset, Project, StoryScene

---

## Part 2: 数据模型设计

### 2.1 角色模型 (Character)

```python
# apps/resources/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Character(models.Model):
    """
    角色资源模型
    支持三级继承: 平台级 / 用户级 / 项目级
    """
    RESOURCE_LEVEL_CHOICES = [
        ('platform', '平台级'),
        ('user', '用户级'),
        ('project', '项目级'),
    ]

    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, verbose_name='角色名称')
    display_name = models.CharField(max_length=100, verbose_name='显示名称')
    gender = models.CharField(max_length=20, choices=[('male', '男'), ('female', '女'), ('other', '其他')])

    # 外观描述
    appearance = models.TextField(verbose_name='外观描述', help_text='详细的容貌、体型描述')
    height = models.CharField(max_length=50, blank=True, verbose_name='身高')
    body_type = models.CharField(max_length=50, blank=True, verbose_name='体型')

    # 服装
    default_outfit = models.TextField(verbose_name='默认服装', help_text='默认穿着的服装描述')
    accessories = models.TextField(blank=True, verbose_name='配饰', help_text='常用配饰')

    # 性格
    personality = models.TextField(verbose_name='性格特征', help_text='性格特点、行为习惯')
    mannerisms = models.TextField(blank=True, verbose_name='习惯动作', help_text='标志性动作或口头禅')

    # 声音
    voice_description = models.TextField(blank=True, verbose_name='声音描述', help_text='音色、语调特点')

    # 一致性配置
    face_seed = models.CharField(max_length=100, blank=True, verbose_name='面部种子', help_text='AI生成面部的随机种子')
    hair_color = models.CharField(max_length=50, blank=True, verbose_name='发色')
    eye_color = models.CharField(max_length=50, blank=True, verbose_name='瞳色')

    # 参考图片
    reference_images = models.JSONField(default=list, verbose_name='参考图片URLs')

    # 资源层级
    resource_level = models.CharField(max_length=20, choices=RESOURCE_LEVEL_CHOICES, default='user')

    # 所属关系
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='characters', null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='characters', null=True, blank=True)

    # 克隆追踪
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 元数据
    tags = models.JSONField(default=list, verbose_name='标签')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'resource_characters'
        verbose_name = '角色资源'
        verbose_name_plural = '角色资源'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.display_name} ({self.get_resource_level_display()})"
```

### 2.2 场景模型 (Scene)

```python
class SceneResource(models.Model):
    """
    场景资源模型
    支持时间/天气变体
    """
    RESOURCE_LEVEL_CHOICES = [
        ('platform', '平台级'),
        ('user', '用户级'),
        ('project', '项目级'),
    ]

    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, verbose_name='场景名称')
    scene_type = models.CharField(max_length=50, verbose_name='场景类型', help_text='如: 古镇、森林、室内')

    # 环境描述
    environment = models.TextField(verbose_name='环境描述')
    atmosphere = models.TextField(verbose_name='氛围描述', help_text='情感氛围、色调倾向')

    # 时间设定
    time_of_day = models.CharField(max_length=50, verbose_name='默认时间', help_text='如: 清晨、正午、黄昏')
    weather = models.CharField(max_length=50, verbose_name='默认天气', help_text='如: 晴朗、雨天、雪天')

    # 视觉元素
    architecture_style = models.CharField(max_length=100, blank=True, verbose_name='建筑风格')
    color_palette = models.JSONField(default=list, verbose_name='色调配置', help_text='HEX颜色列表')
    key_elements = models.TextField(blank=True, verbose_name='关键元素', help_text='场景中的标志性物体')

    # 推荐镜头
    recommended_shots = models.JSONField(default=list, verbose_name='推荐镜头类型', help_text='如: ["广角", "特写"]')

    # 参考图片
    reference_images = models.JSONField(default=list, verbose_name='参考图片URLs')

    # 一致性配置
    style_seed = models.CharField(max_length=100, blank=True, verbose_name='风格种子')
    art_style = models.CharField(max_length=50, blank=True, verbose_name='艺术风格', help_text='如: 写实、水墨、动漫')

    # 时间变体
    time_variations = models.JSONField(default=dict, verbose_name='时间变体配置', help_text='{"morning": {...}, "night": {...}}')

    # 天气变体
    weather_variations = models.JSONField(default=dict, verbose_name='天气变体配置')

    # 资源层级
    resource_level = models.CharField(max_length=20, choices=RESOURCE_LEVEL_CHOICES, default='user')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scenes', null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='scenes', null=True, blank=True)

    # 克隆追踪
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 元数据
    tags = models.JSONField(default=list, verbose_name='标签')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'resource_scenes'
        verbose_name = '场景资源'
        verbose_name_plural = '场景资源'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_resource_level_display()})"
```

### 2.3 道具模型 (Prop)

```python
class Prop(models.Model):
    """
    道具资源模型
    支持状态追踪
    """
    RESOURCE_LEVEL_CHOICES = [
        ('platform', '平台级'),
        ('user', '用户级'),
        ('project', '项目级'),
    ]

    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, verbose_name='道具名称')
    prop_type = models.CharField(max_length=50, verbose_name='道具类型', help_text='如: 武器、饰品、工具')

    # 外观
    appearance = models.TextField(verbose_name='外观描述')
    material = models.CharField(max_length=50, blank=True, verbose_name='材质')
    size = models.CharField(max_length=50, blank=True, verbose_name='尺寸')
    weight = models.CharField(max_length=50, blank=True, verbose_name='重量')

    # 功能
    purpose = models.TextField(verbose_name='用途描述')
    special_features = models.TextField(blank=True, verbose_name='特殊功能')

    # 持有者
    default_holder = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='default_props', verbose_name='默认持有者')

    # 状态变化
    state_changes = models.JSONField(default=list, verbose_name='状态变化记录',
                                     help_text='[{"scene_number": 3, "state": "破损"}]')

    # 参考图片
    reference_images = models.JSONField(default=list, verbose_name='参考图片URLs')

    # 资源层级
    resource_level = models.CharField(max_length=20, choices=RESOURCE_LEVEL_CHOICES, default='user')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='props', null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='props', null=True, blank=True)

    # 克隆追踪
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 元数据
    tags = models.JSONField(default=list, verbose_name='标签')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'resource_props'
        verbose_name = '道具资源'
        verbose_name_plural = '道具资源'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_resource_level_display()})"
```

### 2.4 风格预设模型 (StylePreset)

```python
class StylePreset(models.Model):
    """
    风格预设模型
    包含AI生成参数和视觉风格配置
    """
    RESOURCE_LEVEL_CHOICES = [
        ('platform', '平台级'),
        ('user', '用户级'),
        ('project', '项目级'),
    ]

    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, verbose_name='预设名称')
    display_name = models.CharField(max_length=100, verbose_name='显示名称')
    category = models.CharField(max_length=50, verbose_name='分类', help_text='如: 武侠、科幻、童话')

    # AI参数配置
    storyboard_params = models.JSONField(default=dict, verbose_name='分镜生成参数',
                                         help_text='{"narration_style": "...", "visual_prompt_template": "..."}')
    image_generation_params = models.JSONField(default=dict, verbose_name='图生参数',
                                               help_text='{"model": "...", "sampler": "...", "steps": 20, "cfg_scale": 7}')
    video_generation_params = models.JSONField(default=dict, verbose_name='视频生成参数',
                                               help_text='{"motion_bucket_id": 127, "fps": 24}')

    # 颜色配置
    color_palette = models.JSONField(default=list, verbose_name='色调配置', help_text='HEX颜色列表')
    color_grading = models.JSONField(default=dict, verbose_name='调色配置', help_text='{"contrast": 1.2, "saturation": 1.1}')

    # 标签
    tags = models.JSONField(default=list, verbose_name='标签')

    # 资源层级
    resource_level = models.CharField(max_length=20, choices=RESOURCE_LEVEL_CHOICES, default='user')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='style_presets', null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='style_presets', null=True, blank=True)

    # 克隆追踪
    cloned_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='clones')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 元数据
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')

    class Meta:
        db_table = 'resource_style_presets'
        verbose_name = '风格预设'
        verbose_name_plural = '风格预设'
        ordering = ['-usage_count', '-created_at']

    def __str__(self):
        return f"{self.display_name} ({self.get_resource_level_display()})"
```

### 2.5 角色关系模型 (CharacterRelationship)

```python
class CharacterRelationship(models.Model):
    """
    角色关系模型
    定义角色间的社会关系
    """
    RELATIONSHIP_TYPES = [
        ('friend', '朋友'),
        ('enemy', '敌人'),
        ('mentor', '师徒'),
        ('family', '家人'),
        ('lover', '恋人'),
        ('stranger', '陌生人'),
        ('rival', '竞争对手'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # 关系双方
    character_from = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='relationships_from')
    character_to = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='relationships_to')

    # 关系类型和描述
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    description = models.TextField(blank=True, verbose_name='关系描述')

    # 项目关联
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='character_relationships')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'character_relationships'
        verbose_name = '角色关系'
        verbose_name_plural = '角色关系'
        unique_together = [['character_from', 'character_to', 'project']]

    def __str__(self):
        return f"{self.character_from.display_name} → {self.character_to.display_name} ({self.get_relationship_type_display()})"
```

### 2.6 项目-资源关联模型 (ProjectResourceAssignment)

```python
class ProjectResourceAssignment(models.Model):
    """
    项目资源分配模型
    记录资源如何应用到项目中
    """
    RESOURCE_TYPES = [
        ('character', '角色'),
        ('scene', '场景'),
        ('prop', '道具'),
        ('style', '风格预设'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # 项目和资源
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='resource_assignments')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    resource_id = models.UUIDField(verbose_name='资源ID')

    # 应用配置
    applied_at_scene = models.IntegerField(verbose_name='应用场景号', help_text='从哪个场景开始应用', null=True, blank=True)
    is_global = models.BooleanField(default=False, verbose_name='全局应用', help_text='是否应用到所有场景')

    # 角色特殊配置
    character_importance = models.CharField(max_length=20, blank=True,
                                           choices=[('protagonist', '主角'), ('supporting', '配角'), ('background', '背景')],
                                           verbose_name='角色重要性')

    # 道具特殊配置
    prop_holder = models.ForeignKey(Character, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='assigned_props', verbose_name='道具持有者')

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_resource_assignments'
        verbose_name = '项目资源分配'
        verbose_name_plural = '项目资源分配'

    def __str__(self):
        return f"{self.project.name} - {self.get_resource_type_display()} ({self.resource_id})"
```

---

## Part 3: API接口设计

### 3.1 资源管理API

#### 资源列表和查询

```
GET /api/v1/resources/characters/
Query Parameters:
  - level: platform/user/project
  - owner_id: UUID
  - project_id: UUID
  - search: string
  - tags: string[]

Response:
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "name": "古代剑客",
      "display_name": "古代剑客",
      "gender": "male",
      "resource_level": "platform",
      "appearance": "...",
      "reference_images": [],
      "tags": ["武侠", "古装"]
    }
  ]
}
```

#### 资源克隆

```
POST /api/v1/resources/characters/{id}/clone_to_project/
Request Body:
{
  "project_id": "uuid",
  "customizations": {
    "appearance": "修改后的外观描述"
  }
}

Response:
{
  "id": "new-uuid",
  "cloned_from": "original-uuid",
  "resource_level": "project",
  "project_id": "uuid"
}
```

#### 资源编辑

```
PUT /api/v1/resources/characters/{id}/
Request Body:
{
  "name": "新名称",
  "appearance": "更新后的外观",
  "reference_images": ["url1", "url2"]
}

Response:
{
  "id": "uuid",
  "updated_at": "2026-01-29T10:00:00Z"
}
```

### 3.2 项目资源关联API

#### 批量添加资源到项目

```
POST /api/v1/projects/{project_id}/resources/batch_assign/
Request Body:
{
  "resources": [
    {
      "resource_type": "character",
      "resource_id": "uuid",
      "character_importance": "protagonist",
      "applied_at_scene": 1
    },
    {
      "resource_type": "scene",
      "resource_id": "uuid",
      "is_global": true
    }
  ]
}

Response:
{
  "created": 2,
  "failed": 0,
  "assignments": [...]
}
```

#### 查询项目资源

```
GET /api/v1/projects/{project_id}/resources/
Query Parameters:
  - resource_type: character/scene/prop/style

Response:
{
  "characters": [...],
  "scenes": [...],
  "props": [...],
  "styles": [...]
}
```

### 3.3 一致性检查API

#### 触发检查

```
POST /api/v1/projects/{project_id}/consistency/check/
Response:
{
  "task_id": "celery-task-id",
  "status": "checking",
  "estimated_time": 5
}
```

#### 获取检查结果

```
GET /api/v1/projects/{project_id}/consistency/report/
Response:
{
  "overall_score": 85,
  "issues": [
    {
      "type": "character_consistency",
      "severity": "high",
      "description": "场景7中的角色面部特征与场景1不一致",
      "location": {
        "stage": "image_generation",
        "scene_number": 7
      },
      "suggestions": [
        "重新生成场景7图片，使用相同的face_seed",
        "手动调整场景7的角色描述"
      ]
    }
  ],
  "checked_at": "2026-01-29T10:00:00Z"
}
```

#### 一键修复

```
POST /api/v1/projects/{project_id}/consistency/fix_issue/
Request Body:
{
  "issue_id": "issue-uuid",
  "fix_type": "regenerate"
}

Response:
{
  "task_id": "celery-task-id",
  "status": "fixing"
}
```

---

## Part 4: 服务层设计

### 4.1 资源管理服务 (ResourceService)

```python
# apps/resources/services.py

from typing import List, Dict, Optional
from django.db import transaction
from .models import Character, SceneResource, Prop, StylePreset, ProjectResourceAssignment

class ResourceService:
    """
    资源管理服务
    职责: 资源克隆、三级继承、资源关联
    """

    @staticmethod
    @transaction.atomic
    def clone_to_project(resource_model, resource_id: str, project_id: str,
                        customizations: Optional[Dict] = None) -> Dict:
        """
        将资源克隆到项目级

        Args:
            resource_model: Character/SceneResource/Prop/StylePreset
            resource_id: 源资源ID
            project_id: 目标项目ID
            customizations: 自定义修改

        Returns:
            克隆后的资源对象
        """
        # 获取源资源
        source_resource = resource_model.objects.get(id=resource_id)

        # 准备克隆数据
        clone_data = {
            field.name: getattr(source_resource, field.name)
            for field in source_resource._meta.fields
            if field.name not in ['id', 'created_at', 'updated_at', 'cloned_from']
        }

        # 更新层级
        clone_data['resource_level'] = 'project'
        clone_data['project_id'] = project_id
        clone_data['cloned_from'] = source_resource

        # 应用自定义
        if customizations:
            clone_data.update(customizations)

        # 创建克隆
        cloned_resource = resource_model.objects.create(**clone_data)

        return {
            'id': str(cloned_resource.id),
            'cloned_from': str(source_resource.id),
            'resource_level': 'project'
        }

    @staticmethod
    def get_available_resources(project_id: str, resource_type: str) -> List[Dict]:
        """
        获取项目可用的资源（平台级 + 用户级 + 项目级）

        Returns:
            按层级分组的资源列表
        """
        from apps.projects.models import Project

        project = Project.objects.get(id=project_id)
        user = project.user

        resource_map = {
            'character': Character,
            'scene': SceneResource,
            'prop': Prop,
            'style': StylePreset
        }

        model = resource_map[resource_type]

        # 获取所有可用资源
        platform_resources = model.objects.filter(resource_level='platform', is_active=True)
        user_resources = model.objects.filter(owner=user, resource_level='user', is_active=True)
        project_resources = model.objects.filter(project=project, resource_level='project', is_active=True)

        return {
            'platform': [r.to_dict() for r in platform_resources],
            'user': [r.to_dict() for r in user_resources],
            'project': [r.to_dict() for r in project_resources]
        }

    @staticmethod
    @transaction.atomic
    def batch_assign_resources(project_id: str, resources: List[Dict]) -> Dict:
        """
        批量分配资源到项目

        Args:
            project_id: 项目ID
            resources: 资源分配列表

        Returns:
            创建成功的分配数量
        """
        assignments_created = 0
        assignments_failed = 0

        for resource_data in resources:
            try:
                ProjectResourceAssignment.objects.create(
                    project_id=project_id,
                    **resource_data
                )
                assignments_created += 1
            except Exception as e:
                assignments_failed += 1
                logger.error(f"Failed to assign resource: {e}")

        return {
            'created': assignments_created,
            'failed': assignments_failed
        }
```

### 4.2 一致性检查服务 (ConsistencyService)

```python
# apps/resources/consistency.py

from typing import List, Dict
from apps.projects.models import Project, StoryScene
from apps.resources.models import Character, SceneResource, Prop

class ConsistencyService:
    """
    一致性检查服务
    职责: 检查角色、场景、道具、时间逻辑的一致性
    """

    def check_project_consistency(self, project_id: str) -> Dict:
        """
        检查项目的整体一致性

        Returns:
            {
                "overall_score": 85,
                "issues": [...],
                "details": {...}
            }
        """
        project = Project.objects.get(id=project_id)

        issues = []

        # 1. 角色一致性检查
        character_issues = self._check_character_consistency(project)
        issues.extend(character_issues)

        # 2. 场景一致性检查
        scene_issues = self._check_scene_consistency(project)
        issues.extend(scene_issues)

        # 3. 道具一致性检查
        prop_issues = self._check_prop_consistency(project)
        issues.extend(prop_issues)

        # 4. 时间逻辑检查
        time_issues = self._check_time_logic(project)
        issues.extend(time_issues)

        # 计算总分
        total_deductions = sum(issue['score_deduction'] for issue in issues)
        overall_score = max(0, 100 - total_deductions)

        return {
            'overall_score': overall_score,
            'issues': issues,
            'details': {
                'character_issues': len(character_issues),
                'scene_issues': len(scene_issues),
                'prop_issues': len(prop_issues),
                'time_issues': len(time_issues)
            }
        }

    def _check_character_consistency(self, project: Project) -> List[Dict]:
        """
        检查角色一致性
        重点: 同一角色在不同场景中的视觉一致性
        """
        issues = []

        # 获取项目中使用的所有角色
        character_assignments = project.resource_assignments.filter(
            resource_type='character'
        )

        for assignment in character_assignments:
            character = Character.objects.get(id=assignment.resource_id)

            # 检查该角色在所有已生成图片的场景中
            scenes = StoryScene.objects.filter(
                project=project,
                image_generated=True
            )

            if not scenes.exists():
                continue

            # 模拟检查: 比较face_seed是否一致
            # 实际实现可能需要图像识别API
            first_scene = scenes.first()
            first_seed = first_scene.metadata.get('character_seeds', {}).get(str(character.id))

            inconsistencies = []
            for scene in scenes:
                current_seed = scene.metadata.get('character_seeds', {}).get(str(character.id))
                if current_seed != first_seed:
                    inconsistencies.append(scene.scene_number)

            if inconsistencies:
                issues.append({
                    'type': 'character_consistency',
                    'severity': 'high',
                    'description': f'角色"{character.display_name}"在场景{inconsistencies}中的面部特征不一致',
                    'character_id': str(character.id),
                    'character_name': character.display_name,
                    'affected_scenes': inconsistencies,
                    'score_deduction': 15,
                    'suggestions': [
                        '重新生成不一致场景的图片，使用相同的face_seed',
                        '手动调整角色描述，强调一致性特征'
                    ]
                })

        return issues

    def _check_scene_consistency(self, project: Project) -> List[Dict]:
        """
        检查场景一致性
        重点: 同一场景在不同场景号中的视觉风格一致性
        """
        issues = []

        # 获取项目中的场景资源
        scene_assignments = project.resource_assignments.filter(
            resource_type='scene'
        )

        for assignment in scene_assignments:
            scene_resource = SceneResource.objects.get(id=assignment.resource_id)

            # 检查使用该场景资源的所有分镜
            story_scenes = StoryScene.objects.filter(
                project=project,
                scene_resource_id=str(scene_resource.id)
            )

            # 比较style_seed
            if story_scenes.count() > 1:
                first_scene = story_scenes.first()
                first_style = first_scene.metadata.get('style_seed')

                inconsistencies = []
                for scene in story_scenes:
                    current_style = scene.metadata.get('style_seed')
                    if current_style != first_style:
                        inconsistencies.append(scene.scene_number)

                if inconsistencies:
                    issues.append({
                        'type': 'scene_consistency',
                        'severity': 'medium',
                        'description': f'场景"{scene_resource.name}"的风格在场景号{inconsistencies}中不一致',
                        'scene_resource_id': str(scene_resource.id),
                        'affected_scenes': inconsistencies,
                        'score_deduction': 10,
                        'suggestions': [
                            '统一使用相同的style_seed',
                            '检查时间/天气变体配置'
                        ]
                    })

        return issues

    def _check_prop_consistency(self, project: Project) -> List[Dict]:
        """
        检查道具一致性
        重点: 道具状态变化的逻辑一致性
        """
        issues = []

        # 获取项目中的道具
        prop_assignments = project.resource_assignments.filter(
            resource_type='prop'
        )

        for assignment in prop_assignments:
            prop = Prop.objects.get(id=assignment.resource_id)

            # 检查道具状态变化逻辑
            state_changes = prop.state_changes

            # 验证状态变化是否递增
            scene_numbers = [change['scene_number'] for change in state_changes]
            if scene_numbers != sorted(scene_numbers):
                issues.append({
                    'type': 'prop_consistency',
                    'severity': 'medium',
                    'description': f'道具"{prop.name}"的状态变化场景号顺序错误',
                    'prop_id': str(prop.id),
                    'prop_name': prop.name,
                    'score_deduction': 8,
                    'suggestions': [
                        '调整状态变化的场景号顺序',
                        '检查剧情逻辑是否合理'
                    ]
                })

        return issues

    def _check_time_logic(self, project: Project) -> List[Dict]:
        """
        检查时间逻辑一致性
        重点: 场景间时间递进的合理性
        """
        issues = []

        # 获取所有分镜，按场景号排序
        story_scenes = StoryScene.objects.filter(
            project=project
        ).order_by('scene_number')

        # 检查时间递进
        for i in range(len(story_scenes) - 1):
            current_scene = story_scenes[i]
            next_scene = story_scenes[i + 1]

            # 获取时间设定
            current_time = current_scene.metadata.get('time_of_day')
            next_time = next_scene.metadata.get('time_of_day')

            # 简单的时间逻辑检查
            time_order = ['morning', 'noon', 'afternoon', 'dusk', 'night', 'midnight']

            if current_time in time_order and next_time in time_order:
                current_index = time_order.index(current_time)
                next_index = time_order.index(next_time)

                # 如果时间倒退（除了特殊情况）
                if next_index < current_index and next_index not in [0, len(time_order) - 1]:
                    issues.append({
                        'type': 'time_logic',
                        'severity': 'low',
                        'description': f'场景{current_scene.scene_number}到{next_scene.scene_number}的时间逻辑不合理',
                        'from_time': current_time,
                        'to_time': next_time,
                        'score_deduction': 5,
                        'suggestions': [
                            '调整时间递进顺序',
                            '添加时间跳转的旁白说明'
                        ]
                    })

        return issues
```

### 4.3 AI辅助服务 (AIAssistantService)

```python
# apps/resources/ai_assistant.py

from typing import List, Dict
from core.ai_client.factory import AIClientFactory

class AIAssistantService:
    """
    AI辅助服务
    职责: 智能推荐、AI辅助编辑
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.factory = AIClientFactory()

    def recommend_resources(self, topic: str) -> Dict:
        """
        基于主题推荐资源

        Returns:
            {
                "characters": [...],
                "scenes": [...],
                "styles": [...]
            }
        """
        # 使用LLM分析主题
        llm_client = self.factory.create_client('llm')

        prompt = f"""
        分析以下主题，推荐适合的角色、场景、风格：

        主题: {topic}

        请以JSON格式返回推荐结果:
        {{
            "characters": ["角色类型1", "角色类型2"],
            "scenes": ["场景类型1", "场景类型2"],
            "styles": ["风格1", "风格2"]
        }}
        """

        response = llm_client.generate(prompt)
        recommendations = json.loads(response.text)

        # 匹配实际资源
        matched_resources = self._match_resources(recommendations)

        return matched_resources

    def _match_resources(self, recommendations: Dict) -> Dict:
        """
        将推荐匹配到实际资源
        """
        from apps.resources.models import Character, SceneResource, StylePreset

        result = {}

        # 匹配角色
        character_types = recommendations.get('characters', [])
        result['characters'] = Character.objects.filter(
            tags__overlap=character_types,
            resource_level__in=['platform', 'user']
        )[:5]

        # 匹配场景
        scene_types = recommendations.get('scenes', [])
        result['scenes'] = SceneResource.objects.filter(
            tags__overlap=scene_types,
            resource_level__in=['platform', 'user']
        )[:5]

        # 匹配风格
        style_categories = recommendations.get('styles', [])
        result['styles'] = StylePreset.objects.filter(
            category__in=style_categories,
            resource_level__in=['platform', 'user']
        )[:3]

        return result

    def optimize_storyboard_text(self, scene_number: int, original_text: str,
                                optimization_type: str = 'polish') -> Dict:
        """
        AI优化分镜文本

        Args:
            scene_number: 场景号
            original_text: 原始文本
            optimization_type: polish(润色)/expand(扩写)/simplify(简化)

        Returns:
            优化后的文本
        """
        llm_client = self.factory.create_client('llm')

        instructions = {
            'polish': '请润色以下文本，使其更加通顺、优美，保持原意不变',
            'expand': '请扩写以下文本，添加更多细节描述',
            'simplify': '请简化以下文本，保留核心信息，去除冗余'
        }

        prompt = f"""
        {instructions[optimization_type]}:

        原文: {original_text}

        返回优化后的文本:
        """

        response = llm_client.generate(prompt)

        return {
            'original_text': original_text,
            'optimized_text': response.text,
            'optimization_type': optimization_type
        }
```

---

## Part 5: 数据库Schema设计

### 5.1 SQLite Schema

```sql
-- 资源表: 角色
CREATE TABLE resource_characters (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    appearance TEXT NOT NULL,
    height VARCHAR(50),
    body_type VARCHAR(50),
    default_outfit TEXT NOT NULL,
    accessories TEXT,
    personality TEXT NOT NULL,
    mannerisms TEXT,
    voice_description TEXT,
    face_seed VARCHAR(100),
    hair_color VARCHAR(50),
    eye_color VARCHAR(50),
    reference_images JSON DEFAULT '[]',
    resource_level VARCHAR(20) DEFAULT 'user',
    owner_id UUID,
    project_id UUID,
    cloned_from_id UUID,
    tags JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users_user(id),
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    FOREIGN KEY (cloned_from_id) REFERENCES resource_characters(id)
);

CREATE INDEX idx_characters_resource_level ON resource_characters(resource_level);
CREATE INDEX idx_characters_owner ON resource_characters(owner_id);
CREATE INDEX idx_characters_project ON resource_characters(project_id);

-- 资源表: 场景
CREATE TABLE resource_scenes (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    scene_type VARCHAR(50) NOT NULL,
    environment TEXT NOT NULL,
    atmosphere TEXT NOT NULL,
    time_of_day VARCHAR(50) NOT NULL,
    weather VARCHAR(50) NOT NULL,
    architecture_style VARCHAR(100),
    color_palette JSON DEFAULT '[]',
    key_elements TEXT,
    recommended_shots JSON DEFAULT '[]',
    reference_images JSON DEFAULT '[]',
    style_seed VARCHAR(100),
    art_style VARCHAR(50),
    time_variations JSON DEFAULT '{}',
    weather_variations JSON DEFAULT '{}',
    resource_level VARCHAR(20) DEFAULT 'user',
    owner_id UUID,
    project_id UUID,
    cloned_from_id UUID,
    tags JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users_user(id),
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    FOREIGN KEY (cloned_from_id) REFERENCES resource_scenes(id)
);

-- 资源表: 道具
CREATE TABLE resource_props (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    prop_type VARCHAR(50) NOT NULL,
    appearance TEXT NOT NULL,
    material VARCHAR(50),
    size VARCHAR(50),
    weight VARCHAR(50),
    purpose TEXT NOT NULL,
    special_features TEXT,
    default_holder_id UUID,
    state_changes JSON DEFAULT '[]',
    reference_images JSON DEFAULT '[]',
    resource_level VARCHAR(20) DEFAULT 'user',
    owner_id UUID,
    project_id UUID,
    cloned_from_id UUID,
    tags JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (default_holder_id) REFERENCES resource_characters(id),
    FOREIGN KEY (owner_id) REFERENCES users_user(id),
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    FOREIGN KEY (cloned_from_id) REFERENCES resource_props(id)
);

-- 资源表: 风格预设
CREATE TABLE resource_style_presets (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    storyboard_params JSON DEFAULT '{}',
    image_generation_params JSON DEFAULT '{}',
    video_generation_params JSON DEFAULT '{}',
    color_palette JSON DEFAULT '[]',
    color_grading JSON DEFAULT '{}',
    tags JSON DEFAULT '[]',
    resource_level VARCHAR(20) DEFAULT 'user',
    owner_id UUID,
    project_id UUID,
    cloned_from_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users_user(id),
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    FOREIGN KEY (cloned_from_id) REFERENCES resource_style_presets(id)
);

CREATE INDEX idx_style_presets_category ON resource_style_presets(category);

-- 角色关系表
CREATE TABLE character_relationships (
    id UUID PRIMARY KEY,
    character_from_id UUID NOT NULL,
    character_to_id UUID NOT NULL,
    relationship_type VARCHAR(20) NOT NULL,
    description TEXT,
    project_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_from_id) REFERENCES resource_characters(id),
    FOREIGN KEY (character_to_id) REFERENCES resource_characters(id),
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    UNIQUE(character_from_id, character_to_id, project_id)
);

-- 项目资源分配表
CREATE TABLE project_resource_assignments (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    resource_type VARCHAR(20) NOT NULL,
    resource_id UUID NOT NULL,
    applied_at_scene INTEGER,
    is_global BOOLEAN DEFAULT FALSE,
    character_importance VARCHAR(20),
    prop_holder_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects_project(id),
    FOREIGN KEY (prop_holder_id) REFERENCES resource_characters(id)
);

CREATE INDEX idx_resource_assignments_project ON project_resource_assignments(project_id);
CREATE INDEX idx_resource_assignments_type ON project_resource_assignments(resource_type, resource_id);
```

### 5.2 PostgreSQL迁移路径

当数据量增长到需要PostgreSQL时:

1. **使用Django的数据库迁移工具**
```bash
python manage.py migrate --database=postgres
```

2. **迁移JSON字段为JSONB**
```sql
ALTER TABLE resource_characters ALTER COLUMN reference_images TYPE JSONB USING reference_images::JSONB;
```

3. **添加全文搜索索引**
```sql
CREATE INDEX idx_characters_name_gin ON resource_characters USING GIN(to_tsvector('english', name));
CREATE INDEX idx_scenes_environment_gin ON resource_scenes USING GIN(to_tsvector('english', environment));
```

---

## Part 6: 前端架构设计

### 6.1 Vuex Store模块

```javascript
// frontend/src/store/modules/resources.js

const state = {
  // 资源库
  characters: {
    platform: [],
    user: [],
    project: []
  },
  scenes: {
    platform: [],
    user: [],
    project: []
  },
  props: {
    platform: [],
    user: [],
    project: []
  },
  styles: {
    platform: [],
    user: [],
    project: []
  },

  // 当前选中的资源
  selectedResources: {
    characters: [],
    scenes: [],
    props: [],
    styles: []
  },

  // 一致性检查结果
  consistencyReport: null,

  // 加载状态
  loading: false,
  error: null
}

const mutations = {
  SET_RESOURCES(state, { type, level, resources }) {
    state[type][level] = resources
  },

  SELECT_RESOURCE(state, { type, resource }) {
    const index = state.selectedResources[type].findIndex(r => r.id === resource.id)
    if (index === -1) {
      state.selectedResources[type].push(resource)
    }
  },

  DESELECT_RESOURCE(state, { type, resourceId }) {
    state.selectedResources[type] = state.selectedResources[type].filter(r => r.id !== resourceId)
  },

  SET_CONSISTENCY_REPORT(state, report) {
    state.consistencyReport = report
  },

  SET_LOADING(state, loading) {
    state.loading = loading
  },

  SET_ERROR(state, error) {
    state.error = error
  }
}

const actions = {
  async loadResources({ commit }, { projectId, type }) {
    commit('SET_LOADING', true)
    try {
      const response = await api.resources.getResources(projectId, type)
      commit('SET_RESOURCES', { type, ...response.data })
    } catch (error) {
      commit('SET_ERROR', error.message)
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async cloneToProject({ dispatch }, { resourceType, resourceId, projectId }) {
    const response = await api.resources.cloneToProject(resourceType, resourceId, projectId)
    await dispatch('loadResources', { projectId, type: resourceType })
    return response.data
  },

  async runConsistencyCheck({ commit }, projectId) {
    commit('SET_LOADING', true)
    try {
      const response = await api.resources.runConsistencyCheck(projectId)
      return response.data
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
```

### 6.2 核心组件设计

#### ResourceManager.vue

```vue
<template>
  <div class="resource-manager">
    <!-- 资源类型标签页 -->
    <b-tabs v-model="activeTab">
      <b-tab-item label="角色" value="characters">
        <resource-browser
          :resources="resources.characters"
          :selected="selectedResources.characters"
          @select="handleSelect"
          @clone="handleClone"
        />
      </b-tab-item>

      <b-tab-item label="场景" value="scenes">
        <resource-browser
          :resources="resources.scenes"
          :selected="selectedResources.scenes"
          @select="handleSelect"
          @clone="handleClone"
        />
      </b-tab-item>

      <!-- 其他标签... -->
    </b-tabs>

    <!-- 资源预览面板 -->
    <resource-preview
      v-if="selectedResource"
      :resource="selectedResource"
      @edit="handleEdit"
    />
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'ResourceManager',

  data() {
    return {
      activeTab: 'characters'
    }
  },

  computed: {
    ...mapState('resources', ['resources', 'selectedResources']),

    selectedResource() {
      return this.selectedResources[this.activeTab][0] || null
    }
  },

  methods: {
    ...mapActions('resources', ['loadResources', 'cloneToProject']),

    handleSelect(resource) {
      this.$store.commit('resources/SELECT_RESOURCE', {
        type: this.activeTab,
        resource
      })
    },

    async handleClone(resource) {
      const projectId = this.$route.params.id
      await this.cloneToProject({
        resourceType: this.activeTab.slice(0, -1), // 移除复数's'
        resourceId: resource.id,
        projectId
      })
      this.$buefy.toast.open({
        message: '资源已克隆到项目',
        type: 'is-success'
      })
    },

    handleEdit(resource) {
      // 打开编辑对话框
      this.$refs.editDialog.open(resource)
    }
  },

  mounted() {
    const projectId = this.$route.params.id
    this.loadResources({ projectId })
  }
}
</script>
```

---

## Part 7: 性能优化策略

### 7.1 数据库优化

1. **索引策略**
```sql
-- 复合索引
CREATE INDEX idx_resource_level_type ON resource_characters(resource_level, is_active);
CREATE INDEX idx_project_resource ON project_resource_assignments(project_id, resource_type, resource_id);
```

2. **查询优化**
```python
# 使用select_related减少查询次数
characters = Character.objects.select_related(
    'owner', 'project', 'cloned_from'
).filter(resource_level='platform')

# 使用prefetch_related优化多对多查询
projects = Project.objects.prefetch_related(
    'resource_assignments__character'
)
```

### 7.2 缓存策略

```python
# apps/resources/services.py

from django.core.cache import cache

class ResourceService:
    @staticmethod
    def get_platform_resources(resource_type: str) -> List[Dict]:
        """
        获取平台级资源（带缓存）
        """
        cache_key = f"platform_resources:{resource_type}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        # 查询数据库
        resources = ResourceService._query_resources(resource_type, 'platform')

        # 缓存1小时
        cache.set(cache_key, resources, 3600)

        return resources
```

### 7.3 异步任务

```python
# apps/resources/tasks.py

from celery import shared_task

@shared_task
def clone_resources_batch(project_id: str, resource_ids: List[str]):
    """
    批量克隆资源（异步）
    """
    for resource_id in resource_ids:
        ResourceService.clone_to_project(...)

@shared_task
def run_consistency_check_async(project_id: str):
    """
    异步执行一致性检查
    """
    service = ConsistencyService()
    report = service.check_project_consistency(project_id)

    # 通过WebSocket推送结果
    from core.redis.publisher import RedisPublisher
    publisher = RedisPublisher()
    publisher.publish(
        channel=f"ai_story:project:{project_id}:consistency",
        message=report
    )

    return report
```

---

## Part 8: 安全性设计

### 8.1 权限控制

```python
# apps/resources/permissions.py

from rest_framework import permissions

class ResourcePermission(permissions.BasePermission):
    """
    资源权限控制
    """

    def has_object_permission(self, request, view, obj):
        # 平台级资源: 所有用户只读
        if obj.resource_level == 'platform':
            return request.method in permissions.SAFE_METHODS

        # 用户级资源: 所有者可读写
        if obj.resource_level == 'user':
            return obj.owner == request.user

        # 项目级资源: 项目成员可读写
        if obj.resource_level == 'project':
            return obj.project.user == request.user

        return False
```

### 8.2 数据隔离

```python
# 确保项目级资源完全隔离
class ProjectResourceAssignment(models.Model):
    class Meta:
        # 每个项目的资源分配独立存储
        db_table = 'project_resource_assignments'

    def save(self, *args, **kwargs):
        # 验证项目权限
        if self.project.user != self.owner:
            raise PermissionError("用户无权为该项目分配资源")
        super().save(*args, **kwargs)
```

---

## Part 9: 部署架构

### 9.1 Docker Compose配置

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    command: uv run daphne config.asgi:application -b 0.0.0.0 -p 8000
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=sqlite:///db.sqlite3
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  celery_worker:
    build: ./backend
    command: uv run celery -A config worker -Q llm,image,video -l info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=sqlite:///db.sqlite3
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:latest
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

---

## 📊 下一步

基于以上架构设计，下一步将：

1. ✅ **创建详细的实施计划** (Step 4)
   - 第一阶段（2周）- 核心基础
   - 第二阶段（3周）- 智能增强
   - 第三阶段（3周）- 高级功能

2. ✅ **设计UI/UX原型**
   - 资源管理器界面
   - 分镜编辑器界面
   - 时间轴编辑器界面

3. ✅ **编写技术风险分析**
   - 识别潜在技术挑战
   - 提供应对方案

**请审阅以上架构设计，如有问题请提出！准备继续下一步了吗？** (输入 Y 继续)
