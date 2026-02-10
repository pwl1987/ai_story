# Story 11.2.1: ScriptScene 数据模型增强

**用户故事:**
作为漫剧编辑系统，
我需要增强 ScriptScene 数据模型以支持首尾帧、转场配置和场景继承，
以便实现专业的场景转场效果和场景资产复用。

---

## Acceptance Criteria

### [场景1: 首尾帧字段添加]
**Given** 执行数据库迁移命令
**When** 添加 head_frame 和 tail_frame 字段到 ScriptScene 模型
**Then** 两个 ImageField 字段成功创建
**And** head_frame 上传路径为 'scenes/heads/'
**And** tail_frame 上传路径为 'scenes/tails/'
**And** 两个字段都允许为空 (blank=True, null=True)
**And** 迁移文件名为 '0004_add_scene_frames.py'

### [场景2: 转场配置字段添加]
**Given** ScriptScene 模型需要支持转场配置
**When** 添加转场相关字段
**Then** transition_to_next 字段创建 (ForeignKey到self，关联下一个场景)
**And** transition_type 字段创建 (CharField，choices包含fade/dissolve/wipe/cut)
**And** transition_duration 字段创建 (FloatField，默认值1.5秒)
**And** transition_to_next 允许为空 (blank=True, null=True)
**And** transition_type 默认为空字符串
**And** 相关数据库索引创建成功

### [场景3: 场景继承逻辑验证]
**Given** ScriptScene 继承自 TimeStampedModel (不使用 PhysicalScene)
**When** 创建 ScriptScene 实例
**Then** ScriptScene 包含基础字段 (atmosphere, time_of_day, weather)
**And** 字段验证逻辑正常工作
**And** 数据库迁移成功执行

### [场景4: Django Admin 界面支持]
**Given** Django Admin 的 ScriptScene 配置
**When** 编辑 ScriptScene 实例
**Then** Admin 界面显示首尾帧上传控件
**And** Admin 界面显示转场配置表单 (转场目标、类型、时长)
**And** 转场类型使用下拉选择框显示
**And** 转场时长使用数字输入框 (支持小数)
**And** 所有字段都有清晰的中文 label 和 help_text

### [场景5: 字段验证逻辑]
**Given** 用户在 Admin 或 API 中修改 ScriptScene
**When** transition_type 字段设置为非空值
**And** transition_to_next 字段为空
**Then** 模型的 clean() 方法抛出 ValidationError
**And** 错误消息: "设置转场类型时必须指定转场目标场景"
**When** transition_duration 设置为负数或超过10秒
**Then** 验证错误: "转场时长必须在0-10秒之间"

### [场景6: 首尾帧文件上传验证]
**Given** 用户上传 head_frame 或 tail_frame 图片
**When** 文件格式不是 JPG/PNG
**Then** Django 验证器拒绝上传
**And** 错误消息: "只支持 JPG 和 PNG 格式"
**When** 文件大小超过 5MB
**Then** 上传失败并提示文件过大
**And** 错误消息: "图片大小不能超过 5MB"

### [场景7: 转场配置序列化]
**Given** DRF API 返回 ScriptScene 数据
**When** 序列化器包含转场配置
**Then** JSON 响应包含 transition_to_next_id (目标场景ID)
**And** 包含 transition_type (转场类型)
**And** 包含 transition_duration (转场时长)
**And** 包含 head_frame 和 tail_frame 的 URL
**And** 所有字段都是可读可写 (除系统自动生成字段外)

### [场景8: 单元测试覆盖]
**Given** 运行 ScriptScene 模型的单元测试
**When** 测试所有新增功能
**Then** 测试首尾帧字段创建和存储 ✅
**And** 测试转场配置字段创建和存储 ✅
**And** 测试字段验证逻辑 (转场目标、时长范围) ✅
**And** 测试文件上传验证 (格式、大小) ✅
**And** 测试覆盖率 > 85% ✅

---

## Tasks / Subtasks

### 数据模型增强
- [ ] 1.1 在 ScriptScene 模型中添加首尾帧字段 (head_frame, tail_frame)
- [ ] 1.2 在 ScriptScene 模型中添加转场配置字段 (transition_to_next, transition_type, transition_duration)
- [ ] 1.3 定义 TransitionType 文本选择类
- [ ] 1.4 实现模型 clean() 方法验证转场配置
- [ ] 1.5 添加图片格式验证器 (FileExtensionValidator)
- [ ] 1.6 添加时长范围验证器 (MinValueValidator, MaxValueValidator)

### 数据库迁移
- [ ] 2.1 生成数据库迁移文件 (makemigrations)
- 2.2 检查迁移文件内容确认字段定义正确
- 2.3 执行数据库迁移 (migrate)

