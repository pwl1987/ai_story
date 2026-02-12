# Story 13-2.1: 实现视频合成服务

> **Epic:** Epic 13 - 转场与导出
> **优先级:** P0
> **预估工作量:** 2天
> **依赖:** 13.1.1, 13.1.4

---

## 📋 需求描述

**用户故事：** 作为系统，我需要能够将章节中的所有场景合成为完整的视频，包括应用转场效果和添加字幕。

**功能说明：**
- 实现视频合成服务
- 支持场景拼接
- 支持转场效果应用
- 支持字幕添加
- 支持音频混合

**边界条件：**
- 不包含导出触发逻辑
- 不包含 UI 组件
- 只负责视频合成

**验收标准：**
- [ ] 视频合成服务可执行
- [ ] 支持所有转场类型
- [ ] 字幕正确添加
- [ ] 音频正确混合
- [ ] 单元测试通过

---

## 🔧 技术实现细节

### 视频合成服务

```python
# apps/artworks/services/video_composition.py

from moviepy.editor import (
    VideoFileClip, CompositeVideoClip,
    TextClip, CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.fx.all import fadeout, fadein
import numpy as np

class VideoCompositionService:
    """视频合成服务"""

    def __init__(self):
        self.temp_dir = '/tmp/video_composition/'
        os.makedirs(self.temp_dir, exist_ok=True)

    def compose_chapter_video(
        self,
        chapter_id: int,
        resolution: str = "1080p",
        quality: str = "high",
        output_format: str = "mp4"
    ) -> str:
        """合成章节视频

        Args:
            chapter_id: 章节ID
            resolution: 分辨率 (720p/1080p/4k)
            quality: 质量 (low/medium/high)
            output_format: 输出格式 (mp4/webm)

        Returns:
            output_file_path: 输出文件路径
        """
        chapter = Chapter.objects.get(id=chapter_id)
        scenes = ScriptScene.objects.filter(
            chapter=chapter
        ).prefetch_related('shots').order_by('sequence_order')

        if not scenes.exists():
            raise ValueError(f'Chapter {chapter_id} has no scenes')

        # 第一步：收集所有场景的视频片段
        scene_clips = []
        transitions = []

        for i, scene in enumerate(scenes):
            # 生成单个场景的视频
            scene_clip = self._compose_scene_clip(scene, resolution)
            scene_clips.append(scene_clip)

            # 获取转场配置
            if i < len(scenes) - 1:
                next_scene = scenes[i + 1]
                transition = scene.get_transition_for_next()
                if transition:
                    transitions.append({
                        'from_clip': scene_clip,
                        'to_clip': None,  # 稍后填充
                        'type': transition.transition_type,
                        'duration': transition.duration,
                        'params': transition.custom_params
                    })

        # 第二步：应用转场
        final_clips = []
        for i, clip in enumerate(scene_clips):
            final_clips.append(clip)

            # 在场景之间添加转场
            if i < len(transitions):
                trans_config = transitions[i]
                next_clip = scene_clips[i + 1] if i + 1 < len(scene_clips) else None

                if next_clip:
                    transition_clip = self._create_transition_clip(
                        clip, next_clip, trans_config
                    )
                    final_clips.append(transition_clip)

        # 第三步：拼接所有片段
        from moviepy.editor import concatenate_videoclips
        final_video = concatenate_videoclips(final_clips, method="compose")

        # 第四步：添加字幕
        final_video = self._add_subtitles(final_video, scenes)

        # 第五步：混合音频
        final_video = self._mix_audio(final_video, scenes)

        # 第六步：导出
        output_filename = f'{chapter.title}_export.{output_format}'
        output_path = os.path.join(self.temp_dir, output_filename)

        # 应用质量参数
        crf = self._get_crf_for_quality(quality)

        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            bitrate='8000k' if quality == 'high' else '4000k',
            preset='medium',
            crf=crf
        )

        # 计算文件大小和时长
        file_size = os.path.getsize(output_path)
        duration = final_video.duration

        return output_path, file_size, duration

    def _compose_scene_clip(self, scene: ScriptScene, resolution: str):
        """合成单个场景的视频"""
        shots = scene.shots.filter(is_generated=True)

        if not shots.exists():
            # 如果没有生成的镜头，创建占位符
            duration = 3.0  # 默认3秒
            return ColorClip(
                size=self._get_resolution_size(resolution),
                color=(0, 0, 0),
                duration=duration
            )

        # 拼接镜头
        clip_paths = [shot.generated_video.path for shot in shots if shot.generated_video]

        from moviepy.editor import concatenate_videoclips
        return concatenate_videoclips([
            VideoFileClip(p) for p in clip_paths
        ])

    def _create_transition_clip(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        config: dict
    ) -> VideoClip:
        """创建转场片段"""

        transition_type = config['type']
        duration = config['duration']
        params = config.get('params', {})

        if transition_type == 'fade':
            # 淡入淡出
            return self._fade_transition(from_clip, to_clip, duration)

        elif transition_type == 'dissolve':
            # 溶解
            return self._dissolve_transition(from_clip, to_clip, duration)

        elif transition_type == 'wipe':
            # 擦除
            return self._wipe_transition(from_clip, to_clip, duration, params)

        elif transition_type == 'slide':
            # 滑动
            return self._slide_transition(from_clip, to_clip, duration, params)

        elif transition_type == 'zoom':
            # 缩放
            return self._zoom_transition(from_clip, to_clip, duration, params)

        else:
            # 无转场：直接拼接
            return from_clip

    def _fade_transition(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        duration: float
    ) -> VideoClip:
        """淡入淡出转场"""
        # 淡出
        fade_out = from_clip.fx(fadeout, duration / 2)
        # 淡入
        fade_in = to_clip.fx(fadein, duration / 2)

        # 叠加
        return CompositeVideoClip([fade_out, fade_in]).set_duration(duration)

    def _wipe_transition(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        duration: float,
        params: dict
    ) -> VideoClip:
        """擦除转场"""
        direction = params.get('wipeDirection', 'left')

        # 创建遮罩动画
        def wipe_effect(get_frame, t):
            """擦除效果函数"""
            w, h = from_clip.w, from_clip.h

            if direction == 'left':
                mask = np.zeros((h, w), dtype=float)
                mask[:, :int(w * t)] = 1
            elif direction == 'right':
                mask = np.zeros((h, w), dtype=float)
                mask[:, int(w * (1 - t)):] = 1
            elif direction == 'top':
                mask = np.zeros((h, w), dtype=float)
                mask[:int(h * t), :] = 1
            elif direction == 'bottom':
                mask = np.zeros((h, w), dtype=float)
                mask[int(h * (1 - t)):, :] = 1

            # 应用遮罩
            from_frame = get_frame(t * duration)
            to_frame = to_clip.get_frame(t * duration)

            combined = from_frame * mask + to_frame * (1 - mask)
            return combined

        return from_clip.fl(wipe_effect, duration=duration).set_duration(duration)

    def _slide_transition(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        duration: float,
        params: dict
    ) -> VideoClip:
        """滑动转场"""
        angle = params.get('slideAngle', 0)

        # 创建滑动动画
        def slide_effect(get_frame, t):
            """滑动效果函数"""
            w, h = from_clip.w, from_clip.h

            # 计算滑动偏移
            offset_x = int(w * t * np.cos(np.radians(angle)))
            offset_y = int(h * t * np.sin(np.radians(angle)))

            from_frame = get_frame(t * duration)
            to_frame = to_clip.get_frame(t * duration)

            # 创建组合帧
            combined = np.zeros_like(from_frame)

            # 偏移源图像
            from_y_start = max(0, -offset_y)
            from_y_end = min(h, h - offset_y)

            if from_y_start < from_y_end and from_x_start < from_x_end:
                combined[from_y_start:from_y_end, from_x_start:from_x_end] = \
                    from_frame[from_y_start:from_y_end, from_x_start:from_x_end]

            # 填充目标图像
            to_y_start = max(0, offset_y)
            to_y_end = min(h, h + offset_y)

            to_x_start = max(0, offset_x)
            to_x_end = min(w, w + offset_x)

            if to_y_start < to_y_end and to_x_start < to_x_end:
                combined[to_y_start:to_y_end, to_x_start:to_x_end] = \
                    to_frame[to_y_start:to_y_end, to_x_start:to_x_end]

            return combined

        return from_clip.fl(slide_effect, duration=duration).set_duration(duration)

    def _zoom_transition(
        self,
        from_clip: VideoClip,
        to_clip: VideoClip,
        duration: float,
        params: dict
    ) -> VideoClip:
        """缩放转场"""
        scale = params.get('zoomScale', 1.5)

        def zoom_effect(get_frame, t):
            """缩放效果函数"""
            w, h = from_frame.shape[:2]
            center = (w // 2, h // 2)

            # 计算当前缩放比例
            current_scale = 1 + (scale - 1) * t

            # 应用缩放
            from_zoomed = np.zeros_like(from_frame)
            if current_scale > 0:
                # 缩小
                scaled_w = int(w / current_scale)
                scaled_h = int(h / current_scale)

                # 居中裁剪
                x_start = (w - scaled_w) // 2
                y_start = (h - scaled_h) // 2

                from_scaled = cv2.resize(from_frame, (scaled_w, scaled_h))
                from_zoomed[y_start:y_start+scaled_h, x_start:x_start+scaled_w] = from_scaled

            # 淡入目标场景
            to_frame = to_clip.get_frame(t * duration)
            alpha = t

            # Alpha 混合
            result = from_zoomed * (1 - alpha) + to_frame * alpha
            return result

        return from_clip.fl(zoom_effect, duration=duration).set_duration(duration)

    def _add_subtitles(self, video: VideoClip, scenes: list) -> VideoClip:
        """添加字幕"""
        subtitles = []

        for scene in scenes:
            for shot in scene.shots.all():
                if not shot.dialogue:
                    continue

                # 计算时间（需要累积前面的时长）
                start_time = self._calculate_shot_time(shot, scenes)

                # 创建字幕
                txt_clip = TextClip(
                    shot.dialogue,
                    fontsize=48,
                    color='white',
                    font='SimHei-Normal-STHeiti',
                    stroke_color='black',
                    stroke_width=2
                )

                # 定位字幕（底部居中）
                subtitle = txt_clip.set_position(
                    ('center', video.h - 100)
                ).set_start(start_time).set_duration(shot.duration or 3.0)

                subtitles.append(subtitle)

        # 叠加字幕到视频
        if subtitles:
            from moviepy.video.compositing import CompositeVideoClip
            return CompositeVideoClip([video] + subtitles, size=video.size)

        return video

    def _mix_audio(self, video: VideoClip, scenes: list) -> VideoClip:
        """混合音频"""
        audio_clips = []

        for scene in scenes:
            for shot in scene.shots.all():
                if shot.generated_audio:
                    audio_clip = AudioFileClip(shot.generated_audio.path)
                    audio_clips.append(audio_clip)

        if not audio_clips:
            return video

        # 拼接音频
        from moviepy.audio import CompositeAudioClip
        combined_audio = CompositeAudioClip(audio_clips)

        # 调整视频时长匹配音频
        video_duration = video.duration
        audio_duration = combined_audio.duration

        if audio_duration > video_duration:
            combined_audio = combined_audio.subclip(0, video_duration)
        elif audio_duration < video_duration:
            # 循环音频
            combined_audio = combined_audio.loop(duration=video_duration)

        return video.set_audio(combined_audio)

    def _calculate_shot_time(self, shot: Shot, scenes: list) -> float:
        """计算镜头的开始时间"""
        elapsed = 0.0

        for scene in scenes:
            if scene.sequence_order == shot.scene.sequence_order:
                for s in scene.shots.all():
                    if s.sequence_order < shot.sequence_order:
                        elapsed += s.duration or 3.0
                break
            elapsed += (shot.duration or 3.0)

        return elapsed

    def _get_resolution_size(self, resolution: str) -> tuple:
        """获取分辨率尺寸"""
        sizes = {
            '720p': (1280, 720),
            '1080p': (1920, 1080),
            '4k': (3840, 2160)
        }
        return sizes.get(resolution, (1920, 1080))

    def _get_crf_for_quality(self, quality: str) -> int:
        """获取质量对应的CRF值"""
        crf_map = {
            'low': 28,
            'medium': 23,
            'high': 18
        }
        return crf_map.get(quality, 23)
```

