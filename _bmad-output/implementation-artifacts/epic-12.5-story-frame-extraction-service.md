# Story 12-2.1: 实现首尾帧提取服务

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P1
> **预估工作量:** 1.5天
> **依赖:** 12-1.1

---

## 📋 需求描述

**用户故事：** 作为工作流引擎，我需要能够从已生成的视频镜头中自动提取首帧和尾帧，用于转场预览。

**功能说明：**
- 实现首尾帧提取服务
- 从 Shot 生成的视频中提取帧
- 支持自定义帧位置（首帧/尾帧/指定时间戳）
- 存储提取的帧为图片

**边界条件：**
- 不包含视频生成逻辑（由 Epic 10 处理）
- 不包含 UI 组件
- 只提取已存在的视频帧

**验收标准：**
- [ ] 首尾帧提取服务可执行
- [ ] 提取的帧保存为图片
- [ ] 支持批量提取
- [ ] 单元测试通过

---

## 🔧 技术实现细节

### 服务实现

```python
# apps/artworks/services/frame_extraction.py

import cv2
import os
from django.core.files.storage import default_storage

class FrameExtractionService:
    """首尾帧提取服务"""

    def extract_head_frame(
        self,
        video_path: str,
        output_name: str = None
    ) -> str:
        """提取视频首帧

        Args:
            video_path: 视频文件路径
            output_name: 输出文件名

        Returns:
            提取的帧文件路径
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f'Video not found: {video_path}')

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f'Cannot open video: {video_path}')

        # 读取第一帧
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError('Failed to read first frame')

        # 保存帧
        if output_name is None:
            output_name = f'head_frame_{os.path.basename(video_path)}.jpg'

        output_path = os.path.join(
            default_storage.path('frames/'),
            output_name
        )

        cv2.imwrite(output_path, frame)

        return output_path

    def extract_tail_frame(
        self,
        video_path: str,
        output_name: str = None
    ) -> str:
        """提取视频尾帧"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f'Video not found: {video_path}')

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f'Cannot open video: {video_path}')

        # 跳到最后一帧
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError('Failed to read last frame')

        if output_name is None:
            output_name = f'tail_frame_{os.path.basename(video_path)}.jpg'

        output_path = os.path.join(
            default_storage.path('frames/'),
            output_name
        )

        cv2.imwrite(output_path, frame)

        return output_path

    def extract_frame_at_time(
        self,
        video_path: str,
        time_seconds: float,
        output_name: str = None
    ) -> str:
        """提取指定时间点的帧"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f'Video not found: {video_path}')

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f'Cannot open video: {video_path}')

        # 跳到指定时间
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError(f'Failed to read frame at {time_seconds}s')

        if output_name is None:
            output_name = f'frame_{time_seconds}s_{os.path.basename(video_path)}.jpg'

        output_path = os.path.join(
            default_storage.path('frames/'),
            output_name
        )

        cv2.imwrite(output_path, frame)

        return output_path

    def batch_extract_for_scene(self, scene: ScriptScene) -> dict:
        """批量为场景提取所有 Shot 的首尾帧"""
        results = {}

        for shot in scene.shots.all():
            if not shot.generated_video:
                continue

            head_frame = self.extract_head_frame(
                shot.generated_video.path,
                output_name=f'head_shot_{shot.id}.jpg'
            )

            tail_frame = self.extract_tail_frame(
                shot.generated_video.path,
                output_name=f'tail_shot_{shot.id}.jpg'
            )

            # 更新 Shot 模型
            shot.head_frame = head_frame
            shot.tail_frame = tail_frame
            shot.save()

            results[shot.id] = {
                'head_frame': head_frame,
                'tail_frame': tail_frame
            }

        return results
```

### Celery 任务

```python
# apps/artworks/tasks.py

@celery_app.task(bind=True, max_retries=2)
def extract_scene_frames_task(self, scene_id: int):
    """异步提取场景帧任务"""
    scene = ScriptScene.objects.get(id=scene_id)

    service = FrameExtractionService()
    results = service.batch_extract_for_scene(scene)

    return {
        'scene_id': scene_id,
        'shots_processed': len(results),
        'frames': results
    }
```

### API 端点

```python
# apps/artworks/views.py

class ScriptSceneViewSet(viewsets.ModelViewSet):
    """场景 ViewSet（扩展现有）"""

    @action(detail=True, methods=['post'])
    def extract_frames(self, request, pk=None):
        """提取场景首尾帧"""
        scene = self.get_object()

        # 检查权限
        if scene.chapter.project.user != request.user:
            return Response(
                {'error': '无权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 启动异步任务
        from apps.artworks.tasks import extract_scene_frames_task
        task = extract_scene_frames_task.delay(scene.id)

        return Response({
            'message': '帧提取任务已启动',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
```

### 单元测试

```python
# apps/artworks/tests/test_frame_extraction.py

class TestFrameExtractionService(TestCase):
    def setUp(self):
        self.service = FrameExtractionService()
        self.test_video = self._create_test_video()

    def _create_test_video(self):
        """创建测试视频文件"""
        import numpy as np
        output_path = 'test_video.mp4'

        # 生成10帧的测试视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            output_path, fourcc, 10.0, (640, 480), True
        )

        for i in range(10):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (i * 25, 100, 150)  # 渐变色
            out.write(frame)

        out.release()
        return output_path

    def test_extract_head_frame(self):
        """测试提取首帧"""
        output_path = self.service.extract_head_frame(self.test_video)

        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith('.jpg'))

    def test_extract_tail_frame(self):
        """测试提取尾帧"""
        output_path = self.service.extract_tail_frame(self.test_video)

        self.assertTrue(os.path.exists(output_path))

    def test_extract_frame_at_time(self):
        """测试提取指定时间帧"""
        output_path = self.service.extract_frame_at_time(
            self.test_video,
            time_seconds=0.5
        )

        self.assertTrue(os.path.exists(output_path))

    def test_video_not_found(self):
        """测试视频不存在异常"""
        with self.assertRaises(FileNotFoundError):
            self.service.extract_head_frame('non_existent.mp4')

    def tearDown(self):
        if os.path.exists(self.test_video):
            os.remove(self.test_video)
```

---

## 📊 依赖关系

**前置 Story:** 12-1.1
**阻塞 Story:** 无（可并行开发）

---

## 🎯 成功标准

- [ ] 首尾帧提取服务可独立执行
- [ ] 支持 OpenCV 格式
- [ ] 单元测试通过
- [ ] API 端点可访问
