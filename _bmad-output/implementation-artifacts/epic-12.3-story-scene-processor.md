# Story 12-1.3: 实现场景处理器

> **Epic:** Epic 12 - 章节推进式工作流
> **优先级:** P0
> **预估工作量:** 2天
> **依赖:** 12-1.1, 12-1.2

---

## 📋 需求描述

**用户故事：** 作为工作流引擎，我需要能够处理单个场景的完整生命周期，包括图像生成、音频生成和状态更新。

**功能说明：**
- 实现场景处理服务
- 集成 Shot 内容生成（调用 Epic 10 的本地AI引擎）
- 实现进度追踪和推送
- 支持失败重试

**边界条件：**
- 不包含工作流编排逻辑
- 不包含 UI 组件
- 只处理单个场景

**验收标准：**
- [ ] 场景处理服务可执行
- [ ] 进度通过 WebSocket 推送
- [ ] 失败场景支持重试
- [ ] 集成测试通过

---

## 🔧 技术实现细节

### 场景处理服务

```python
# apps/artworks/services/scene_processor.py

class SceneProcessorService:
    """单场景处理服务"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.workflow = ChapterWorkflow.objects.get(workflow_id=workflow_id)
        self.publisher = RedisStreamPublisher()

    def process_scene(self, scene_id: int) -> dict:
        """处理单个场景

        工作流：
            1. 更新工作流状态为 running
            2. 获取场景的所有 Shot
            3. 依次处理每个 Shot：
               - 生成图像（调用 Shot 生成服务）
               - 生成音频（调用 TTS 服务）
               - 更新 Shot 状态
            4. 推送进度更新
            5. 标记场景为完成
        """
        scenes = ScriptScene.objects.filter(id=scene_id).select_related('chapter')
        if not scenes.exists():
            raise ValueError(f'Scene {scene_id} not found')

        scene = scenes.first()
        shots = scene.shots.all()

        self._publish_event(
            event_type=WorkflowEvent.EventType.SCENE_STARTED,
            scene_id=scene_id,
            message=f'开始处理场景：{scene.title}'
        )

        total_shots = shots.count()
        processed = 0

        for shot in shots:
            try:
                self._process_shot(shot)
                processed += 1

                # 推送进度
                progress = int((processed / total_shots) * 100)
                self._publish_progress(scene_id, progress)

            except Exception as e:
                logger.error(f'Error processing shot {shot.id}: {e}')
                self._publish_event(
                    event_type=WorkflowEvent.EventType.SCENE_FAILED,
                    scene_id=scene_id,
                    message=f'Shot {shot.id} 失败: {str(e)}',
                    metadata={'shot_id': shot.id, 'error': str(e)}
                )
                raise

        # 标记场景完成
        self._publish_event(
            event_type=WorkflowEvent.EventType.SCENE_COMPLETED,
            scene_id=scene_id,
            message=f'场景 {scene.title} 处理完成'
        )

        return {
            'scene_id': scene_id,
            'shots_processed': processed,
            'status': 'completed'
        }

    def _process_shot(self, shot: Shot):
        """处理单个 Shot

        调用 Epic 10 的服务生成内容：
        - generated_image: 调用 ComfyUI 服务
        - generated_audio: 调用 Edge-TTS 服务
        """
        # 调用 Epic 10 的本地 AI 引擎
        from apps.artworks.services.comfyui_service import ComfyUIService
        from apps.artworks.services.tts_service import EdgeTTSService

        # 生成图像
        comfy_service = ComfyUIService()
        image_path = comfy_service.generate_image(
            prompt=shot.prompt,
            character_pose=shot.character_pose
        )
        shot.generated_image = image_path

        # 生成音频
        tts_service = EdgeTTSService()
        audio_path = tts_service.synthesize(
            text=shot.dialogue,
            voice_config=shot.chapter.character_voice_config
        )
        shot.generated_audio = audio_path

        shot.is_generated = True
        shot.generated_at = timezone.now()
        shot.save()

    def _publish_event(self, event_type: str, scene_id: int,
                     message: str, metadata: dict = None):
        """发布工作流事件"""
        WorkflowEvent.objects.create(
            workflow=self.workflow,
            event_type=event_type,
            scene_id=scene_id,
            message=message,
            metadata=metadata or {}
        )

    def _publish_progress(self, scene_id: int, progress: int):
        """推送进度到 Redis"""
        self.publisher.publish(
            channel=f'workflow:{self.workflow_id}',
            message={
                'type': 'scene_progress',
                'scene_id': scene_id,
                'progress': progress,
                'timestamp': timezone.now().isoformat()
            }
        )
```

### Celery 任务

```python
# apps/artworks/tasks.py

@celery_app.task(bind=True, max_retries=3)
def process_scene_task(self, workflow_id: str, scene_id: int):
    """异步处理场景任务"""
    try:
        processor = SceneProcessorService(workflow_id)
        result = processor.process_scene(scene_id)
        return result
    except Exception as exc:
        logger.error(f'Scene processing failed: {exc}')

        # 更新工作流为失败状态
        workflow = ChapterWorkflow.objects.get(workflow_id=workflow_id)
        workflow.status = ChapterWorkflow.Status.FAILED
        workflow.error_message = str(exc)
        workflow.save()

        raise self.retry(exc=exc, countdown=60)
```

### 集成测试

```python
# apps/artworks/tests/test_scene_processor_integration.py

class TestSceneProcessorIntegration(TestCase):
    @pytest.mark.integration
    def test_full_scene_processing(self):
        """测试完整场景处理流程"""
        workflow = ChapterWorkflow.objects.create(chapter=self.chapter)
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            title='测试场景',
            sequence_order=1
        )
        shot = Shot.objects.create(
            scene=scene,
            prompt='一个美丽的风景',
            dialogue='你好，世界'
        )

        processor = SceneProcessorService(workflow.workflow_id)
        result = processor.process_scene(scene.id)

        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['shots_processed'], 1)

        shot.refresh_from_db()
        self.assertTrue(shot.is_generated)
        self.assertIsNotNone(shot.generated_image)
```

---

## 📊 依赖关系

**前置 Story:** 12-1.1, 12-1.2
**阻塞 Story:** 12-1.4

---

## 🎯 成功标准

- [ ] 场景处理服务可独立执行
- [ ] 集成 Epic 10 的 AI 服务
- [ ] 进度推送到 WebSocket
- [ ] 集成测试通过
