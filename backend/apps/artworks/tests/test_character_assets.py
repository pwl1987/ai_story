"""
单元测试: 角色资产管理 (CharacterPose 和 CharacterVoiceConfig)

Epic 11 Story 11.1.1: CharacterPose 数据模型
Epic 11 Story 11.1.2: CharacterVoiceConfig 数据模型

测试覆盖:
- 模型创建和验证
- 关系验证 (ForeignKey, OneToOne)
- 方法测试 (increment_usage, __str__)
- JSON字段测试
- Django Admin 配置验证
"""

import pytest
from django.db.utils import IntegrityError

from apps.artworks.models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    CharacterVoiceConfig,
)


@pytest.fixture
def artwork(db):
    """创建测试作品"""
    return Artwork.objects.create(
        title="测试作品",
        author="测试作者",
        artwork_type="novel",
    )


@pytest.fixture
def chapter(db, artwork):
    """创建测试章节"""
    return Chapter.objects.create(
        artwork=artwork,
        chapter_number=1,
        title="第一章",
        original_text="测试内容",
    )


@pytest.fixture
def character(db, artwork):
    """创建测试角色"""
    return CharacterProfile.objects.create(
        artwork=artwork,
        name="test_character",
        display_name="测试角色",
        appearance_count=10,
        dialogue_count=20,
    )


# ========================================
# CharacterPose 模型测试
# ========================================


class TestCharacterPoseModel:
    """测试 CharacterPose 模型"""

    def test_character_pose_creation(self, character):
        """测试创建角色造型"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="家庭装",
            pose_type="home",
            is_default=True,
        )

        assert pose.character == character
        assert pose.pose_name == "家庭装"
        assert pose.pose_type == "home"
        assert pose.is_default is True
        assert pose.usage_count == 0
        assert pose.suitable_for_scenes == []
        assert str(pose) == f"{character.display_name} - 家庭装"

    def test_character_pose_all_types(self, character):
        """测试所有造型类型"""
        pose_types = ["casual", "formal", "battle", "school", "home", "custom"]

        created_poses = []
        for i, pose_type in enumerate(pose_types):
            pose = CharacterPose.objects.create(
                character=character,
                pose_name=f"造型{i}",
                pose_type=pose_type,
            )
            created_poses.append(pose)

        # 验证所有类型都创建成功
        assert CharacterPose.objects.filter(character=character).count() == 6

        # 验证每种类型
        for pose, expected_type in zip(created_poses, pose_types):
            assert pose.pose_type == expected_type

    def test_character_pose_suitable_scenes(self, character):
        """测试适用场景 JSON 字段"""
        scenes = ["家", "室内", "客厅"]
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="居家造型",
            pose_type="home",
            suitable_for_scenes=scenes,
        )

        assert pose.suitable_for_scenes == scenes
        assert "家" in pose.suitable_for_scenes
        assert "室内" in pose.suitable_for_scenes

    def test_character_pose_ai_extraction_fields(self, character):
        """测试 AI 提取信息字段"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="AI提取造型",
            pose_type="casual",
            extraction_source="AI_extracted",
            extracted_from_chapter=5,
            description="AI 自动提取的造型信息",
        )

        assert pose.extraction_source == "AI_extracted"
        assert pose.extracted_from_chapter == 5
        assert pose.description == "AI 自动提取的造型信息"

    def test_character_pose_increment_usage(self, character):
        """测试 increment_usage 方法"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="战斗装",
            pose_type="battle",
            usage_count=5,
        )

        assert pose.usage_count == 5

        # 调用 increment_usage 方法
        pose.increment_usage()

        # 重新加载对象
        pose.refresh_from_db()
        assert pose.usage_count == 6

    def test_character_pose_default_sorting(self, character):
        """测试默认排序"""
        # 创建多个造型
        CharacterPose.objects.create(
            character=character,
            pose_name="造型1",
            pose_type="casual",
            is_default=False,
            usage_count=5,
        )
        CharacterPose.objects.create(
            character=character,
            pose_name="造型2",
            pose_type="formal",
            is_default=True,
            usage_count=10,
        )
        CharacterPose.objects.create(
            character=character,
            pose_name="造型3",
            pose_type="battle",
            is_default=False,
            usage_count=15,
        )

        # 查询所有造型
        poses = list(CharacterPose.objects.filter(character=character))

        # 验证排序: is_default DESC, usage_count DESC, pose_name ASC
        assert poses[0].is_default is True  # 默认造型排在最前
        assert poses[1].usage_count == 15
        assert poses[2].usage_count == 5

    def test_character_pose_foreign_key_cascade(self, character):
        """测试级联删除"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="测试造型",
            pose_type="casual",
        )

        pose_id = pose.id

        # 删除角色
        character.delete()

        # 验证造型也被级联删除
        assert not CharacterPose.objects.filter(id=pose_id).exists()

    def test_character_pose_str_method(self, character):
        """测试 __str__ 方法"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="宴会装",
            pose_type="formal",
        )

        expected = f"{character.display_name} - 宴会装"
        assert str(pose) == expected

    def test_character_pose_unique_default_per_character(self, character):
        """测试每个角色可以有多个默认造型 (业务逻辑层约束)"""
        # 数据模型层允许多个 is_default=True
        # 但应用层应该确保只有一个默认造型
        pose1 = CharacterPose.objects.create(
            character=character,
            pose_name="默认造型1",
            pose_type="casual",
            is_default=True,
        )
        pose2 = CharacterPose.objects.create(
            character=character,
            pose_name="默认造型2",
            pose_type="formal",
            is_default=True,
        )

        # 模型层允许这样做
        assert pose1.is_default is True
        assert pose2.is_default is True

        # 查询默认造型
        default_poses = CharacterPose.objects.filter(character=character, is_default=True)
        assert default_poses.count() == 2

    def test_character_pose_empty_suitable_scenes(self, character):
        """测试空的适用场景列表"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="基础造型",
            pose_type="casual",
        )

        # 默认应该是空列表
        assert pose.suitable_for_scenes == []
        assert len(pose.suitable_for_scenes) == 0


