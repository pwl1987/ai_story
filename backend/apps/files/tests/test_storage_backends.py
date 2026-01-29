"""
文件存储服务单元测试
Epic 6.2: 文件存储服务实现

测试内容：
1. 本地存储后端测试
2. S3存储后端测试（Mock）
3. OSS存储后端测试（Mock）
4. 工厂模式测试
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.files.storage_backends import (
    LocalStorageBackend,
    OSSStorageBackend,
    S3StorageBackend,
    StorageBackendFactory,
    get_storage_backend,
)


class LocalStorageBackendTestCase(TestCase):
    """本地存储后端测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {"root": self.temp_dir, "base_url": "storage/"}
        self.backend = LocalStorageBackend(self.config)

    def tearDown(self):
        """清理测试环境"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_file(self):
        """测试保存文件"""
        # 创建测试文件
        file_content = b"Test content"
        uploaded_file = SimpleUploadedFile("test.txt", file_content)

        # 保存文件
        file_path = self.backend.save(uploaded_file, "test/test.txt")

        # 验证文件已保存
        self.assertTrue(self.backend.exists(file_path))

        # 验证文件内容
        absolute_path = self.backend.get_absolute_path(file_path)
        with open(absolute_path, "rb") as f:
            saved_content = f.read()
        self.assertEqual(saved_content, file_content)

    def test_delete_file(self):
        """测试删除文件"""
        # 创建并保存文件
        uploaded_file = SimpleUploadedFile("test.txt", b"Test content")
        file_path = self.backend.save(uploaded_file, "test/test.txt")

        # 删除文件
        self.backend.delete(file_path)

        # 验证文件已删除
        self.assertFalse(self.backend.exists(file_path))

    def test_file_exists(self):
        """测试检查文件是否存在"""
        uploaded_file = SimpleUploadedFile("test.txt", b"Test content")
        file_path = self.backend.save(uploaded_file, "test/test.txt")

        # 文件应该存在
        self.assertTrue(self.backend.exists(file_path))

        # 不存在的文件
        self.assertFalse(self.backend.exists("nonexistent.txt"))

    def test_get_url(self):
        """测试获取文件URL"""
        url = self.backend.url("test/test.txt")
        self.assertIn("storage/", url)
        self.assertIn("test/test.txt", url)

    def test_get_absolute_path(self):
        """测试获取绝对路径"""
        uploaded_file = SimpleUploadedFile("test.txt", b"Test content")
        file_path = self.backend.save(uploaded_file, "test/test.txt")

        absolute_path = self.backend.get_absolute_path(file_path)
        self.assertTrue(os.path.isabs(absolute_path))
        self.assertTrue(absolute_path.endswith("test/test.txt"))


class S3StorageBackendTestCase(TestCase):
    """S3存储后端测试（使用Mock）"""

    @patch.dict(
        os.environ,
        {
            "AWS_S3_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "AWS_S3_REGION": "us-east-1",
        },
    )
    def setUp(self):
        """设置测试环境"""
        self.config = {
            "bucket_name": "test-bucket",
            "access_key": "test-key",
            "secret_key": "test-secret",
            "region": "us-east-1",
        }

    @patch("apps.files.storage_backends.S3Boto3Storage")
    def test_init_s3_backend(self, mock_storage_class):
        """测试初始化S3存储后端"""
        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage

        backend = S3StorageBackend(self.config)

        # 验证S3Boto3Storage被正确初始化
        self.assertTrue(mock_storage_class.called)
        self.assertEqual(backend.storage, mock_storage)

    @patch("apps.files.storage_backends.S3Boto3Storage")
    def test_save_file(self, mock_storage_class):
        """测试保存文件到S3"""
        mock_storage = Mock()
        mock_storage.save.return_value = "https://test-bucket.s3.amazonaws.com/test.txt"
        mock_storage_class.return_value = mock_storage

        backend = S3StorageBackend(self.config)

        # 保存文件
        uploaded_file = SimpleUploadedFile("test.txt", b"Test content")
        file_url = backend.save(uploaded_file, "test/test.txt")

        # 验证save被调用
        self.assertTrue(mock_storage.save.called)
        self.assertEqual(file_url, "https://test-bucket.s3.amazonaws.com/test.txt")

    @patch("apps.files.storage_backends.S3Boto3Storage")
    def test_delete_file(self, mock_storage_class):
        """测试从S3删除文件"""
        mock_storage = Mock()
        mock_storage.exists.return_value = True
        mock_storage_class.return_value = mock_storage

        backend = S3StorageBackend(self.config)

        # 删除文件
        backend.delete("test/test.txt")

        # 验证delete被调用
        self.assertTrue(mock_storage.delete.called)

    @patch("apps.files.storage_backends.S3Boto3Storage")
    def test_get_url(self, mock_storage_class):
        """测试获取S3文件URL"""
        mock_storage = Mock()
        mock_storage.url.return_value = "https://test-bucket.s3.amazonaws.com/test.txt"
        mock_storage_class.return_value = mock_storage

        backend = S3StorageBackend(self.config)
        url = backend.url("test/test.txt")

        # 验证URL
        self.assertEqual(url, "https://test-bucket.s3.amazonaws.com/test.txt")


class OSSStorageBackendTestCase(TestCase):
    """阿里云OSS存储后端测试（使用Mock）"""

    def setUp(self):
        """设置测试环境"""
        import importlib.util

        if not importlib.util.find_spec("oss2"):
            # oss2未安装，跳过所有测试
            self.skipTest("oss2库未安装")

        self.config = {
            "bucket_name": "test-bucket",
            "access_key": "test-key",
            "secret_key": "test-secret",
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
        }

    @patch("apps.files.storage_backends.oss2")
    def test_init_oss_backend(self, mock_oss2):
        """测试初始化OSS存储后端"""
        mock_auth = Mock()
        mock_bucket = Mock()
        mock_oss2.Auth.return_value = mock_auth
        mock_oss2.Bucket.return_value = mock_bucket

        backend = OSSStorageBackend(self.config)

        # 验证oss2.Auth和oss2.Bucket被调用
        self.assertTrue(mock_oss2.Auth.called)
        self.assertTrue(mock_oss2.Bucket.called)
        self.assertEqual(backend.bucket, mock_bucket)

    @patch("apps.files.storage_backends.oss2")
    def test_save_file(self, mock_oss2):
        """测试保存文件到OSS"""
        mock_bucket = Mock()
        mock_oss2.Auth.return_value = Mock()
        mock_oss2.Bucket.return_value = mock_bucket

        backend = OSSStorageBackend(self.config)

        # 保存文件
        uploaded_file = SimpleUploadedFile("test.txt", b"Test content")
        url = backend.save(uploaded_file, "test/test.txt")

        # 验证put_object被调用
        self.assertTrue(mock_bucket.put_object.called)
        self.assertIn("test-bucket.oss-cn-hangzhou.aliyuncs.com", url)

    @patch("apps.files.storage_backends.oss2")
    def test_delete_file(self, mock_oss2):
        """测试从OSS删除文件"""
        mock_bucket = Mock()
        mock_oss2.Auth.return_value = Mock()
        mock_oss2.Bucket.return_value = mock_bucket
        mock_oss2.exceptions = MagicMock()

        backend = OSSStorageBackend(self.config)
        backend.exists = Mock(return_value=True)

        # 删除文件
        backend.delete("test/test.txt")

        # 验证delete_object被调用
        self.assertTrue(mock_bucket.delete_object.called)

    @patch("apps.files.storage_backends.oss2")
    def test_get_url(self, mock_oss2):
        """测试获取OSS文件URL"""
        mock_bucket = Mock()
        mock_oss2.Auth.return_value = Mock()
        mock_oss2.Bucket.return_value = mock_bucket

        backend = OSSStorageBackend(self.config)
        url = backend.url("test/test.txt")

        # 验证URL格式
        self.assertIn("oss-cn-hangzhou.aliyuncs.com", url)


class StorageBackendFactoryTestCase(TestCase):
    """存储后端工厂测试"""

    def test_create_local_backend(self):
        """测试创建本地存储后端"""
        backend = StorageBackendFactory.create_backend("local", {})
        self.assertIsInstance(backend, LocalStorageBackend)

    @patch.dict(
        os.environ,
        {
            "AWS_S3_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    )
    def test_create_s3_backend(self):
        """测试创建S3存储后端"""
        backend = StorageBackendFactory.create_backend("s3", {})
        self.assertIsInstance(backend, S3StorageBackend)

    def test_create_oss_backend(self):
        """测试创建OSS存储后端"""
        import importlib.util

        if not importlib.util.find_spec("oss2"):
            self.skipTest("oss2库未安装")

        with patch.dict(
            os.environ,
            {
                "ALIYUN_OSS_BUCKET_NAME": "test-bucket",
                "ALIYUN_ACCESS_KEY_ID": "test-key",
                "ALIYUN_ACCESS_KEY_SECRET": "test-secret",
                "ALIYUN_OSS_ENDPOINT": "oss-cn-hangzhou.aliyuncs.com",
            },
        ):
            backend = StorageBackendFactory.create_backend("oss", {})
            self.assertIsInstance(backend, OSSStorageBackend)

    def test_invalid_backend_type(self):
        """测试无效的存储类型"""
        with self.assertRaises(ValueError) as context:
            StorageBackendFactory.create_backend("invalid")

        self.assertIn("不支持的存储类型", str(context.exception))

    @patch.dict(os.environ, {"DEFAULT_STORAGE_BACKEND": "local"})
    def test_get_current_backend(self):
        """测试获取当前配置的存储后端"""
        with patch("apps.files.storage_backends.settings") as mock_settings:
            mock_settings.DEFAULT_STORAGE_BACKEND = "local"
            mock_settings.STORAGE_BACKEND_CONFIG = {}

            backend = StorageBackendFactory.get_current_backend()
            self.assertIsInstance(backend, LocalStorageBackend)


class GetStorageBackendTestCase(TestCase):
    """get_storage_backend便捷函数测试"""

    @patch("apps.files.storage_backends.StorageBackendFactory.get_current_backend")
    def test_get_storage_backend(self, mock_get_current):
        """测试get_storage_backend函数"""
        mock_backend = Mock()
        mock_get_current.return_value = mock_backend

        backend = get_storage_backend()

        # 验证返回正确的后端
        self.assertEqual(backend, mock_backend)
