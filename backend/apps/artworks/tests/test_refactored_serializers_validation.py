"""
新增序列化器验证测试 (Story 12-4 序列化器重构)

测试覆盖新增的序列化器模块中的验证方法和字段

运行方法：python -m pytest apps.artworks.tests.test_refactored_serializers_validation
"""

import pytest
from rest_framework import serializers
from apps.artworks.serializers.batch import (
    GenerationProgressSerializer,
    GenerationHistorySerializer
)
from apps.artworks.serializers.scene import (
    ScriptSceneSerializer,
    ShotSerializer
)
from apps.artworks.serializers.character import (
    RegenerateShotSerializer
)


class TestRefactoredSerializersValidationSuite:
    """新增序列化器验证测试套件"""

    @pytest.mark.unit
    def test_generation_progress_serializer_fields(self):
        """测试 GenerationProgressSerializer 包含所有必需字段"""
        self.assertIn('generation_type', GenerationProgressSerializer.Meta.fields)
        self.assertIn('status', GenerationProgressSerializer.Meta.fields)
        self.assertIn('progress_percentage', GenerationProgressSerializer.Meta.fields)
        self.assertIn('total_items', GenerationProgressSerializer.Meta.fields)
        self.assertIn('completed_items', GenerationProgressSerializer.Meta.fields)

    @pytest.mark.unit
    def test_generation_history_serializer_fields(self):
        """测试 GenerationHistorySerializer 包含所有必需字段"""
        self.assertIn('generation_type', GenerationHistorySerializer.Meta.fields)
        self.assertIn('quality_rating', GenerationHistorySerializer.Meta.fields)
        self.assertIn('prompt_params', GenerationHistorySerializer.Meta.fields)
        self.assertIn('voice_params', GenerationHistorySerializer.Meta.fields)

    @pytest.mark.unit
    def test_script_scene_serializer_enhanced_fields(self):
        """测试 ScriptSceneSerializer 增强字段"""
        self.assertIn('transition_type_display', ScriptSceneSerializer.Meta.fields)
        self.assertIn('physical_scene_name', ScriptSceneSerializer.Meta.fields)
        self.assertIn('head_frame_url', ScriptSceneSerializer.Meta.fields)
        self.assertIn('tail_frame_url', ScriptSceneSerializer.Meta.fields)

    @pytest.mark.unit
    def test_shot_serializer_camera_validation(self):
        """测试 ShotSerializer 运镜参数验证"""
        serializer = ShotSerializer(data={
            'scene': 1,
            'shot_number': 1,
            'camera_movement_params': 'invalid_json_string'
        })
        self.assertFalse(serializer.is_valid())

    @pytest.mark.unit
    def test_shot_serializer_negative_retry_count(self):
        """测试 ShotSerializer 负数重试次数验证"""
        serializer = ShotSerializer(data={
            'scene': 1,
            'shot_number': 1,
            'generation_retry_count': -1
        })
        self.assertFalse(serializer.is_valid())

    @pytest.mark.unit
    def test_regenerate_shot_serializer_validation(self):
        """测试 RegenerateShotSerializer 参数验证"""
        serializer = RegenerateShotSerializer(data={
            'regenerate_image': False,
            'regenerate_audio': False
        })
        self.assertFalse(serializer.is_valid())
