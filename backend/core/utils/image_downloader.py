"""
图片下载工具
职责: 从远程URL下载图片到本地存储
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


class ImageDownloader:
    """图片下载器"""

    def __init__(self):
        self.download_timeout = 30  # 下载超时时间(秒)
        self.max_file_size = 50 * 1024 * 1024  # 最大文件大小(50MB)

    def download_image(
        self,
        image_url: str,
        subfolder: str = "generated_images"
    ) -> Tuple[bool, str, dict]:
        """
        下载图片到本地

        Args:
            image_url: 图片URL
            subfolder: 存储子文件夹名称

        Returns:
            Tuple[success: bool, local_path: str, metadata: dict]
        """
        try:
            # 验证URL
            if not image_url or not image_url.startswith(('http://', 'https://')):
                return False, "", {"error": "无效的图片URL"}

            # 发送HTTP请求获取图片
            response = requests.get(
                image_url,
                stream=True,
                timeout=self.download_timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            response.raise_for_status()

            # 检查文件大小
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                return False, "", {
                    "error": f"文件过大: {int(content_length) / 1024 / 1024:.1f}MB"
                }

            # 检查Content-Type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False, "", {"error": f"非图片格式: {content_type}"}

            # 生成文件名和路径
            file_extension = self._get_file_extension(content_type, image_url)
            filename = f"{uuid.uuid4()}{file_extension}"

            # 构建存储路径: media/subfolder/UUID.ext
            relative_path = os.path.join(subfolder, filename)

            # 读取图片内容
            image_content = response.content

            # 验证图片内容（简单检查文件头）
            if not self._validate_image_content(image_content):
                return False, "", {"error": "图片内容验证失败"}

            # 保存到Django的media目录
            saved_path = default_storage.save(relative_path, ContentFile(image_content))
            local_url = default_storage.url(saved_path)

            # 获取文件信息
            file_size = len(image_content)
            width, height = self._get_image_dimensions(image_content)

            metadata = {
                "original_url": image_url,
                "local_path": saved_path,
                "local_url": local_url,
                "file_size": file_size,
                "width": width,
                "height": height,
                "content_type": content_type,
                "filename": filename
            }

            logger.info(f"图片下��成功: {image_url} -> {saved_path}")
            return True, local_url, metadata

        except requests.exceptions.Timeout:
            error_msg = f"下载超时: {image_url}"
            logger.error(error_msg)
            return False, "", {"error": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败: {e!s}"
            logger.error(f"{error_msg}, URL: {image_url}")
            return False, "", {"error": error_msg}

        except Exception as e:
            error_msg = f"未知错误: {e!s}"
            logger.error(f"图片下载异常: {error_msg}, URL: {image_url}", exc_info=True)
            return False, "", {"error": error_msg}

    def _get_file_extension(self, content_type: str, url: str) -> str:
        """根据Content-Type或URL获取文件扩展名"""
        # 优先从Content-Type获取
        if content_type:
            type_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.webp',
                'image/bmp': '.bmp',
                'image/tiff': '.tiff'
            }
            if content_type.lower() in type_map:
                return type_map[content_type.lower()]

        # 从URL路径获取
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        if path.endswith(('.jpg', '.jpeg')):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        elif path.endswith('.bmp'):
            return '.bmp'
        elif path.endswith('.tiff', '.tif'):
            return '.tiff'

        # 默认使用.jpg
        return '.jpg'

    def _validate_image_content(self, content: bytes) -> bool:
        """验证图片内容（检查文件头）"""
        if len(content) < 8:
            return False

        # 检查常见图片格式的文件头
        image_signatures = [
            # JPEG
            b'\xFF\xD8\xFF',
            # PNG
            b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
            # GIF
            b'GIF87a',
            b'GIF89a',
            # WebP
            b'RIFF',
            # BMP
            b'BM',
        ]

        return any(content.startswith(sig) for sig in image_signatures)

    def _get_image_dimensions(self, content: bytes) -> Tuple[int, int]:
        """获取图片尺寸（简化版，返回默认值）"""
        # 这里可以集成PIL库来获取真实的图片尺寸
        # 为了减少依赖，暂时返回默认值
        return 0, 0

    def cleanup_local_file(self, local_path: str) -> bool:
        """清理本地文件"""
        try:
            if default_storage.exists(local_path):
                default_storage.delete(local_path)
                logger.info(f"本地文件已删除: {local_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除本地文件失败: {local_path}, 错误: {e!s}")
            return False


# 全局下载器实例
image_downloader = ImageDownloader()