### Celery 任务

```python
# apps/artworks/tasks.py

@celery_app.task(bind=True, max_retries=2)
def export_chapter_video_task(self, export_id: str):
    """异步导出章节视频任务"""
    from apps.artworks.models import VideoExport
    from apps.artworks.services.video_composition import VideoCompositionService

    export_record = VideoExport.objects.get(export_id=export_id)

    try:
        # 更新状态为处理中
        export_record.status = VideoExport.Status.PROCESSING
        export_record.save()

        # 调用合成服务
        service = VideoCompositionService()

        output_path, file_size, duration = service.compose_chapter_video(
            chapter_id=export_record.chapter.id,
            resolution=export_record.resolution,
            quality=export_record.quality,
            output_format=export_record.format
        )

        # 保存输出文件
        from django.core.files import File
        with open(output_path, 'rb') as f:
            export_record.output_file.save(
                f'{export_record.chapter.title}_export.{export_record.format}',
                File(f)
            )

        # 更新记录
        export_record.file_size = file_size
        export_record.duration_seconds = duration
        export_record.status = VideoExport.Status.COMPLETED
        export_record.completed_at = timezone.now()
        export_record.progress_percentage = 100
        export_record.save()

        # 推送完成通知
        from core.redis.publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher()
        publisher.publish(
            channel=f'export:{export_id}',
            message={
                'type': 'export_completed',
                'export_id': export_id,
                'output_file': export_record.output_file.name,
                'file_size': file_size,
                'duration': duration
            }
        )

        return {
            'export_id': export_id,
            'status': 'completed',
            'output_path': output_path
        }

    except Exception as exc:
        logger.error(f'Video export failed: {exc}')

        export_record.status = VideoExport.Status.FAILED
        export_record.error_message = str(exc)
        export_record.save()

        # 推送失败通知
        from core.redis.publisher import RedisStreamPublisher
        publisher = RedisStreamPublisher()
        publisher.publish(
            channel=f'export:{export_id}',
            message={
                'type': 'export_failed',
                'export_id': export_id,
                'error': str(exc)
            }
        )

        raise self.retry(exc=exc, countdown=60)
```

