"""
文件上传API测试
Epic 6: 文件管理与预览
Story 6.1: 文件上传API
"""

import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class FileUploadAPITestCase(APITestCase):
    """文件上传API测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_upload_image_success(self):
        """测试上传图片成功"""
        # 创建临时图片文件
        image = Image.new('RGB', (100, 100), color='red')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file, format='JPEG')
            tmp_path = tmp_file.name

        # 读取文件并创建上传文件对象
        with open(tmp_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_image.jpg',
                f.read(),
                content_type='image/jpeg'
            )

        # 发送上传请求
        response = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file},
            format='multipart'
        )

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('file', response.data)
        self.assertEqual(response.data['file']['file_type'], 'image')
        self.assertEqual(response.data['file']['original_filename'], 'test_image.jpg')

        # 清理临时文件
        os.unlink(tmp_file.name)

    def test_upload_document_success(self):
        """测试上传文档成功"""
        # 创建临时文本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write('This is a test document.')
            tmp_path = tmp_file.name

        # 读取文件并创建上传文件对象
        with open(tmp_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_document.txt',
                f.read(),
                content_type='text/plain'
            )

        # 发送上传请求
        response = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file},
            format='multipart'
        )

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['file']['file_type'], 'document')

        # 清理临时文件
        os.unlink(tmp_file.name)

    def test_upload_file_too_large(self):
        """测试上传文件过大"""
        # 创建超大文件（>100MB）
        large_file = SimpleUploadedFile(
            "large_file.jpg",
            b"0" * (101 * 1024 * 1024),  # 101MB
            content_type="image/jpeg"
        )

        # 发送上传请求
        response = self.client.post(
            '/api/v1/files/upload/',
            {'file': large_file},
            format='multipart'
        )

        # 验证响应（应该失败）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_invalid_file_type(self):
        """测试上传不支持的文件类型"""
        # 创建不支持的文件类型
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"invalid executable",
            content_type="application/x-msdownload"
        )

        # 发送上传请求
        response = self.client.post(
            '/api/v1/files/upload/',
            {'file': invalid_file},
            format='multipart'
        )

        # 验证响应（应该失败）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_files(self):
        """测试获取文件列表"""
        # 先上传一个文件
        image = Image.new('RGB', (100, 100), color='blue')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            image.save(tmp_file, format='PNG')
            tmp_path = tmp_file.name

        with open(tmp_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_list.png',
                f.read(),
                content_type='image/png'
            )

        self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file},
            format='multipart'
        )

        # 获取文件列表
        response = self.client.get('/api/v1/files/')

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

        # 清理临时文件
        os.unlink(tmp_file.name)

    def test_get_file_detail(self):
        """测试获取文件详情"""
        # 先上传一个文件
        image = Image.new('RGB', (100, 100), color='green')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file, format='JPEG')
            tmp_path = tmp_file.name

        with open(tmp_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_detail.jpg',
                f.read(),
                content_type='image/jpeg'
            )

        upload_response = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file},
            format='multipart'
        )

        file_id = upload_response.data['file']['id']

        # 获取文件详情
        response = self.client.get(f'/api/v1/files/{file_id}/')

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(file_id))
        self.assertEqual(response.data['original_filename'], 'test_detail.jpg')

        # 清理临时文件
        os.unlink(tmp_file.name)

    def test_delete_file(self):
        """测试删除文件"""
        # 先上传一个文件
        image = Image.new('RGB', (100, 100), color='yellow')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file, format='JPEG')
            tmp_path = tmp_file.name

        with open(tmp_path, 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                'test_delete.jpg',
                f.read(),
                content_type='image/jpeg'
            )

        upload_response = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file},
            format='multipart'
        )

        file_id = upload_response.data['file']['id']

        # 删除文件
        response = self.client.delete(f'/api/v1/files/{file_id}/')

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证文件已被删除
        get_response = self.client.get(f'/api/v1/files/{file_id}/')
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

        # 清理临时文件
        os.unlink(tmp_file.name)

    def test_get_quota(self):
        """测试获取配额信息"""
        response = self.client.get('/api/v1/files/quota/')

        # 验证响应
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('max_total_size', response.data)
        self.assertIn('used_total_size', response.data)
        self.assertIn('usage_percentage', response.data)

    def test_file_deduplication(self):
        """测试文件去重功能"""
        # 创建文件
        image = Image.new('RGB', (50, 50), color='red')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file, format='JPEG')
            tmp_path = tmp_file.name

        with open(tmp_path, 'rb') as f:
            file_content = f.read()

        # 第一次上传
        uploaded_file1 = SimpleUploadedFile(
            'duplicate.jpg',
            file_content,
            content_type='image/jpeg'
        )
        response1 = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file1},
            format='multipart'
        )

        # 第二次上传相同文件
        uploaded_file2 = SimpleUploadedFile(
            'duplicate.jpg',
            file_content,
            content_type='image/jpeg'
        )
        response2 = self.client.post(
            '/api/v1/files/upload/',
            {'file': uploaded_file2},
            format='multipart'
        )

        # 验证第二次上传返回已存在的文件
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['message'], '文件已存在')
        self.assertEqual(
            response1.data['file']['id'],
            response2.data['file']['id']
        )

        # 清理临时文件
        os.unlink(tmp_file.name)