# ========================================
# CharacterVoiceConfig 模型测试
# ========================================


class TestCharacterVoiceConfigModel:
    """测试 CharacterVoiceConfig 模型"""

    def test_character_voice_config_creation(self, character):
        """测试创建音色配置"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_id="zh-CN-XiaoxiaoNeural",
            pitch="normal",
            speed="normal",
            volume="normal",
        )

        assert voice_config.character == character
        assert voice_config.tts_engine == "edge"
        assert voice_config.voice_id == "zh-CN-XiaoxiaoNeural"
        assert voice_config.pitch == "normal"
        assert voice_config.speed == "normal"
        assert voice_config.volume == "normal"
        assert str(voice_config) == f"{character.display_name} - edge"

    def test_character_voice_config_all_engines(self, artwork):
        """测试所有 TTS 引擎类型"""
        engines = ["edge", "elevenlabs", "baidu", "azure"]

        for i, engine in enumerate(engines):
            # 为每个引擎创建不同的角色
            char = CharacterProfile.objects.create(
                artwork=artwork,
                name=f"test_char_{i}",
                display_name=f"测试角色{i}",
            )
            voice_config = CharacterVoiceConfig.objects.create(
                character=char,
                tts_engine=engine,
                voice_id=f"test_{engine}_voice",
            )
            assert voice_config.tts_engine == engine

    def test_character_voice_config_pitch_choices(self, artwork):
        """测试所有音调选项"""
        pitch_choices = ["very_low", "low", "normal", "high", "very_high"]

        for i, pitch in enumerate(pitch_choices):
            # 为每个音调创建不同的角色
            char = CharacterProfile.objects.create(
                artwork=artwork,
                name=f"test_char_pitch_{i}",
                display_name=f"测试角色音调{i}",
            )
            voice_config = CharacterVoiceConfig.objects.create(
                character=char,
                tts_engine="edge",
                pitch=pitch,
            )
            assert voice_config.pitch == pitch

    def test_character_voice_config_speed_choices(self, artwork):
        """测试所有语速选项"""
        speed_choices = ["very_slow", "slow", "normal", "fast", "very_fast"]

        for i, speed in enumerate(speed_choices):
            # 为每个语速创建不同的角色
            char = CharacterProfile.objects.create(
                artwork=artwork,
                name=f"test_char_speed_{i}",
                display_name=f"测试角色语速{i}",
            )
            voice_config = CharacterVoiceConfig.objects.create(
                character=char,
                tts_engine="edge",
                speed=speed,
            )
            assert voice_config.speed == speed

    def test_character_voice_config_volume_choices(self, artwork):
        """测试所有音量选项"""
        volume_choices = ["very_soft", "soft", "normal", "loud", "very_loud"]

        for i, volume in enumerate(volume_choices):
            # 为每个音量创建不同的角色
            char = CharacterProfile.objects.create(
                artwork=artwork,
                name=f"test_char_volume_{i}",
                display_name=f"测试角色音量{i}",
            )
            voice_config = CharacterVoiceConfig.objects.create(
                character=char,
                tts_engine="edge",
                volume=volume,
            )
            assert voice_config.volume == volume

    def test_character_voice_config_emotion_voices(self, character):
        """测试情感音色映射 JSON 字段"""
        emotion_mapping = {
            "happy": "zh-CN-XiaoxiaoNeural_happy",
            "sad": "zh-CN-XiaoxiaoNeural_sad",
            "angry": "zh-CN-XiaoxiaoNeural_angry",
            "excited": "zh-CN-XiaoxiaoNeural_excited",
        }

        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            emotion_voices=emotion_mapping,
        )

        assert voice_config.emotion_voices == emotion_mapping
        assert voice_config.emotion_voices["happy"] == "zh-CN-XiaoxiaoNeural_happy"
        assert voice_config.emotion_voices["sad"] == "zh-CN-XiaoxiaoNeural_sad"

    def test_character_voice_config_emotion_settings(self, character):
        """测试情感配置"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            emotion_mode="expressive",
            emotion_intensity="high",
        )

        assert voice_config.emotion_mode == "expressive"
        assert voice_config.emotion_intensity == "high"

    def test_character_voice_config_voice_sample_url(self, character):
        """测试试听样本 URL"""
        sample_url = "https://example.com/voice_sample.mp3"

        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_sample_url=sample_url,
        )

        assert voice_config.voice_sample_url == sample_url
        assert voice_config.voice_sample_url.startswith("https://")

    def test_character_voice_config_onetoone_relationship(self, character):
        """测试 OneToOne 关系"""
        # 创建音色配置
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        # 验证可以从角色访问音色配置
        assert character.voice_config == voice_config
        assert voice_config.character == character

    def test_character_voice_config_unique_constraint(self, character):
        """测试 OneToOne 唯一约束"""
        # 为同一个角色创建第一个音色配置
        CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        # 尝试为同一个角色创建第二个音色配置应该失败
        with pytest.raises(IntegrityError):
            CharacterVoiceConfig.objects.create(
                character=character,
                tts_engine="elevenlabs",
            )

    def test_character_voice_config_cascade_delete(self, character):
        """测试级联删除"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        voice_config_id = voice_config.id

        # 删除角色
        character.delete()

        # 验证音色配置也被级联删除
        assert not CharacterVoiceConfig.objects.filter(id=voice_config_id).exists()

    def test_character_voice_config_str_method(self, character):
        """测试 __str__ 方法"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_id="zh-CN-XiaoxiaoNeural",
        )

        expected = f"{character.display_name} - edge"
        assert str(voice_config) == expected

    def test_character_voice_config_empty_emotion_voices(self, character):
        """测试空的情感音色映射"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        # 默认应该是空字典
        assert voice_config.emotion_voices == {}
        assert len(voice_config.emotion_voices) == 0


# ========================================
# 集成测试: CharacterPose + CharacterVoiceConfig
# ========================================


class TestCharacterAssetsIntegration:
    """测试角色资产集成"""

    def test_character_with_full_assets(self, artwork):
        """测试角色拥有完整的资产配置"""
        # 创建角色
        character = CharacterProfile.objects.create(
            artwork=artwork,
            name="full_asset_char",
            display_name="完整资产角色",
            appearance_count=100,
            dialogue_count=200,
        )

        # 创建多套造型
        pose1 = CharacterPose.objects.create(
            character=character,
            pose_name="家庭装",
            pose_type="home",
            is_default=True,
            usage_count=30,
        )
        CharacterPose.objects.create(
            character=character,
            pose_name="战斗装",
            pose_type="battle",
            usage_count=20,
        )

        # 创建音色配置
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_id="zh-CN-XiaoxiaoNeural",
            pitch="normal",
            emotion_voices={
                "happy": "zh-CN-XiaoxiaoNeural_happy",
                "sad": "zh-CN-XiaoxiaoNeural_sad",
            },
        )

        # 验证关系
        assert character.poses.count() == 2
        assert character.voice_config == voice_config

        # 验证默认造型
        default_pose = character.poses.filter(is_default=True).first()
        assert default_pose == pose1

        # 验证造型排序
        poses = list(character.poses.all())
        assert poses[0].is_default is True  # 默认造型在前
        assert poses[1].is_default is False

    def test_multiple_characters_with_assets(self, artwork):
        """测试多个角色拥有各自的资产"""
        # 创建两个角色
        char1 = CharacterProfile.objects.create(
            artwork=artwork,
            name="char1",
            display_name="角色1",
        )
        char2 = CharacterProfile.objects.create(
            artwork=artwork,
            name="char2",
            display_name="角色2",
        )

        # 为角色1创建造型
        pose1 = CharacterPose.objects.create(
            character=char1,
            pose_name="角色1造型",
            pose_type="casual",
        )

        # 为角色2创建造型
        pose2 = CharacterPose.objects.create(
            character=char2,
            pose_name="角色2造型",
            pose_type="formal",
        )

        # 为角色1创建音色配置
        voice1 = CharacterVoiceConfig.objects.create(
            character=char1,
            tts_engine="edge",
        )

        # 为角色2创建音色配置
        voice2 = CharacterVoiceConfig.objects.create(
            character=char2,
            tts_engine="elevenlabs",
        )

        # 验证资产隔离
        assert char1.poses.count() == 1
        assert char2.poses.count() == 1
        assert pose1.character == char1
        assert pose2.character == char2
        assert voice1.character == char1
        assert voice2.character == char2

    def test_character_pose_usage_tracking(self, character):
        """测试造型使用追踪"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="战斗装",
            pose_type="battle",
            usage_count=0,
        )

        # 模拟多次使用
        for _ in range(5):
            pose.increment_usage()

        pose.refresh_from_db()
        assert pose.usage_count == 5

    def test_character_pose_with_scene_matching(self, character):
        """测试场景适配逻辑"""
        # 创建一个适用于家庭场景的造型
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="居家装",
            pose_type="home",
            suitable_for_scenes=["家", "室内", "客厅"],
        )

        # 验证场景匹配
        scene_keywords = ["家", "室内"]

        # 检查是否所有场景关键词都在适用场景列表中
        for keyword in scene_keywords:
            assert keyword in pose.suitable_for_scenes

        # 不匹配的场景
        assert "战场" not in pose.suitable_for_scenes


