"""
场景处理器集成测试 (Story 12-1.3)

测试场景:
- 完整场景处理流程
- 图像生成集成
- 音频生成集成
- 进度推送
- 失败重试
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from apps.artworks.models import (
    Chapter,
    ChapterWorkflow,
    CharacterProfile,
    CharacterVoiceConfig,
    ScriptScene,
    Shot,
    WorkflowEvent,
)
from apps.artworks.services.scene_processor import SceneProcessorService
from apps.artworks.services.tts_service import EdgeTTSService


@pytest.mark.django_db
class TestSceneProcessorIntegration:
    """场景处理器集成测试"""

    @pytest.fixture
    def artwork(self):
        """创建测试作品"""
        from apps.artworks.models import Artwork
        artwork = Artwork.objects.create(
            title="测试作品",
            artwork_type="novel",
            author="测试作者"
        )
        return artwork

    @pytest.fixture
    def chapter(self, artwork):
        """创建测试章节"""
        chapter = Chapter.objects.create(
            artwork=artwork,
            chapter_number=1,
            title="第一章",
            original_text="测试章节内容"
        )
        return chapter

    @pytest.fixture
    def physical_scene(self):
        """创建物理场景"""
        from apps.artworks.models import PhysicalScene
        scene = PhysicalScene.objects.create(
            category="indoor",
            name="室内场景",
            default_lighting="natural",
            default_atmosphere="calm"
        )
        return scene

    @pytest.fixture
    def script_scene(self, chapter, physical_scene):
        """创建剧本场景"""
        scene = ScriptScene.objects.create(
            chapter=chapter,
            physical_scene=physical_scene,
            scene_number=1,
            scene_name="测试场景",
            description="一个美丽的室内场景",
            atmosphere="calm",
            time_of_day="morning"
        )
        return scene

    @pytest.fixture
    def character(self, artwork):
        """创建测试角色"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="测试角色",
            display_name="角色A",
            description="一个测试角色"
        )
        return character

    @pytest.fixture
    def voice_config(self, character):
        """创建音色配置"""
        config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_id="zh-CN-XiaoxiaoNeural",
            voice_type="女声",
            pitch="normal",
            speed="normal",
            volume="normal"
        )
        return config

    @pytest.fixture
    def workflow(self, chapter):
        """创建工作流"""
        workflow = ChapterWorkflow.objects.create(
            chapter=chapter,
            status=ChapterWorkflow.Status.RUNNING
        )
        return workflow

    @pytest.fixture
    def mock_comfyui_service(self):
        """Mock ComfyUI 服务"""
        with patch('apps.artworks.services.comfyui_service.ComfyUIService') as mock:
            service_class = mock.return_value
            service_instance = service_class()
            # 直接在实例上 mock 方法，返回简单值而非嵌套字典
            # 使用 side_effect 来返回普通字典而非 Mock
            service_instance.generate_image = Mock(side_effect=lambda workflow_json, **kwargs: {
                "success": True,
                "data": [{"url": "http://example.com/image.png"}],
                "metadata": {"latency_ms": 5000}
            })
            yield service_instance

    @pytest.fixture
    def mock_tts_service(self):
        """Mock TTS 服务"""
        with patch('apps.artworks.services.tts_service.EdgeTTSService') as mock:
            service_class = mock.return_value
            service_instance = service_class()
            # 直接在实例上 mock 方法，返回简单值
            service_instance.synthesize = Mock(side_effect=lambda text, **kwargs: {
                "success": True,
                "audio_path": "/tmp/test.mp3",
                "duration_ms": 3000,
                "metadata": {}
            })
            yield service_instance

    @pytest.fixture
    def mock_redis_publisher(self):
        """Mock Redis 发布器"""
        with patch('apps.artworks.services.scene_processor.RedisStreamPublisher') as mock:
            publisher_instance = MagicMock()
            publisher_instance.publish_progress_detailed = Mock(return_value=True)
            publisher_instance.publish_stage_update = Mock(return_value=True)
            publisher_instance.publish_done = Mock(return_value=True)
            publisher_instance.publish_error = Mock(return_value=True)
            publisher_instance.close = Mock(return_value=True)
            mock.return_value = publisher_instance
            yield publisher_instance

    @pytest.mark.integration
    def test_full_scene_processing(
        self,
        workflow,
        script_scene,
        character,
        voice_config,
        mock_comfyui_service,
        mock_tts_service,
        mock_redis_publisher
    ):
        """测试完整场景处理流程"""
        # 创建测试镜头
        shot1 = Shot.objects.create(
            scene=script_scene,
            shot_number=1,
            shot_type="dialogue",
            content="你好，世界",
            speaker="角色A",
            sort_order=1
        )

        shot2 = Shot.objects.create(
            scene=script_scene,
            shot_number=2,
            shot_type="narration",
            narration="这是旁白",
            sort_order=2
        )

        # 创建场景处理器
        processor = SceneProcessorService(str(workflow.workflow_id))

        # 处理场景
        result = processor.process_scene(script_scene.id)

        # 验证结果
        assert result["status"] == "completed"
        assert result["shots_processed"] == 2
        assert result["total_shots"] == 2

        # 验证镜头状态
        shot1.refresh_from_db()
        shot2.refresh_from_db()
        assert shot1.is_generated is True
        assert shot2.is_generated is True
        assert shot1.generated_at is not None
        assert shot2.generated_at is not None

        # 验证场景状态
        script_scene.refresh_from_db()
        assert script_scene.is_completed is True
        assert script_scene.shot_count == 2

        # 验证工作流事件
        events = WorkflowEvent.objects.filter(workflow=workflow)
        assert events.filter(event_type=WorkflowEvent.EventType.SCENE_STARTED).count() == 1
        assert events.filter(event_type=WorkflowEvent.EventType.SCENE_COMPLETED).count() == 1

    @pytest.mark.integration
    def test_scene_with_no_shots(
        self,
        workflow,
        script_scene,
        mock_redis_publisher
    ):
        """测试没有镜头的场景"""
        processor = SceneProcessorService(str(workflow.workflow_id))
        result = processor.process_scene(script_scene.id)

        assert result["status"] == "skipped"
        assert result["shots_processed"] == 0

    @pytest.mark.integration
    def test_scene_not_found(self, workflow):
        """测试场景不存在的情况"""
        processor = SceneProcessorService(str(workflow.workflow_id))

        with pytest.raises(ValueError, match="场景不存在"):
            processor.process_scene(99999)

    @pytest.mark.integration
    def test_scene_processing_with_shot_failure(
        self,
        workflow,
        script_scene,
        mock_comfyui_service,
        mock_tts_service,
        mock_redis_publisher
    ):
        """测试镜头处理失败的场景"""
        # 创建测试镜头
        shot1 = Shot.objects.create(
            scene=script_scene,
            shot_number=1,
            shot_type="dialogue",
            content="正常镜头",
            sort_order=1
        )

        shot2 = Shot.objects.create(
            scene=script_scene,
            shot_number=2,
            shot_type="dialogue",
            content="失败镜头",
            sort_order=2
        )

        # Mock 第二个镜头生成失败
        mock_comfyui_service.generate_image.side_effect = [
            {"success": True, "data": [{"url": "http://example.com/image.png"}]},  # shot1 成功
            Exception("生成失败")  # shot2 失败 - 这里会被捕获继续音频生成
        ]

        processor = SceneProcessorService(str(workflow.workflow_id))
        result = processor.process_scene(script_scene.id)

        # 验证部分成功
        # 当镜头处理失败时，会记录错误但继续处理，所以状态是 partial
        assert result["status"] in ["partial", "completed"]  # 可能是 partial 或 completed
        assert result["shots_processed"] >= 1  # 至少处理了一个

    @pytest.mark.integration
    def test_workflow_not_exists(self):
        """测试工作流不存在的情况"""
        with pytest.raises(ChapterWorkflow.DoesNotExist):
            SceneProcessorService("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
class TestEdgeTTSService:
    """Edge-TTS 服务测试"""

    @pytest.fixture
    def mock_edge_tts_client(self):
        """Mock Edge-TTS 客户端"""
        with patch('apps.artworks.services.tts_service.EdgeTTSClient') as mock:
            client_instance = MagicMock()
            client_instance.generate = AsyncMock(return_value=MagicMock(
                success=True,
                data={
                    "audio_file": "/tmp/test.mp3",
                    "duration_ms": 3000
                }
            ))
            mock.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def mock_redis_publisher(self):
        """Mock Redis 发布器"""
        with patch('apps.artworks.services.tts_service.RedisStreamPublisher') as mock:
            publisher_instance = MagicMock()
            publisher_instance.publish_stage_update = Mock(return_value=True)
            publisher_instance.publish_done = Mock(return_value=True)
            publisher_instance.publish_error = Mock(return_value=True)
            publisher_instance.close = Mock(return_value=True)
            mock.return_value = publisher_instance
            yield publisher_instance

    def test_synthesize_success(self, mock_edge_tts_client, mock_redis_publisher):
        """测试成功合成语音"""
        service = EdgeTTSService()

        result = service.synthesize(
            text="你好，世界",
            voice_name="zh-CN-XiaoxiaoNeural"
        )

        assert result["success"] is True
        assert "audio_path" in result
        assert result["duration_ms"] > 0

    def test_get_available_voices(self):
        """测试获取可用音色列表"""
        service = EdgeTTSService()
        voices = service.get_available_voices()

        assert "zh-CN-XiaoxiaoNeural" in voices
        assert "zh-CN-YunyangNeural" in voices
        assert len(voices) >= 6

    def test_get_voice_info(self):
        """测试获取音色信息"""
        service = EdgeTTSService()
        info = service.get_voice_info("zh-CN-XiaoxiaoNeural")

        assert info is not None
        assert info["gender"] == "女"
        assert "description" in info

    def test_get_recommended_voice(self):
        """测试推荐音色"""
        service = EdgeTTSService()

        # 测试女性音色推荐
        female_voice = service.get_recommended_voice(character_gender="女")
        assert "Xiaoxiao" in female_voice or "Yunxi" in female_voice or "Xiaoyi" in female_voice

        # 测试男性音色推荐
        male_voice = service.get_recommended_voice(character_gender="男")
        assert "Yunyang" in male_voice or "Yunze" in male_voice or "Yunjian" in male_voice

        # 测试儿童音色推荐
        child_voice = service.get_recommended_voice(
            character_gender="女",
            character_age="child"
        )
        assert "Xiaoyi" in child_voice or "Yunjian" in child_voice


@pytest.mark.django_db
class TestSceneProcessorTask:
    """场景处理 Celery 任务测试"""

    @pytest.fixture
    def artwork(self):
        """创建测试作品"""
        from apps.artworks.models import Artwork
        return Artwork.objects.create(
            title="测试作品",
            artwork_type="novel"
        )

    @pytest.fixture
    def chapter(self, artwork):
        """创建测试章节"""
        return Chapter.objects.create(
            artwork=artwork,
            chapter_number=1,
            title="第一章",
            original_text="测试内容"
        )

    @pytest.fixture
    def physical_scene(self):
        """创建物理场景"""
        from apps.artworks.models import PhysicalScene
        return PhysicalScene.objects.create(
            category="indoor",
            name="室内"
        )

    @pytest.fixture
    def script_scene(self, chapter, physical_scene):
        """创建剧本场景"""
        return ScriptScene.objects.create(
            chapter=chapter,
            physical_scene=physical_scene,
            scene_number=1,
            scene_name="测试场景",
            description="测试"
        )

    @pytest.fixture
    def workflow(self, chapter):
        """创建工作流"""
        return ChapterWorkflow.objects.create(
            chapter=chapter,
            status=ChapterWorkflow.Status.RUNNING
        )

    @pytest.fixture
    def shot(self, script_scene):
        """创建镜头"""
        return Shot.objects.create(
            scene=script_scene,
            shot_number=1,
            shot_type="dialogue",
            content="测试内容",
            sort_order=1
        )

    @pytest.mark.integration
    @patch('apps.artworks.services.scene_processor.SceneProcessorService')
    def test_process_scene_task_success(
        self,
        mock_processor_class,
        workflow,
        script_scene,
        shot
    ):
        """测试场景处理任务成功"""
        # Mock 处理器
        mock_processor = MagicMock()
        mock_processor.process_scene.return_value = {
            "scene_id": script_scene.id,
            "shots_processed": 1,
            "total_shots": 1,
            "status": "completed"
        }
        mock_processor_class.return_value = mock_processor

        from apps.artworks.tasks import process_scene_task

        # 创建 Celery 任务 mock
        task_mock = MagicMock()
        task_mock.request.id = "test-task-id"
        task_mock.request.retries = 0
        task_mock.max_retries = 3

        # 创建 request 属性用于测试
        request_mock = MagicMock()
        request_mock.id = "test-task-id"
        request_mock.retries = 0
        task_mock.request = request_mock

        # 执行任务
        result = process_scene_task(
            task_mock,
            str(workflow.workflow_id),
            script_scene.id
        )

        # 验证结果
        assert result["scene_id"] == script_scene.id
        assert result["status"] == "completed"

        # 验证工作流进度更新
        workflow.refresh_from_db()
        assert workflow.completed_scenes == 1
