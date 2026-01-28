"""
文件预览服务
Epic 6.3: 文件预览功能

提供文件预览功能：
1. 图片缩略图生成
2. 视频首帧提取
3. 文档预览（PDF/文本）
"""

import io
import os
from pathlib import Path

from django.conf import settings
from PIL import Image


class FilePreviewService:
    """
    文件预览服务
    遵循单一职责原则(SRP)
    """

    def __init__(self):
        """初始化预览服务"""
        self.thumbnail_size = (200, 200)  # 缩略图大小
        self.preview_root = Path(settings.STORAGE_ROOT) / 'previews'
        self.preview_root.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail(self, file_path, size=None):
        """
        生成图片缩略图

        :param file_path: 原始图片路径
        :param size: 缩略图大小 (width, height)，默认(200, 200)
        :return: 缩略图相对路径
        """
        if size is None:
            size = self.thumbnail_size

        try:
            # 获取绝对路径
            full_path = Path(settings.STORAGE_ROOT) / file_path

            if not full_path.exists():
                raise FileNotFoundError(f'文件不存在: {file_path}')

            # 打开图片并生成缩略图
            with Image.open(full_path) as img:
                img.thumbnail(size)

                # 生成缩略图文件名
                preview_filename = f"thumb_{full_path.name}"
                preview_path = self.preview_root / preview_filename

                # 保存缩略图
                img.save(preview_path, 'JPEG', quality=85)

                # 返回相对路径
                return f"previews/{preview_filename}"

        except Exception as e:
            raise Exception(f'生成缩略图失败: {e!s}')

    def extract_video_frame(self, file_path, time_offset=0):
        """
        提取视频首帧作为预览图

        :param file_path: 视频文件路径
        :param time_offset: 提取帧的时间偏移（秒），默认0（首帧）
        :return: 预览图相对路径
        """
        try:
            import cv2

            # 获取绝对路径
            full_path = Path(settings.STORAGE_ROOT) / file_path

            if not full_path.exists():
                raise FileNotFoundError(f'文件不存在: {file_path}')

            # 打开视频
            video = cv2.VideoCapture(str(full_path))

            # 跳转到指定时间
            video.set(cv2.CAP_PROP_POS_MSEC, time_offset * 1000)

            # 读取帧
            success, frame = video.read()
            video.release()

            if not success:
                raise Exception('无法读取视频帧')

            # 保存预览图
            preview_filename = f"preview_{full_path.stem}.jpg"
            preview_path = self.preview_root / preview_filename

            cv2.imwrite(str(preview_path), frame)

            return f"previews/{preview_filename}"

        except ImportError:
            # 如果没有cv2，返回None
            return None
        except Exception as e:
            raise Exception(f'提取视频帧失败: {e!s}')

    def generate_pdf_preview(self, file_path, page=0):
        """
        生成PDF预览图

        :param file_path: PDF文件路径
        :param page: 要预览的页码，默认0（第一页）
        :return: 预览图相对路径
        """
        try:
            from pdf2image import convert_from_path

            # 获取绝对路径
            full_path = Path(settings.STORAGE_ROOT) / file_path

            if not full_path.exists():
                raise FileNotFoundError(f'文件不存在: {file_path}')

            # 转换指定页为图片
            images = convert_from_path(str(full_path), first_page=page + 1, last_page=page + 2)

            if not images:
                raise Exception('无法转换PDF')

            # 保存预览图
            preview_filename = f"preview_{full_path.stem}_page{page}.jpg"
            preview_path = self.preview_root / preview_filename

            images[0].save(preview_path, 'JPEG', quality=85)

            return f"previews/{preview_filename}"

        except ImportError:
            # 如果没有pdf2image，返回None
            return None
        except Exception as e:
            raise Exception(f'生成PDF预览失败: {e!s}')

    def get_preview(self, file_type, file_path):
        """
        根据文件类型获取预览

        :param file_type: 文件类型 (image, video, document)
        :param file_path: 文件路径
        :return: 预览图路径或None
        """
        try:
            if file_type == 'image':
                return self.generate_thumbnail(file_path)
            elif file_type == 'video':
                return self.extract_video_frame(file_path)
            elif file_type == 'document':
                # 检查是否为PDF
                if file_path.lower().endswith('.pdf'):
                    return self.generate_pdf_preview(file_path)
                else:
                    # 其他文档类型返回None
                    return None
            else:
                return None
        except Exception:
            # 预览生成失败，返回None
            return None

    def cleanup_previews(self, older_than_days=7):
        """
        清理过期的预览文件

        :param older_than_days: 清理多少天前的预览，默认7天
        """
        import time
        from pathlib import Path

        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)

        for preview_file in self.preview_root.iterdir():
            if preview_file.is_file() and preview_file.stat().st_mtime < cutoff_time:
                preview_file.unlink()


# 便捷函数
def get_preview_service():
    """获取预览服务实例"""
    return FilePreviewService()