### Django Admin 配置
- [ ] 3.1 更新 ScriptSceneAdmin 类的 list_display
- [ ] 3.2 更新 ScriptSceneAdmin 类的 fieldsets
- 3.3 添加首尾帧上传控件到 admin 界面
- [ ] 3.4 添加转场配置到 admin 表单

### DRF 序列化器
- [ ] 4.1 更新 ScriptSceneSerializer 包含首尾帧字段
- [ ] 4.2 更新 ScriptSceneSerializer 包含转场配置字段
- [ ] 4.3 更新 ScriptSceneDetailSerializer 包含关联场景信息

### 单元测试
- [ ] 5.1 创建 apps/artworks/tests/test_script_scene_enhanced.py
- [ ] 5.2 测试首尾帧字段创建
- [ ] 5.3 测试转场配置字段
- [ ] 5.4 测试 clean() 验证逻辑
- [ ] 5.5 测试文件上传验证器
- [ ] 5.6 运行测试并确保覆盖率 > 85%

### 集成测试
- [ ] 6.1 测试 API 端点 (GET, PUT)
- [ ] 6.2 测试文件上传 API (首尾帧)

---

## Dev Notes

### 前置条件
- ✅ Django 项目正常运行
- ✅ PIL/Pillow 库已安装 (图片处理)
- ✅ ScriptScene 基础模型存在于 apps/artworks/models.py

### 依赖关系
- 被 Story 11.2.3 依赖 (前端界面需要完整的数据模型)

### 技术实现要点

**数据模型字段定义:**
```python
class ScriptScene(TimeStampedModel):
    # 现有字段...
    chapter = models.ForeignKey(...)
    scene_number = models.IntegerField(...)
    scene_name = models.CharField(...)
    description = models.TextField(...)

    # 首尾帧 (新增)
    head_frame = models.ImageField(
        upload_to='scenes/heads/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        verbose_name=_("首帧"),
        help_text=_("场景首帧图片，用于淡入效果")
    )
    tail_frame = models.ImageField(
        upload_to='scenes/tails/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        verbose_name=_("尾帧"),
        help_text=_("场景尾帧图片，用于淡出效果")
    )

    # 转场配置 (新增)
    class TransitionType(models.TextChoices):
        FADE = 'fade', _('淡入淡出')
        DISSOLVE = 'dissolve', _('溶解')
        WIPE = 'wipe', _('擦除')
        CUT = 'cut', _('切镜')

    transition_to_next = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transition_from_prev',
        verbose_name=_("转场目标"),
        help_text=_("转场到的下一个场景")
    )
    transition_type = models.CharField(
        max_length=20,
        choices=TransitionType.choices,
        blank=True,
        verbose_name=_("转场类型")
    )
    transition_duration = models.FloatField(
        default=1.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name=_("转场时长(秒)"),
        help_text=_("转场动画持续时间，0-10秒")
    )

    def clean(self):
        """验证业务逻辑"""
        from django.core.exceptions import ValidationError
        super().clean()

        # 验证转场配置
        if self.transition_type and not self.transition_to_next:
            raise ValidationError({
                'transition_to_next': _('设置转场类型时必须指定转场目标场景')
            })
```

### 关键文件路径

**模型文件:**
- `backend/apps/artworks/models.py` - ScriptScene 模型定义

**迁移文件:**
- `backend/apps/artworks/migrations/0004_add_scene_frames.py` - 首尾帧字段

**Admin 配置:**
- `backend/apps/artworks/admin.py` - ScriptSceneAdmin 类

**序列化器:**
- `backend/apps/artworks/serializers.py` - ScriptSceneSerializer

**测试文件:**
- `backend/apps/artworks/tests/test_script_scene_enhanced.py` - 单元测试
- `backend/apps/artworks/tests/test_script_scene_integration.py` - 集成测试

---

## Dev Agent Record

### Implementation Plan

**Phase 1: 数据模型增强 (Day 1)**
1. 在 ScriptScene 模型中添加首尾帧字段
2. 添加转场配置字段
3. 实现 clean() 验证方法
4. 运行 makemigrations 生成迁移文件
5. 运行 migrate 应用迁移

**Phase 2: Admin 和序列化器配置 (Day 1)**
1. 更新 Django Admin 配置
2. 更新 DRF 序列化器
3. 验证 Admin 界面显示正确

**Phase 3: 测试开发 (Day 1-2)**
1. 编写单元测试 (模型、验证逻辑)
2. 编写集成测试 (API、文件上传)
3. 运行测试套件
4. 确保覆盖率 > 85%

### Debug Log

---

### Completion Notes

---

## File List

---

## Change Log

---

## Status

**Status:** ready-for-dev
**Assigned To:**
**Start Date:**
**Completion Date:**
