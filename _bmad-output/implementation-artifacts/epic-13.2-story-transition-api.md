# Story 13-1.2: 实现转场配置API

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P0
> **预估工作量:** 1天
> **依赖:** 13-1.1

---

## 📋 需求描述

**用户故事：** 作为前端用户，我需要通过API管理场景间的转场配置，包括创建、更新和删除转场效果。

**功能说明：**
- 实现转场配置 CRUD API
- 实现批量配置转场
- 验证转场参数合法性
- 实现权限控制

**边界条件：**
- 不包含 UI 组件
- 不包含转场渲染逻辑
- 只提供数据接口

**验收标准：**
- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] 参数验证完整
- [ ] API测试通过

---

## 🔧 技术实现细节

### API 端点

```
GET    /api/v1/artworks/transitions/
POST   /api/v1/artworks/transitions/
GET    /api/v1/artworks/transitions/{id}/
PUT    /api/v1/artworks/transitions/{id}/
DELETE /api/v1/artworks/transitions/{id}/
POST   /api/v1/artworks/scenes/{id}/configure-transition/
GET    /api/v1/artworks/scenes/{id}/transition/
```

### ViewSet 实现

```python
# apps/artworks/views.py

from rest_framework import viewsets, status

class SceneTransitionViewSet(viewsets.ModelViewSet):
    """场景转场 ViewSet"""

    queryset = SceneTransition.objects.all()
    serializer_class = SceneTransitionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回用户项目的转场配置"""
        user = self.request.user
        return SceneTransition.objects.filter(
            from_scene__chapter__project__user=user
        ).select_related('from_scene', 'to_scene')

    def perform_create(self, serializer):
        """创建时自动设置章节"""
        # 验证场景属于同一用户
        from_scene = serializer.validated_data['from_scene']
        to_scene = serializer.validated_data['to_scene']

        if from_scene.chapter.project.user != self.request.user:
            raise PermissionDenied('无权限操作此场景')

        if to_scene.chapter.project.user != self.request.user:
            raise PermissionDenied('无权限操作此场景')

        return serializer.save()

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """验证转场效果"""
        transition = self.get_object()

        # 调用验证服务
        from apps.artworks.services.transition_validator import TransitionValidator
        validator = TransitionValidator()

        try:
            result = validator.validate_transition(
                transition_type=transition.transition_type,
                duration=transition.duration,
                custom_params=transition.custom_params
            )
            return Response({
                'valid': True,
                'preview_info': result
            })
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ScriptSceneTransitionViewSet(viewsets.GenericViewSet):
    """场景转场相关操作的 ViewSet"""

    queryset = ScriptScene.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def transition(self, request, pk=None):
        """获取场景的转场配置"""
        scene = self.get_object()

        if scene.chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        transition = scene.transition_to_next

        if not transition:
            # 尝试查找或创建默认配置
            transition = scene.get_transition_for_next()

        serializer = SceneTransitionSerializer(transition)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def configure_transition(self, request, pk=None):
        """配置场景转场"""
        scene = self.get_object()

        if scene.chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 获取下一场景
        next_scene = ScriptScene.objects.filter(
            chapter=scene.chapter,
            sequence_order=scene.sequence_order + 1
        ).first()

        if not next_scene:
            return Response(
                {'error': '没有下一场景'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取或创建转场配置
        transition, created = SceneTransition.objects.get_or_create(
            from_scene=scene,
            to_scene=next_scene,
            defaults=request.data
        )

        # 更新字段
        serializer = SceneTransitionSerializer(
            transition,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 更新场景关联
        scene.transition_to_next = transition
        scene.save()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
```

### 序列化器

```python
# apps/artworks/serializers.py

class SceneTransitionSerializer(serializers.ModelSerializer):
    """转场配置序列化器"""

    class Meta:
        model = SceneTransition
        fields = [
            'transition_uuid', 'from_scene', 'to_scene',
            'transition_type', 'duration', 'direction',
            'custom_params', 'created_at'
        ]
        read_only_fields = ['transition_uuid']

    def validate(self, attrs):
        """验证转场配置"""
        from django.core.exceptions import ValidationError

        # 验证场景不同
        if attrs.get('from_scene') == attrs.get('to_scene'):
            raise ValidationError('源场景和目标场景不能相同')

        # 验证时长
        duration = attrs.get('duration', TRANSITION_DURATION_DEFAULT)
        if duration < TRANSITION_DURATION_MIN or duration > TRANSITION_DURATION_MAX:
            raise ValidationError(
                f'转场时长必须在 {TRANSITION_DURATION_MIN}-{TRANSITION_DURATION_MAX} 秒之间'
            )

        return attrs

    def to_representation(self, instance):
        """增强序列化输出"""
        data = super().to_representation(instance)

        # 添加显示名称
        data['transition_type_display'] = instance.get_transition_type_display()
        data['from_scene_title'] = instance.from_scene.title
        data['to_scene_title'] = instance.to_scene.title
        data['duration_display'] = f'{instance.duration}秒'

        return data
```

### API 测试

```python
# apps/artworks/tests/test_transition_api.py

class TestTransitionAPI(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(user=self.user)
        self.chapter = Chapter.objects.create(project=self.project, title='测试章节')
        self.scene1 = ScriptScene.objects.create(chapter=self.chapter, sequence_order=1)
        self.scene2 = ScriptScene.objects.create(chapter=self.chapter, sequence_order=2)

    def test_create_transition(self):
        """测试创建转场"""
        url = reverse('transition-list')
        data = {
            'from_scene': self.scene1.id,
            'to_scene': self.scene2.id,
            'transition_type': 'fade',
            'duration': 1.5
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['transition_type'], 'fade')

    def test_invalid_duration(self):
        """测试无效时长"""
        url = reverse('transition-list')
        data = {
            'from_scene': self.scene1.id,
            'to_scene': self.scene2.id,
            'transition_type': 'fade',
            'duration': 10.0  # 超过最大值
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        other_user = User.objects.create_user(username='other')
        transition = SceneTransition.objects.create(
            from_scene=self.scene1,
            to_scene=self.scene2
        )

        url = reverse('transition-detail', kwargs={'pk': transition.id})
        self.client.force_authenticate(user=other_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
```

---

## 📊 依赖关系

**前置 Story:** 13.1.1
**阻塞 Story:** 13.1.3

---

## 🎯 成功标准

- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] 参数验证完整
- [ ] API测试通过
