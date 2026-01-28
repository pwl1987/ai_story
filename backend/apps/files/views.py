"""
文件管理视图
Epic 6: 文件管理与预览
Story 6.1: 文件上传API
Story 6.3: 文件预览功能
Story 6.4: 文件管理和删除
"""

import os
import hashlib
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile as DjangoUploadedFile
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError

from .models import UploadedFile, FileQuota
from .serializers import (
    UploadedFileSerializer,
    UploadedFileListSerializer,
    FileQuotaSerializer,
    FileUploadSerializer,
)


class FileUploadViewSet(viewsets.ModelViewSet):
    """
    文件上传管理ViewSet
    Epic 6: 文件管理与预览
    Story 6.1: 文件上传API

    API端点:
    - POST /api/v1/files/upload/ - 上传文件
    - GET /api/v1/files/ - 获取文件列表
    - GET /api/v1/files/{id}/ - 获取文件详情
    - GET /api/v1/files/{id}/download/ - 下载文件
    - DELETE /api/v1/files/{id}/ - 删除文件
    - GET /api/v1/files/quota/ - 获取用户配额信息
    """

    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """
        获取当前用户的文件列表
        支持筛选: file_type, is_active
        """
        queryset = UploadedFile.objects.filter(user=self.request.user)

        # 文件类型筛选
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        # 状态筛选
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')

        return queryset.select_related('user', 'project')

    def get_serializer_class(self):
        """
        根据action返回不同的序列化器
        """
        if self.action == 'list':
            return UploadedFileListSerializer
        elif self.action == 'upload':
            return FileUploadSerializer
        return UploadedFileSerializer

    def perform_create(self, serializer):
        """
        创建文件记录时自动设置用户
        """
        serializer.save(user=self.request.user, uploaded_from='api')

    def destroy(self, request, *args, **kwargs):
        """
        删除文件
        """
        instance = self.get_object()

        # 更新用户配额
        quota, created = FileQuota.objects.get_or_create(user=instance.user)
        quota.update_usage(instance.file_size, increment=False)

        # 删除物理文件
        if instance.file:
            if os.path.exists(instance.file.path):
                os.remove(instance.file.path)

        # 删除数据库记录
        instance.delete()

        return Response({'message': '文件已删除'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        上传文件
        POST /api/v1/files/upload/

        请求体 (multipart/form-data):
        - file: 文件（必填）
        - file_type: 文件类型（可选，自动检测）
        - project: 项目ID（可选）

        响应:
        {
            "id": "uuid",
            "original_filename": "example.jpg",
            "file_type": "image",
            "file_size": 1234567,
            "file_url": "/api/v1/files/uuid/download/",
            "uploaded_at": "2026-01-28T12:00:00Z"
        }
        """
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        file_type = serializer.validated_data.get('file_type', 'other')
        project_id = serializer.validated_data.get('project')

        # 检查用户配额
        quota, created = FileQuota.objects.get_or_create(user=request.user)
        allowed, message = quota.check_quota(uploaded_file.size)
        if not allowed:
            return Response({
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)

        # 自动检测文件类型
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in UploadedFile.IMAGE_EXTENSIONS:
            file_type = 'image'
        elif ext in UploadedFile.VIDEO_EXTENSIONS:
            file_type = 'video'
        elif ext in UploadedFile.DOCUMENT_EXTENSIONS:
            file_type = 'document'
        elif ext in UploadedFile.AUDIO_EXTENSIONS:
            file_type = 'audio'
        else:
            file_type = 'other'

        # 计算文件哈希
        file_hash = self._calculate_file_hash(uploaded_file)

        # 检查是否已存在相同文件
        existing_file = UploadedFile.objects.filter(
            user=request.user,
            file_hash=file_hash,
            original_filename=uploaded_file.name
        ).first()

        if existing_file:
            return Response({
                'message': '文件已存在',
                'file': UploadedFileSerializer(existing_file).data
            }, status=status.HTTP_200_OK)

        # 创建文件记录
        uploaded_file_obj = UploadedFile.objects.create(
            user=request.user,
            original_filename=uploaded_file.name,
            file=uploaded_file,
            file_type=file_type,
            file_size=uploaded_file.size,
            file_hash=file_hash,
            project_id=project_id,
            uploaded_from='api'
        )

        # 更新用户配额
        quota.update_usage(uploaded_file.size, increment=True)

        return Response({
            'message': '文件上传成功',
            'file': UploadedFileSerializer(uploaded_file_obj).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        下载文件
        GET /api/v1/files/{id}/download/
        """
        try:
            uploaded_file = self.get_object()

            if not uploaded_file.file or not uploaded_file.file.storage.exists(uploaded_file.file.name):
                return Response({
                    'error': '文件不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            # 返回文件响应
            response = FileResponse(
                uploaded_file.file.open('rb'),
                content_type=uploaded_file.mime_type
            )
            response['Content-Disposition'] = f'attachment; filename="{uploaded_file.original_filename}"'
            return response

        except Exception as e:
            return Response({
                'error': f'下载失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='quota')
    def quota(self, request):
        """
        获取用户配额信息
        GET /api/v1/files/quota/

        响应:
        {
            "max_total_size": 5368709120,  # 5GB
            "max_single_file": 104857600,  # 100MB
            "max_file_count": 1000,
            "used_total_size": 52428800,   # 50MB
            "used_file_count": 10,
            "usage_percentage": 1.0,
            "remaining_size": 5316280320,
            "remaining_count": 990
        }
        """
        quota, created = FileQuota.objects.get_or_create(user=request.user)
        serializer = FileQuotaSerializer(quota)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        获取文件统计信息
        GET /api/v1/files/statistics/

        响应:
        {
            "total_files": 100,
            "total_size": 1073741824,
            "by_type": {
                "image": 50,
                "video": 30,
                "document": 20
            }
        }
        """
        from django.db.models import Count, Sum, Q

        queryset = UploadedFile.objects.filter(user=request.user)

        # 总文件数和总大小
        total_files = queryset.count()
        total_size = queryset.aggregate(total=Sum('file_size'))['total'] or 0

        # 按类型统计
        by_type = {}
        for file_type, _ in UploadedFile.FILE_TYPE_CHOICES:
            count = queryset.filter(file_type=file_type).count()
            if count > 0:
                by_type[file_type] = count

        return Response({
            'total_files': total_files,
            'total_size': total_size,
            'by_type': by_type
        })

    def _calculate_file_hash(self, file):
        """
        计算文件SHA256哈希
        """
        # 重置文件指针
        file.seek(0)

        # 计算哈希
        hasher = hashlib.sha256()
        for chunk in file.chunks(8192):
            hasher.update(chunk)

        # 重置文件指针
        file.seek(0)

        return hasher.hexdigest()


class FilePreviewView(APIView):
    """
    文件预览视图
    Epic 6: 文件管理与预览
    Story 6.3: 文件预览功能

    GET /api/v1/files/{id}/preview/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        """
        预览文件（内联显示）
        """
        try:
            uploaded_file = UploadedFile.objects.get(pk=pk, user=request.user)

            if not uploaded_file.file or not uploaded_file.file.storage.exists(uploaded_file.file.name):
                raise Http404('文件不存在')

            # 返回文件响应（inline）
            response = FileResponse(
                uploaded_file.file.open('rb'),
                content_type=uploaded_file.mime_type
            )
            response['Content-Disposition'] = f'inline; filename="{uploaded_file.original_filename}"'
            return response

        except UploadedFile.DoesNotExist:
            raise Http404('文件不存在')
        except Exception as e:
            return Response({
                'error': f'预览失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PublicFileView(APIView):
    """
    公开文件访问视图（无需认证）
    用于访问已公开的文件

    GET /api/v1/files/public/{file_hash}/
    """
    permission_classes = [AllowAny]

    def get(self, request, file_hash=None):
        """
        通过文件哈希访问公开文件
        """
        try:
            uploaded_file = UploadedFile.objects.get(file_hash=file_hash, is_active=True)

            if not uploaded_file.file or not uploaded_file.file.storage.exists(uploaded_file.file.name):
                raise Http404('文件不存在')

            # 返回文件响应
            response = FileResponse(
                uploaded_file.file.open('rb'),
                content_type=uploaded_file.mime_type
            )
            response['Content-Disposition'] = f'inline; filename="{uploaded_file.original_filename}"'
            return response

        except UploadedFile.DoesNotExist:
            raise Http404('文件不存在')