### 单元测试

```python
# apps/artworks/tests/test_video_composition.py

import os
from django.test import TestCase

class TestVideoCompositionService(TestCase):
    def setUp(self):
        self.service = VideoCompositionService()
        self.chapter = Chapter.objects.create(title='测试章节')
        self.scene1 = ScriptScene.objects.create(
            chapter=self.chapter,
            sequence_order=1,
            dialogue='第一句台词'
        )
        self.scene2 = ScriptScene.objects.create(
            chapter=self.chapter,
            sequence_order=2,
            dialogue='第二句台词'
        )

    def test_get_resolution_size(self):
        """测试分辨率尺寸获取"""
        self.assertEqual(
            self.service._get_resolution_size('720p'),
            (1280, 720)
        )
        self.assertEqual(
            self.service._get_resolution_size('1080p'),
            (1920, 1080)
        )

    def test_get_crf_for_quality(self):
        """测试质量CRF获取"""
        self.assertEqual(self.service._get_crf_for_quality('high'), 18)
        self.assertEqual(self.service._get_crf_for_quality('low'), 28)

    @pytest.mark.skipif(
        os.environ.get('SKIP_MOVIEPY_TESTS'),
        reason='MoviePy not available in test environment'
    )
    def test_fade_transition(self):
        """测试淡入淡出转场"""
        # 创建测试片段
        from moviepy.editor import ColorClip
        clip1 = ColorClip(size=(100, 100), color=(255, 0, 0), duration=2)
        clip2 = ColorClip(size=(100, 100), color=(0, 0, 255), duration=2)

        transition = self.service._fade_transition(clip1, clip2, 1.0)

        self.assertIsNotNone(transition)
        self.assertAlmostEqual(transition.duration, 1.0, places=1)

    def test_subtitle_calculation(self):
        """测试字幕时间计算"""
        shot = Shot(sequence_order=1, duration=2.0)
        time = self.service._calculate_shot_time(shot, [self.scene1])
        self.assertAlmostEqual(time, 0.0, places=1)
```

---

## 📊 依赖关系

**前置 Story:** 13.1.1, 13.1.4
**阻塞 Story:** 13.2.2

---

## 🎯 成功标准

- [ ] 视频合成服务可执行
- [ ] 支持所有转场类型
- [ ] 字幕正确添加
- [ ] 音频正确混合
- [ ] 单元测试通过
