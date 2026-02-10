"""
Story 11.2.4: 单分镜重新生成 API 测试

测试 POST /api/v1/artworks/shots/{id}/regenerate/ 端点
"""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.artworks.models import (
    Artwork,
    Chapter,
    CharacterPose,
    CharacterProfile,
    ScriptScene,
    Shot,
)
from apps.users.models import User


class ShotRegenerateAPITestCase(APITestCase):
    """镜头重新生成 API 测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        self.client.force_authenticate(user=self.user)

        # 创建作品
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="manga",
            story_overview="测试故事概要",
            total_chapters=10,
        )

        # 创建角色
        self.character = CharacterProfile.objects.create(
            artwork=self.artwork,
            name="测试角色",
            display_name="测试角色",
            description="测试角色描述",
            importance_rank=1,
        )

        # 创建角色造型
        self.pose = CharacterPose.objects.create(
            character=self.character,
            pose_name="默认造型",
            pose_type="full_body",
            is_default=True,
        )

        # 创建章节
        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="测试章节",
            original_text="测试章节内容",
        )

        # 创建场景
        self.scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="测试场景",
            description="测试场景描述",
        )

        # 创建镜头
        self.shot = Shot.objects.create(
            scene=self.scene,
            shot_number=1,
            shot_type="standard",
            content="测试镜头内容",
            narration="测试旁白",
            duration=3.0,
            character_pose=self.pose,
            is_generated=True,
            generation_retry_count=0,
        )

        # API URL
        self.regenerate_url = f"/api/v1/artworks/shots/{self.shot.id}/regenerate/"

    def test_regenerate_shot_success(self):
        """测试成功重新生成镜头"""
        # 准备请求数据
        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
            "override_params": {
                "image_prompt": "测试自定义提示词",
            },
        }

        # 发送请求
        response = self.client.post(self.regenerate_url, data, format="json")

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertIn("shot_id", response.data)
        self.assertEqual(response.data["shot_id"], self.shot.id)
        self.assertEqual(response.data["regenerate_type"], "image")
        self.assertEqual(response.data["status"], "processing")

    def test_regenerate_both_image_and_audio(self):
        """测试同时重新生成图像和音频"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": True,
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["regenerate_type"], "both")

    def test_regenerate_audio_only(self):
        """测试仅重新生成音频"""
        data = {
            "regenerate_image": False,
            "regenerate_audio": True,
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["regenerate_type"], "audio")

    def test_regenerate_default_values(self):
        """测试使用默认值（同时生成图像和音频）"""
        # 不提供任何参数
        response = self.client.post(self.regenerate_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["regenerate_type"], "both")

    def test_regenerate_validation_error_both_false(self):
        """测试验证错误：两个选项都为 False"""
        data = {
            "regenerate_image": False,
            "regenerate_audio": False,
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("regenerate", response.data)

    def test_regenerate_with_custom_prompt(self):
        """测试使用自定义提示词"""
        custom_prompt = "电影级光效、柔焦背景、暖色调"

        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
            "override_params": {
                "image_prompt": custom_prompt,
            },
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_regenerate_with_pose_override(self):
        """测试覆盖角色造型"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
            "override_params": {
                "character_pose_id": self.pose.id,
            },
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_regenerate_with_duration_override(self):
        """测试覆盖时长"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": True,
            "override_params": {
                "duration": 5.0,
            },
        }

        response = self.client.post(self.regenerate_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_regenerate_nonexistent_shot(self):
        """测试重新生成不存在的镜头"""
        url = "/api/v1/artworks/shots/99999/regenerate/"

        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regenerate_unauthorized(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)

        response = self.client.post(self.regenerate_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegenerateShotSerializerTestCase(APITestCase):
    """RegenerateShotSerializer 测试"""

    def setUp(self):
        """设置测试数据"""
        from apps.artworks.serializers import RegenerateShotSerializer

        self.serializer = RegenerateShotSerializer

    def test_valid_data_both_true(self):
        """测试有效数据：两个选项都为 True"""
        data = {"regenerate_image": True, "regenerate_audio": True, "override_params": {}}

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["regenerate_image"], True)
        self.assertEqual(serializer.validated_data["regenerate_audio"], True)

    def test_valid_data_image_only(self):
        """测试有效数据：仅生成图像"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
        }

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_valid_data_audio_only(self):
        """测试有效数据：仅生成音频"""
        data = {
            "regenerate_image": False,
            "regenerate_audio": True,
        }

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_default_values(self):
        """测试默认值"""
        data = {}

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["regenerate_image"], True)
        self.assertEqual(serializer.validated_data["regenerate_audio"], True)
        self.assertEqual(serializer.validated_data["override_params"], {})

    def test_validation_error_both_false(self):
        """测试验证错误：两个选项都为 False"""
        data = {
            "regenerate_image": False,
            "regenerate_audio": False,
        }

        serializer = self.serializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("regenerate", serializer.errors)

    def test_valid_override_params(self):
        """测试有效的覆盖参数"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
            "override_params": {
                "image_prompt": "测试提示词",
                "character_pose_id": 1,
                "duration": 5.0,
            },
        }

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_default_override_params(self):
        """测试默认覆盖参数"""
        data = {
            "regenerate_image": True,
            "regenerate_audio": False,
        }

        serializer = self.serializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["override_params"], {})
