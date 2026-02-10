"""
角色资产批量生成单元测试

Story 11.1.4: 角色资产批量生成
"""

import pytest

from apps.artworks.models import (
    CharacterProfile,
    GenerationHistory,
    GenerationProgress,
)


@pytest.mark.django_db
class TestGenerationProgressModel:
    """生成进度模型测试"""

    def test_generation_progress_creation(self, user):
        """测试生成进度创建"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            total_items=10,
        )
        assert str(progress) == "批量生成 - 等待中 (0/10)"
        assert progress.status == "pending"
        assert progress.progress_percentage == 0.0

    def test_generation_progress_update(self, user):
        """测试进度更新"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            total_items=10,
        )

        # 更新进度
        progress.update_progress(completed=5)
        assert progress.completed_items == 5
        assert progress.progress_percentage == 50.0

        # 完成所有任务
        progress.update_progress(completed=5)
        assert progress.status == "completed"
        assert progress.completed_at is not None

    def test_generation_progress_all_types(self, user):
        """测试所有生成类型"""
        types = ["portrait", "voice", "batch", "pose_recommendation"]

        for gen_type in types:
            progress = GenerationProgress.objects.create(
                user=user,
                generation_type=gen_type,
                total_items=1,
            )
            assert progress.generation_type == gen_type

    def test_generation_progress_status_choices(self, user):
        """测试所有状态选项"""
        statuses = ["pending", "processing", "completed", "failed", "cancelled"]

        for status_val in statuses:
            progress = GenerationProgress.objects.create(
                user=user,
                generation_type="batch",
                total_items=1,
                status=status_val,
            )
            assert progress.status == status_val

    def test_generation_progress_with_failures(self, user):
        """测试包含失败的进度"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            total_items=10,
        )

        progress.update_progress(completed=8, failed=2)
        assert progress.completed_items == 8
        assert progress.failed_items == 2
        # 所有项目完成后自动标记为完成
        assert progress.status == "completed"


@pytest.mark.django_db
class TestGenerationHistoryModel:
    """生成历史模型测试"""

    def test_generation_history_creation(self, artwork):
        """测试生成历史创建"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            result_url="http://example.com/image.png",
        )
        assert str(history) == "测试角色 - 立绘 - 未评分"
        assert history.generation_type == "portrait"

    def test_generation_history_rating(self, artwork):
        """测试评分功能"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="voice",
            result_url="http://example.com/audio.mp3",
        )

        # 评分
        history.rate(5, "质量很好")
        history.refresh_from_db()

        assert history.quality_rating == 5
        assert history.user_feedback == "质量很好"

    def test_generation_history_mark_as_used(self, artwork):
        """测试标记为已采用"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            result_url="http://example.com/image.png",
        )

        assert not history.is_used

        history.mark_as_used()
        history.refresh_from_db()

        assert history.is_used

    def test_generation_history_increment_regeneration(self, artwork):
        """测试增加重新生成次数"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            result_url="http://example.com/image.png",
        )

        assert history.regeneration_count == 0

        history.increment_regeneration_count()
        history.refresh_from_db()

        assert history.regeneration_count == 1

    def test_generation_history_all_types(self, artwork):
        """测试所有生成类型"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        types = ["portrait", "voice", "pose_recommendation"]

        for gen_type in types:
            history = GenerationHistory.objects.create(
                character=character,
                generation_type=gen_type,
                result_url=f"http://example.com/{gen_type}.png",
            )
            assert history.generation_type == gen_type

    def test_generation_history_prompt_params(self, artwork):
        """测试提示词参数"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        prompt_params = {
            "pose_type": "casual",
            "prompt": "anime style portrait",
            "width": 512,
            "height": 768,
        }

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            prompt_params=prompt_params,
            result_url="http://example.com/image.png",
        )

        assert history.prompt_params == prompt_params

    def test_generation_history_voice_params(self, artwork):
        """测试音色参数"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        voice_params = {
            "voice_name": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
        }

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="voice",
            voice_params=voice_params,
            result_url="http://example.com/audio.mp3",
        )

        assert history.voice_params == voice_params


@pytest.mark.django_db
class TestBatchGenerationIntegration:
    """批量生成集成测试"""

    def test_character_with_generation_history(self, artwork):
        """测试角色和生成历史关联"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        # 创建多个生成历史
        for i in range(3):
            GenerationHistory.objects.create(
                character=character,
                generation_type="portrait",
                result_url=f"http://example.com/image{i}.png",
                quality_rating=i + 3,
            )

        assert character.generation_history.count() == 3

    def test_user_generation_progress(self, user):
        """测试用户和生成进度关联"""
        for i in range(3):
            GenerationProgress.objects.create(
                user=user,
                generation_type="batch",
                total_items=10 * (i + 1),
            )

        assert user.generation_progress.count() == 3

    def test_progress_with_celery_task_id(self, user):
        """测试Celery任务ID关联"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            total_items=10,
            celery_task_id="abc-123-def",
        )

        assert progress.celery_task_id == "abc-123-def"


@pytest.mark.django_db
class TestGenerationProgressMeta:
    """生成进度Meta配置测试"""

    def test_db_table_name(self):
        """测试数据表名称"""
        assert GenerationProgress._meta.db_table == "generation_progress"

    def test_verbose_name(self):
        """测试verbose名称"""
        assert GenerationProgress._meta.verbose_name == "生成进度"
        assert GenerationProgress._meta.verbose_name_plural == "生成进度"

    def test_ordering(self):
        """测试默认排序"""
        ordering = GenerationProgress._meta.ordering
        assert ordering == ["-created_at"]


@pytest.mark.django_db
class TestGenerationHistoryMeta:
    """生成历史Meta配置测试"""

    def test_db_table_name(self):
        """测试数据表名称"""
        assert GenerationHistory._meta.db_table == "generation_history"

    def test_verbose_name(self):
        """测试verbose名称"""
        assert GenerationHistory._meta.verbose_name == "生成历史"
        assert GenerationHistory._meta.verbose_name_plural == "生成历史"

    def test_ordering(self):
        """测试默认排序"""
        ordering = GenerationHistory._meta.ordering
        assert ordering == ["-created_at"]


@pytest.mark.django_db
class TestGenerationProgressEdgeCases:
    """生成进度边界条件测试"""

    def test_zero_total_items(self, user):
        """测试总项目数为0"""
        progress = GenerationProgress.objects.create(
            user=user,
            generation_type="batch",
            total_items=0,
        )
        assert progress.progress_percentage == 0.0

    def test_invalid_rating_values(self, artwork):
        """测试无效评分值"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            result_url="http://example.com/image.png",
        )

        # 评分模型不限制值，但应用层应该限制
        history.quality_rating = 10  # 无效值，但数据库允许
        history.save()

        assert history.quality_rating == 10


@pytest.mark.django_db
class TestGenerationHistoryEdgeCases:
    """生成历史边界条件测试"""

    def test_empty_params(self, artwork):
        """测试空参数"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            prompt_params={},
            voice_params={},
            result_url="http://example.com/image.png",
        )

        assert history.prompt_params == {}
        assert history.voice_params == {}

    def test_large_params(self, artwork):
        """测试大型参数"""
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="test_char",
            display_name="测试角色",
        )

        large_params = {f"key_{i}": f"value_{i}" * 100 for i in range(10)}

        history = GenerationHistory.objects.create(
            character=character,
            generation_type="portrait",
            prompt_params=large_params,
            result_url="http://example.com/image.png",
        )

        assert len(history.prompt_params) == 10
