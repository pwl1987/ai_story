"""
首尾帧提取 API 层测试 (Story 12-5)

测试覆盖:
1. 正常流程测试（成功提取、保存到场景）
2. 错误处理测试（空场景、无效ID）
3. 权限控制测试（认证、授权）

运行方法：python -m pytest apps/artworks/tests/test_frame_extraction_api.py -v
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.artworks.models import ScriptScene, Shot, Chapter, Artwork
from rest_framework import status
from rest_framework.test import APITestCase


class TestFrameExtractionAPI(APITestCase):
    """测试首尾帧提取 API"""

    def setUp(self):
        """测试数据初始化"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", password="test123", email="test@example.com"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="test123", email="other@example.com"
        )

        # 创建测试数据
        self.artwork = Artwork.objects.create(
            title="测试作品",
            author="测试作者",
            artwork_type="novel",
        )

        self.chapter = Chapter.objects.create(
            artwork=self.artwork,
            chapter_number=1,
            title="测试章节",
            original_text="测试内容",
        )

        self.scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=1,
            scene_name="测试场景",
        )

        # 创建带图片的镜头
        self._create_test_shot(self.scene)

        # API客户端
        self.client.force_authenticate(user=self.user)

    def _create_test_shot(self, scene):
        """创建测试用镜头（带图片）"""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        upload = SimpleUploadedFile(
            name="test_shot.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )

        return Shot.objects.create(
            scene=scene,
            shot_number=1,
            sort_order=1,
            generated_image=upload
        )

    # ========== 正常流程测试 ==========

    def test_extract_frames_returns_success(self):
        """测试正常提取返回成功"""
        response = self.client.post(f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    def test_extract_frames_saves_to_scene(self):
        """测试提取后保存到场景"""
        self.client.post(f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/")

        self.scene.refresh_from_db()

        self.assertIsNotNone(self.scene.head_frame)
        self.assertIsNotNone(self.scene.tail_frame)

    def test_extract_frames_returns_urls(self):
        """测试返回首尾帧URL"""
        response = self.client.post(f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/")

        self.assertIn("head_frame_url", response.data)
        self.assertIn("tail_frame_url", response.data)
        self.assertIn("message", response.data)

    # ========== 错误处理测试 ==========

    def test_extract_frames_fails_with_no_shots(self):
        """测试无镜头场景返回400错误"""
        empty_scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=2,
            scene_name="空场景",
        )

        response = self.client.post(
            f"/api/v1/artworks/script-scenes/{empty_scene.id}/extract-frames/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("没有可提取的镜头", response.data["error"])

    def test_extract_frames_returns_404_for_invalid_scene(self):
        """测试无效场景ID返回404"""
        response = self.client.post("/api/v1/artworks/script-scenes/99999/extract-frames/")

        self.assertEqual(response.status_code, 404)

    def test_extract_frames_with_corrupted_image(self):
        """测试损坏图片的处理"""
        # 创建没有图片的镜头
        corrupted_scene = ScriptScene.objects.create(
            chapter=self.chapter,
            scene_number=3,
            scene_name="损坏场景",
        )

        Shot.objects.create(
            scene=corrupted_scene,
            shot_number=1,
            sort_order=1,
            generated_image=None
        )

        response = self.client.post(
            f"/api/v1/artworks/script-scenes/{corrupted_scene.id}/extract-frames/"
        )

        # 应该返回成功但首尾帧为None
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    # ========== 权限控制测试 ==========

    def test_unauthenticated_user_cannot_extract_frames(self):
        """测试未认证用户无法提取"""
        self.client.force_authenticate(user=None)

        response = self.client.post(
            f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/"
        )

        self.assertEqual(response.status_code, 401)

    def test_unauthorized_user_cannot_extract_frames(self):
        """测试未授权用户无法提取"""
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            f"/api/v1/artworks/script-scenes/{self.scene.id}/extract-frames/"
        )

        self.assertEqual(response.status_code, 403)

    # ========== 辅助方法 ==========

    def _create_test_image(self, color="red", size=(100, 100)):
        """创建测试图片"""
        img = Image.new("RGB", size, color=color)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        return SimpleUploadedFile(
            name="test.jpg",
            content=buffer.read(),
            content_type="image/jpeg",
        )
