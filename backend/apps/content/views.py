"""
内容管理视图
提供图片、视频等内容的访问接口
"""

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class StorageImageListView(APIView):
    """
    获取 storage/image 目录下的所有图片列表（递归遍历子目录）
    """
    permission_classes = [AllowAny]  # 允许未认证访问

    def get(self, request):
        """
        返回图片列表，包含文件名、大小、修改时间等信息
        """
        try:
            image_dir = Path(settings.STORAGE_ROOT) / 'image'

            # 确保目录存在
            if not image_dir.exists():
                return Response({
                    'success': False,
                    'message': '图片目录不存在',
                    'data': []
                }, status=status.HTTP_404_NOT_FOUND)

            # 支持的图片格式
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}

            images = []
            # 递归遍历所有子目录
            for file_path in image_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    stat = file_path.stat()
                    # 计算相对于image目录的路径
                    relative_path = file_path.relative_to(image_dir)
                    images.append({
                        'name': file_path.name,
                        'path': str(relative_path),  # 例如: 2025-11-30/xx.png
                        'size': stat.st_size,
                        'modified_time': stat.st_mtime,
                        'url': f'/api/v1/content/storage/image/{relative_path}'
                    })

            # 按修改时间倒序排列
            images.sort(key=lambda x: x['modified_time'], reverse=True)

            return Response({
                'success': True,
                'message': '获取图片列表成功',
                'data': images,
                'total': len(images)
            })

        except Exception as e:
            return Response({
                'success': False,
                'message': f'获取图片列表失败: {e!s}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StorageImageDetailView(APIView):
    """
    访问 storage/image 目录下的单个图片文件（支持日期子目录）
    例如: /api/v1/content/storage/image/2025-11-30/xx.png
    """
    permission_classes = [AllowAny]  # 允许未认证访问

    def get(self, request, filepath):
        """
        返回指定的图片文件
        :param filepath: 相对于storage/image的文件路径，例如: 2025-11-30/xx.png
        """
        try:
            # 构建文件路径
            image_path = Path(settings.STORAGE_ROOT) / 'image' / filepath

            # 安全检查：确保路径在允许的目录内（防止路径遍历攻击）
            storage_root = Path(settings.STORAGE_ROOT).resolve()
            resolved_path = image_path.resolve()

            if not str(resolved_path).startswith(str(storage_root)):
                raise Http404('非法的文件路径')

            # 检查文件是否存在
            if not image_path.exists() or not image_path.is_file():
                raise Http404('图片文件不存在')

            # 返回文件响应
            return FileResponse(
                open(image_path, 'rb'),
                content_type=self._get_content_type(image_path.suffix)
            )

        except Http404:
            raise
        except Exception as e:
            raise Http404(f'访问图片失败: {e!s}')

    def _get_content_type(self, extension):
        """
        根据文件扩展名返回对应的 Content-Type
        """
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml',
        }
        return content_types.get(extension.lower(), 'application/octet-stream')

class StorageVideoDetailView(APIView):
    """
    访问 storage/video 目录下的单个视频文件（支持日期子目录）
    例如: /api/v1/content/storage/video/2025-11-30/xx.mp4
    """
    permission_classes = [AllowAny]  # 允许未认证访问

    def get(self, request, filepath):
        """
        返回指定的视频文件
        :param filepath: 相对于storage/video的文件路径，例如: 2025-11-30/xx.mp4
        """
        try:
            # 构建文件路径
            video_path = Path(settings.STORAGE_ROOT) / 'video' / filepath

            # 安全检查：确保路径在允许的目录内（防止路径遍历攻击）
            storage_root = Path(settings.STORAGE_ROOT).resolve()
            resolved_path = video_path.resolve()

            if not str(resolved_path).startswith(str(storage_root)):
                raise Http404('非法的文件路径')

            # 检查文件是否存在
            if not video_path.exists() or not video_path.is_file():
                raise Http404('视频文件不存在')

            # 返回文件响应
            return FileResponse(
                open(video_path, 'rb'),
                content_type=self._get_content_type(video_path.suffix)
            )

        except Http404:
            raise
        except Exception as e:
            raise Http404(f'访问视频失败: {e!s}')

    def _get_content_type(self, extension):
        """
        根据文件扩展名返回对应的 Content-Type
        """
        content_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
        }
        return content_types.get(extension.lower(), 'application/octet-stream')
