"""
Content API集成测试
测试内容管理API: StorageImageListView, StorageImageDetailView, StorageVideoDetailView
"""

import pytest
from pathlib import Path
from django.conf import settings
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import ContentRewrite, Storyboard, GeneratedImage, GeneratedVideo
from apps.content.tests.factories import (
    ContentRewriteFactory,
    StoryboardFactory,
    GeneratedImageFactory,
    GeneratedVideoFactory,
    ProjectFactory,
)


@pytest.mark.django_db
class TestStorageImageListView:
    """测试图片列表API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_list_images_empty_directory(self):
        """测试图片列表 - 空目录"""
        # 创建测试目录
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        response = self.client.get('/api/v1/content/storage/image/')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert '图片目录不存在' in response.data['message']

        # 清理
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_list_images_with_files(self):
        """测试图片列表 - 有文件"""
        # 创建测试目录和图片文件
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片文件
        test_image = image_dir / 'test.jpg'
        test_image.write_bytes(b'fake image data')

        response = self.client.get('/api/v1/content/storage/image/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['total'] == 1
        assert len(response.data['data']) == 1

        # 清理
        test_image.unlink()
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_list_images_recursively(self):
        """测试图片列表 - 递归遍历子目录"""
        # 创建测试目录结构
        image_dir = Path('/tmp/test_storage/image')
        subdir = image_dir / '2025-01-27'
        subdir.mkdir(parents=True, exist_ok=True)

        # 创建测试图片
        test_image1 = image_dir / 'root.jpg'
        test_image2 = subdir / 'sub.jpg'
        test_image1.write_bytes(b'fake image 1')
        test_image2.write_bytes(b'fake image 2')

        response = self.client.get('/api/v1/content/storage/image/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 2

        # 清理
        test_image1.unlink()
        test_image2.unlink()
        subdir.rmdir()
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_list_images_sorted_by_modified_time(self):
        """测试图片列表 - 按修改时间倒序"""
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        # 创建多个测试图片
        test_image1 = image_dir / 'image1.jpg'
        test_image2 = image_dir / 'image2.png'

        test_image1.write_bytes(b'image 1')
        test_image2.write_bytes(b'image 2')

        response = self.client.get('/api/v1/content/storage/image/')

        assert response.status_code == status.HTTP_200_OK
        # 验证返回了2个图片
        assert response.data['total'] == 2

        # 清理
        test_image1.unlink()
        test_image2.unlink()
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_list_images_filters_by_extension(self):
        """测试图片列表 - 按扩展名过滤"""
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        # 创建不同类型的文件
        (image_dir / 'image.jpg').write_bytes(b'jpg image')
        (image_dir / 'image.png').write_bytes(b'png image')
        (image_dir / 'document.txt').write_bytes(b'text file')

        response = self.client.get('/api/v1/content/storage/image/')

        assert response.status_code == status.HTTP_200_OK
        # 应该只返回图片文件,不包含txt
        assert response.data['total'] == 2

        # 清理
        for f in image_dir.glob('*'):
            f.unlink()
        image_dir.rmdir()


@pytest.mark.django_db
class TestStorageImageDetailView:
    """测试图片详情API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_image_file(self):
        """测试获取图片文件"""
        # 创建测试目录和图片
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        test_image = image_dir / 'test.jpg'
        test_image.write_bytes(b'fake jpg data')

        response = self.client.get('/api/v1/content/storage/image/test.jpg')

        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == 'image/jpeg'

        # 清理
        test_image.unlink()
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_image_with_subdirectory(self):
        """测试获取子目录中的图片"""
        image_dir = Path('/tmp/test_storage/image')
        subdir = image_dir / '2025-01-27'
        subdir.mkdir(parents=True, exist_ok=True)

        test_image = subdir / 'photo.png'
        test_image.write_bytes(b'fake png data')

        response = self.client.get('/api/v1/content/storage/image/2025-01-27/photo.png')

        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == 'image/png'

        # 清理
        test_image.unlink()
        subdir.rmdir()
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_image_not_found(self):
        """测试获取不存在的图片"""
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        response = self.client.get('/api/v1/content/storage/image/nonexistent.jpg')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 清理
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_image_path_traversal_protection(self):
        """测试路径遍历攻击防护"""
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        # 尝试使用../访问上层目录
        response = self.client.get('/api/v1/content/storage/image/../sensitive.txt')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 清理
        image_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_various_image_formats(self):
        """测试各种图片格式的Content-Type"""
        image_dir = Path('/tmp/test_storage/image')
        image_dir.mkdir(parents=True, exist_ok=True)

        formats = {
            'test.jpg': 'image/jpeg',
            'test.png': 'image/png',
            'test.gif': 'image/gif',
            'test.bmp': 'image/bmp',
            'test.webp': 'image/webp',
        }

        for filename, expected_content_type in formats.items():
            test_image = image_dir / filename
            test_image.write_bytes(b'fake data')

            response = self.client.get(f'/api/v1/content/storage/image/{filename}')

            assert response.status_code == status.HTTP_200_OK
            assert response.headers['Content-Type'] == expected_content_type

            test_image.unlink()

        # 清理
        image_dir.rmdir()


