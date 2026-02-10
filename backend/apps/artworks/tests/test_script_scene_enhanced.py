"""
ScriptScene 模型增强单元测试 (Story 11.2.1)

测试覆盖:
1. 首尾帧字段
2. 转场配置字段和验证
3. 序列化器验证
"""

import pytest

from apps.artworks.models import (
    Artwork,
    Chapter,
    PhysicalScene,
    ScriptScene,
)
from apps.artworks.serializers import ScriptSceneSerializer


@pytest.mark.django_db
class TestScriptSceneFields:
    """测试 ScriptScene 新字段"""

    def setup_method(self):
        """创建测试数据"""
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="novel",
        )

        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="第一章",
            original_text="测试章节内容",
        )

        self.physical_scene = PhysicalScene.objects.create(
            category="indoor",
            name="实验室",
            default_lighting="明亮",
            default_atmosphere="现代",
        )

    def test_script_scene_has_transition_fields(self):
        """测试转场字段存在"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=1,
            scene_name="场景1",
            description="测试场景",
            transition_type="fade",
            transition_duration=2.5,
        )

        assert scene.transition_type == "fade"
        assert scene.transition_duration == 2.5

    def test_script_scene_transition_to_next_nullable(self):
        """测试 transition_to_next 可为空"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=1,
            scene_name="场景1",
            description="测试场景",
            transition_type="fade",
        )

        # transition_to_next 可以为空
        assert scene.transition_to_next is None

    def test_script_scene_transition_duration_default(self):
        """测试 transition_duration 默认值为 1.5"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=1,
            scene_name="场景1",
            description="测试场景",
        )

        assert scene.transition_duration == 1.5

    def test_script_scene_head_tail_frame_nullable(self):
        """测试首尾帧字段可为空"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=1,
            scene_name="场景1",
            description="测试场景",
        )

        assert scene.head_frame == ""
        assert scene.tail_frame == ""


@pytest.mark.django_db
class TestScriptSceneSerializerValidation:
    """测试 ScriptScene 序列化器验证逻辑"""

    def setup_method(self):
        """创建测试数据"""
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="novel",
        )

        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="第一章",
            original_text="测试章节内容",
        )

        self.physical_scene = PhysicalScene.objects.create(
            category="indoor",
            name="实验室",
            default_lighting="明亮",
            default_atmosphere="现代",
        )

        self.scene1 = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=1,
            scene_name="场景1",
            description="测试场景1",
        )

        self.scene2 = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=2,
            scene_name="场景2",
            description="测试场景2",
        )

    def test_serializer_valid_data(self):
        """测试序列化器验证有效数据"""
        data = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 3,
            "scene_name": "场景3",
            "description": "测试场景3",
            "transition_type": "",  # 空字符串表示不设置转场
            "transition_duration": 2.0,
        }

        serializer = ScriptSceneSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_transition_type_without_target(self):
        """测试设置转场类型但没有设置目标场景"""
        data = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 3,
            "scene_name": "场景3",
            "description": "测试场景3",
            "transition_type": "fade",
            "transition_to_next": None,  # 没有设置目标
            "transition_duration": 2.0,
        }

        serializer = ScriptSceneSerializer(data=data)
        assert not serializer.is_valid()
        assert "transition_to_next" in serializer.errors

    def test_serializer_transition_type_with_target(self):
        """测试设置转场类型和目标场景"""
        data = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 1,  # 更新现有场景1
            "scene_name": "场景1-更新",
            "description": "测试场景1-更新",
            "transition_type": "fade",
            "transition_to_next": self.scene2.id,  # 设置了目标
            "transition_duration": 2.0,
        }

        serializer = ScriptSceneSerializer(self.scene1, data=data)
        assert serializer.is_valid(), serializer.errors

    def test_serializer_transition_duration_out_of_range(self):
        """测试转场时长超出范围"""
        data = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 3,
            "scene_name": "场景3",
            "description": "测试场景3",
            "transition_duration": 15.0,  # 超过10秒
        }

        serializer = ScriptSceneSerializer(data=data)
        assert not serializer.is_valid()
        assert "transition_duration" in serializer.errors

    def test_serializer_negative_transition_duration(self):
        """测试负数的转场时长"""
        data = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 3,
            "scene_name": "场景3",
            "description": "测试场景3",
            "transition_duration": -1.0,
        }

        serializer = ScriptSceneSerializer(data=data)
        assert not serializer.is_valid()
        assert "transition_duration" in serializer.errors

    def test_serializer_valid_transition_duration(self):
        """测试有效的转场时长边界值"""
        # 测试 0 秒
        data1 = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 3,
            "scene_name": "场景3",
            "description": "测试场景3",
            "transition_duration": 0,
        }
        serializer1 = ScriptSceneSerializer(data=data1)
        assert serializer1.is_valid(), serializer1.errors

        # 测试 10 秒
        data2 = {
            "chapter": self.chapter.id,
            "physical_scene": self.physical_scene.id,
            "scene_number": 4,
            "scene_name": "场景4",
            "description": "测试场景4",
            "transition_duration": 10,
        }
        serializer2 = ScriptSceneSerializer(data=data2)
        assert serializer2.is_valid(), serializer2.errors

    def test_serializer_read_only_fields(self):
        """测试只读字段"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=3,  # 使用不同的序号避免冲突
            scene_name="场景3",
            description="测试场景",
        )

        serializer = ScriptSceneSerializer(scene)
        data = serializer.data

        # 检查只读字段存在
        assert "chapter_title" in data
        assert "physical_scene_name" in data
        assert "transition_type_display" in data
        assert "shot_count" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_serializer_nested_fields(self):
        """测试嵌套字段"""
        scene = ScriptScene.objects.create(
            chapter=self.chapter,
            physical_scene=self.physical_scene,
            scene_number=4,  # 使用不同的序号避免冲突
            scene_name="场景4",
            description="测试场景",
        )

        serializer = ScriptSceneSerializer(scene)
        data = serializer.data

        # 检查嵌套字段
        assert data["chapter_title"] == "第一章"
        assert data["physical_scene_name"] == "实验室"