# ========================================
# Meta 配置测试
# ========================================


class TestCharacterAssetsMeta:
    """测试模型 Meta 配置"""

    def test_character_pose_db_table(self, character):
        """测试 CharacterPose 数据库表名"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="测试造型",
            pose_type="casual",
        )

        assert pose._meta.db_table == "character_poses"
        assert pose._meta.verbose_name == "角色造型"
        assert pose._meta.verbose_name_plural == "角色造型"

    def test_character_voice_config_db_table(self, character):
        """测试 CharacterVoiceConfig 数据库表名"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        assert voice_config._meta.db_table == "character_voice_configs"
        assert voice_config._meta.verbose_name == "角色音色配置"
        assert voice_config._meta.verbose_name_plural == "角色音色配置"

    def test_character_pose_ordering(self, character):
        """测试 CharacterPose 排序配置"""
        # 创建多个造型
        CharacterPose.objects.create(
            character=character,
            pose_name="C造型",
            pose_type="casual",
            is_default=False,
            usage_count=5,
        )
        CharacterPose.objects.create(
            character=character,
            pose_name="A造型",
            pose_type="home",
            is_default=True,
            usage_count=10,
        )
        CharacterPose.objects.create(
            character=character,
            pose_name="B造型",
            pose_type="formal",
            is_default=False,
            usage_count=15,
        )

        # 查询所有造型
        poses = list(CharacterPose.objects.filter(character=character))

        # 验证排序: is_default DESC, usage_count DESC, pose_name ASC
        assert poses[0].pose_name == "A造型"  # is_default=True
        assert poses[1].pose_name == "B造型"  # usage_count=15
        assert poses[2].pose_name == "C造型"  # usage_count=5

    def test_character_timestamped_model(self, character):
        """测试 TimeStampedModel 继承"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="测试造型",
            pose_type="casual",
        )
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        # 验证时间戳字段存在
        assert pose.created_at is not None
        assert pose.updated_at is not None
        assert voice_config.created_at is not None
        assert voice_config.updated_at is not None


# ========================================
# 边界条件测试
# ========================================


class TestCharacterAssetsEdgeCases:
    """测试边界条件和异常情况"""

    def test_character_pose_max_length_fields(self, character):
        """测试最大长度字段"""
        # pose_name max_length=200
        long_name = "A" * 200
        pose = CharacterPose.objects.create(
            character=character,
            pose_name=long_name,
            pose_type="casual",
        )

        assert pose.pose_name == long_name
        assert len(pose.pose_name) == 200

    def test_character_voice_config_max_length_fields(self, character):
        """测试最大长度字段"""
        # voice_id max_length=100
        long_voice_id = "x" * 100
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
            voice_id=long_voice_id,
        )

        assert voice_config.voice_id == long_voice_id
        assert len(voice_config.voice_id) == 100

    def test_character_pose_blank_optional_fields(self, character):
        """测试可选字段为空"""
        pose = CharacterPose.objects.create(
            character=character,
            pose_name="最小配置造型",
            pose_type="casual",
        )

        # 可选字段应该可以为空
        assert pose.extraction_source == ""
        assert pose.extracted_from_chapter is None
        assert pose.description == ""

    def test_character_voice_config_blank_optional_fields(self, character):
        """测试可选字段为空"""
        voice_config = CharacterVoiceConfig.objects.create(
            character=character,
            tts_engine="edge",
        )

        # 可选字段应该可以为空
        assert voice_config.voice_id == ""
        assert voice_config.voice_type == ""
        assert voice_config.emotion_mode == ""
        assert voice_config.voice_sample_url == ""
        assert voice_config.emotion_voices == {}