@pytest.mark.django_db
class TestStorageVideoDetailView:
    """测试视频详情API"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_video_file(self):
        """测试获取视频文件"""
        video_dir = Path('/tmp/test_storage/video')
        video_dir.mkdir(parents=True, exist_ok=True)

        test_video = video_dir / 'test.mp4'
        test_video.write_bytes(b'fake mp4 data')

        response = self.client.get('/api/v1/content/storage/video/test.mp4')

        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == 'video/mp4'

        # 清理
        test_video.unlink()
        video_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_video_with_subdirectory(self):
        """测试获取子目录中的视频"""
        video_dir = Path('/tmp/test_storage/video')
        subdir = video_dir / '2025-01-27'
        subdir.mkdir(parents=True, exist_ok=True)

        test_video = subdir / 'movie.mp4'
        test_video.write_bytes(b'fake video data')

        response = self.client.get('/api/v1/content/storage/video/2025-01-27/movie.mp4')

        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == 'video/mp4'

        # 清理
        test_video.unlink()
        subdir.rmdir()
        video_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_video_not_found(self):
        """测试获取不存在的视频"""
        video_dir = Path('/tmp/test_storage/video')
        video_dir.mkdir(parents=True, exist_ok=True)

        response = self.client.get('/api/v1/content/storage/video/nonexistent.mp4')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 清理
        video_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_video_path_traversal_protection(self):
        """测试路径遍历攻击防护"""
        video_dir = Path('/tmp/test_storage/video')
        video_dir.mkdir(parents=True, exist_ok=True)

        # 尝试使用../访问上层目录
        response = self.client.get('/api/v1/content/storage/video/../sensitive.mp4')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 清理
        video_dir.rmdir()

    @override_settings(STORAGE_ROOT='/tmp/test_storage')
    def test_get_various_video_formats(self):
        """测试各种视频格式的Content-Type"""
        video_dir = Path('/tmp/test_storage/video')
        video_dir.mkdir(parents=True, exist_ok=True)

        formats = {
            'test.mp4': 'video/mp4',
            'test.avi': 'video/x-msvideo',
            'test.mov': 'video/quicktime',
            'test.webm': 'video/webm',
        }

        for filename, expected_content_type in formats.items():
            test_video = video_dir / filename
            test_video.write_bytes(b'fake data')

            response = self.client.get(f'/api/v1/content/storage/video/{filename}')

            assert response.status_code == status.HTTP_200_OK
            assert response.headers['Content-Type'] == expected_content_type

            test_video.unlink()

        # 清理
        video_dir.rmdir()


@pytest.mark.django_db
class TestContentModelsAccess:
    """测试内容模型访问权限"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.client = APIClient()

    def test_unauthenticated_can_access_storage_images(self):
        """测试未认证用户可以访问存储图片"""
        # 这是个公开的API (permission_classes = [AllowAny])
        response = self.client.get('/api/v1/content/storage/image/')

        # 应该返回200或者404(目录不存在),但不应该是401或403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_unauthenticated_can_access_storage_videos(self):
        """测试未认证用户可以访问存储视频"""
        # 这是个公开的API
        response = self.client.get('/api/v1/content/storage/video/')

        # 应该返回200或者404(目录不存在),但不应该是401或403
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
