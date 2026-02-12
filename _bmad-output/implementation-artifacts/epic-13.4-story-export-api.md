# Story 13-1.4: 实现导出配置和触发API

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P0
> **预估工作量:** 1天
> **依赖:** 13.1.2

---

## 📋 需求描述

**用户故事：** 作为前端用户，我需要通过API配置和触发章节视频导出，包括选择分辨率、质量和导出格式。

**功能说明：**
- 实现导出配置API（分辨率/质量/格式）
- 实现导出触发API
- 实现导出状态查询API
- 实现权限控制
- 支持取消导出

**边界条件：**
- 不包含视频合成逻辑
- 不包含 UI 组件
- 只提供 API 接口

**验收标准：**
- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] 参数验证完整
- [ ] API测试通过

---

## 🔧 技术实现细节

### API 端点

```
POST   /api/v1/artworks/chapters/{id}/export/
GET    /api/v1/artworks/exports/{export_id}/status/
DELETE /api/v1/artworks/exports/{export_id}/
GET    /api/v1/artworks/chapters/{id}/exports/
GET    /api/v1/artworks/exports/{export_id}/download/
```

### ViewSet 实现

```python
# apps/artworks/views.py

class ChapterExportViewSet(viewsets.ViewSet):
    """章节导出 ViewSet"""

    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """触发章节导出"""
        chapter = self.get_object()

        # 检查权限
        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 创建导出记录
        export_record = VideoExport.objects.create(
            chapter=chapter,
            resolution=request.data.get('resolution', '1080p'),
            quality=request.data.get('quality', 'high'),
            format=request.data.get('format', 'mp4'),
            status=VideoExport.Status.PENDING
        )

        # 启动异步导出任务
        from apps.artworks.tasks import export_chapter_video_task
        task = export_chapter_video_task.delay(str(export_record.export_id))

        # 记录导出事件
        WorkflowEvent.objects.create(
            workflow=None,
            event_type='export_started',
            message=f'章节 {chapter.title} 开始导出',
            metadata={'export_id': str(export_record.export_id)}
        )

        serializer = VideoExportSerializer(export_record)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def exports(self, request, pk=None):
        """获取章节的导出历史"""
        chapter = self.get_object()

        if chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        exports = VideoExport.objects.filter(
            chapter=chapter
        ).order_by('-created_at')

        serializer = VideoExportSerializer(exports, many=True)
        return Response(serializer.data)


class VideoExportViewSet(viewsets.ReadOnlyModelViewSet):
    """视频导出记录 ViewSet"""

    queryset = VideoExport.objects.all()
    serializer_class = VideoExportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return VideoExport.objects.filter(
            chapter__project__user=user
        ).select_related('chapter')

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取导出状态"""
        export_record = self.get_object()

        # 检查权限
        if export_record.chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = VideoExportSerializer(export_record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消导出"""
        export_record = self.get_object()

        if export_record.chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        if export_record.status not in ['pending', 'processing']:
            return Response(
                {'error': '导出已在进行中或已完成'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 取消 Celery 任务
        celery_app.control.revoke(
            task_id=export_record.celery_task_id,
            terminate=True
        )

        # 更新状态
        export_record.status = VideoExport.Status.CANCELLED
        export_record.save()

        return Response({'message': '导出已取消'})
```

### 序列化器

```python
# apps/artworks/serializers.py

class VideoExportSerializer(serializers.ModelSerializer):
    """视频导出序列化器"""

    class Meta:
        model = VideoExport
        fields = [
            'export_id', 'chapter', 'resolution', 'quality',
            'format', 'status', 'progress_percentage',
            'output_file', 'file_size', 'duration_seconds',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['export_id']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 添加显示名称
        data['status_display'] = instance.get_status_display()
        data['resolution_display'] = instance.get_resolution_display()
        data['quality_display'] = instance.get_quality_display()
        data['chapter_title'] = instance.chapter.title

        # 添加文件大小显示
        if instance.file_size:
            data['file_size_display'] = self._format_file_size(instance.file_size)
        else:
            data['file_size_display'] = None

        return data

    def _format_file_size(self, bytes_size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f'{bytes_size} {unit}'
            bytes_size /= 1024
        return f'{bytes_size:.1f} TB'
```

### API 测试

```python
# apps/artworks/tests/test_export_api.py

class TestExportAPI(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.client.force_authenticate(user=self.user)
        self.chapter = Chapter.objects.create(
            project=Project.objects.create(user=self.user),
            title='测试章节'
        )

    def test_create_export(self):
        """测试创建导出"""
        url = reverse('chapter-export', kwargs={'pk': self.chapter.id})
        data = {
            'resolution': '1080p',
            'quality': 'high',
            'format': 'mp4'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 202)
        self.assertIn('export_id', response.data)

    def test_export_status(self):
        """测试查询导出状态"""
        export = VideoExport.objects.create(chapter=self.chapter)

        url = reverse('export-status', kwargs={'pk': export.export_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('progress_percentage', response.data)
```

---

## 📊 依赖关系

**前置 Story:** 13.1.2
**阻塞 Story:** 13-2.1, 13-2.2

---

## 🎯 成功标准

- [ ] 所有API端点可访问
- [ ] 权限控制正确
- [ ] 参数验证完整
- [ ] API测试通过
