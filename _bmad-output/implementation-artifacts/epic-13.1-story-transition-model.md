# Story 13-1.1: 创建转场配置数据模型

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P0
> **预估工作量:** 0.5天
> **依赖:** 无

---

## 📋 需求描述

**用户故事：** 作为开发者，我需要定义转场配置的数据模型，以便系统能够存储和应用场景间的转场效果。

**功能说明：**
- 定义转场类型枚举
- 创建 SceneTransition 模型
- 扩展 ScriptScene 模型添加转场字段
- 添加 Django Admin 配置

**边界条件：**
- 不包含转场应用逻辑
- 不包含 UI 组件
- 只定义数据结构

**验收标准：**
- [ ] 转场类型枚举定义完整
- [ ] SceneTransition 模型创建成功
- [ ] ScriptScene 模型扩展完成
- [ ] 数据库迁移执行成功
- [ ] 单元测试通过

---

## 🔧 技术实现细节

### 转场类型常量

```python
# apps/artworks/constants.py

TRANSITION_TYPES = [
    ('none', '无转场'),
    ('fade', '淡入淡出'),
    ('dissolve', '溶解'),
    ('wipe', '擦除'),
    ('slide', '滑动'),
    ('zoom', '缩放'),
]

TRANSITION_DURATION_DEFAULT = 1.0  # 默认1秒
TRANSITION_DURATION_MIN = 0.5
TRANSITION_DURATION_MAX = 5.0

# 转场方向
TRANSITION_DIRECTION = [
    ('forward', '正向'),
    ('backward', '反向'),
]
```

### SceneTransition 模型

```python
# apps/artworks/models.py

class SceneTransition(models.Model):
    """场景转场配置"""

    transition_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_('转场唯一ID')
    )

    # 关联
    from_scene = models.ForeignKey(
        'ScriptScene',
        on_delete=models.CASCADE,
        related_name='transitions_from',
        verbose_name=_('源场景')
    )
    to_scene = models.ForeignKey(
        'ScriptScene',
        on_delete=models.CASCADE,
        related_name='transitions_to',
        verbose_name=_('目标场景')
    )

    # 转场配置
    transition_type = models.CharField(
        max_length=20,
        choices=TRANSITION_TYPES,
        default='fade',
        verbose_name=_('转场类型')
    )
    duration = models.FloatField(
        default=TRANSITION_DURATION_DEFAULT,
        validators=[
            MinValueValidator(TRANSITION_DURATION_MIN),
            MaxValueValidator(TRANSITION_DURATION_MAX)
        ],
        verbose_name=_('转场时长(秒)')
    )
    direction = models.CharField(
        max_length=20,
        choices=TRANSITION_DIRECTION,
        default='forward',
        verbose_name=_('转场方向')
    )

    # 高级选项
    custom_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('自定义参数'),
        help_text=_('转场效果的自定义参数，如擦除方向、滑动角度等')
    )

    # 元数据
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('创建时间')
    )

    class Meta:
        verbose_name = _('场景转场')
        verbose_name_plural = _('场景转场')
        unique_together = [['from_scene', 'to_scene']]
        ordering = ['from_scene__sequence_order', 'to_scene__sequence_order']

    def __str__(self):
        return f'{self.from_scene} → {self.to_scene} ({self.transition_type})'

    def clean(self):
        """验证业务逻辑"""
        from django.core.exceptions import ValidationError

        super().clean()

        # 不能自己转场到自己
        if self.from_scene == self.to_scene:
            raise ValidationError('源场景和目标场景不能相同')

        # 场景必须在同一章节
        if self.from_scene.chapter != self.to_scene.chapter:
            raise ValidationError('转场场景必须在同一章节')

        # 验证转场时长
        if self.duration < TRANSITION_DURATION_MIN or self.duration > TRANSITION_DURATION_MAX:
            raise ValidationError(
                f'转场时长必须在 {TRANSITION_DURATION_MIN}-{TRANSITION_DURATION_MAX} 秒之间'
            )
```

### 扩展 ScriptScene 模型

```python
# apps/artworks/models.py - 扩展现有模型

class ScriptScene(models.Model):
    # ... 现有字段 ...

    # 新增转场配置（如果尚未存在）
    transition_to_next = models.ForeignKey(
        'SceneTransition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',  # 不创建反向关系
        verbose_name=_('转场配置'),
        help_text=_('此场景到下一场景的转场效果')
    )

    # 辅助方法
    def get_transition_for_next(self) -> SceneTransition:
        """获取到下一场景的转场配置"""
        if not self.transition_to_next:
            # 尝试查找已存在的转场配置
            next_scene = ScriptScene.objects.filter(
                chapter=self.chapter,
                sequence_order=self.sequence_order + 1
            ).first()

            if next_scene:
                transition, created = SceneTransition.objects.get_or_create(
                    from_scene=self,
                    to_scene=next_scene,
                    defaults={'transition_type': 'fade', 'duration': 1.0}
                )
                return transition
        return self.transition_to_next
```

### Django Admin 配置

```python
# apps/artworks/admin.py

@admin.register(SceneTransition)
class SceneTransitionAdmin(admin.ModelAdmin):
    list_display = [
        'transition_uuid', 'from_scene', 'to_scene',
        'transition_type', 'duration', 'direction'
    ]
    list_filter = ['transition_type', 'direction', 'created_at']
    search_fields = ['transition_uuid', 'from_scene__title', 'to_scene__title']
    readonly_fields = ['transition_uuid']

    fieldsets = (
        (_('基本信息'), {
            'fields': ('from_scene', 'to_scene')
        }),
        (_('转场配置'), {
            'fields': (
                'transition_type', 'duration',
                'direction', 'custom_params'
            )
        }),
    )
```

### 单元测试

```python
# apps/artworks/tests/test_scene_transition.py

class TestSceneTransitionModel(TestCase):
    def test_create_transition(self):
        """测试创建转场"""
        from_scene = ScriptScene.objects.create(sequence_order=1)
        to_scene = ScriptScene.objects.create(sequence_order=2)

        transition = SceneTransition.objects.create(
            from_scene=from_scene,
            to_scene=to_scene,
            transition_type='fade',
            duration=1.5
        )

        self.assertEqual(transition.transition_type, 'fade')
        self.assertEqual(transition.duration, 1.5)

    def test_same_scene_validation(self):
        """测试相同场景验证"""
        scene = ScriptScene.objects.create(sequence_order=1)

        with self.assertRaises(ValidationError):
            transition = SceneTransition(
                from_scene=scene,
                to_scene=scene
            )
            transition.full_clean()  # 手动调用 clean

    def test_duration_validation(self):
        """测试时长验证"""
        from_scene = ScriptScene.objects.create(sequence_order=1)
        to_scene = ScriptScene.objects.create(sequence_order=2)

        # 测试最小值以下
        with self.assertRaises(ValidationError):
            transition = SceneTransition(
                from_scene=from_scene,
                to_scene=to_scene,
                duration=0.3
            )
            transition.full_clean()
```

---

## 📊 依赖关系

**前置 Story:** 无
**阻塞 Story:** 13-1.2, 13-1.3

---

## 🎯 成功标准

- [ ] 转场类型枚举定义完整
- [ ] 数据模型创建成功
- [ ] 数据库迁移执行成功
- [ ] 单元测试通过
