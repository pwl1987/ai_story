"""
文件管理序列化器
Epic 6: 文件管理与预览
Story 6.1: 文件上传API
"""

import hashlib
import os

from django.core.files.base import File
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import FileQuota, UploadedFile


class UploadedFileSerializer(serializers.ModelSerializer):
    """
    上传文件序列化器
    """

    file_size_human = serializers.ReadOnlyField()
    file_url = serializers.ReadOnlyField()
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UploadedFile
        fields = [
            "id",
            "user",
            "username",
            "project",
            "original_filename",
            "file",
            "file_type",
            "file_size",
            "file_size_human",
            "mime_type",
            "file_hash",
            "file_url",
            "uploaded_at",
            "uploaded_from",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "file_size",
            "mime_type",
            "file_hash",
            "file_url",
            "file_size_human",
        ]

    def validate_file(self, value: File):
        """
        验证上传文件
        """
        # 检查文件大小
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise ValidationError(f"文件大小不能超过 {max_size / (1024 * 1024):.0f}MB")

        # 检查文件扩展名
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = {
            # 图片
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            # 视频
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".mkv",
            # 文档
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".md",
            ".html",
            ".json",
            ".csv",
            # 音频
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
        }

        if ext not in allowed_extensions:
            raise ValidationError(f"不支持的文件格式: {ext}")

        return value

    def validate(self, attrs):
        """
        验证整体数据
        """
        # 检查用户配额
        user = attrs.get("user")
        file = attrs.get("file")

        if user and file:
            # 获取或创建用户配额
            quota, _created = FileQuota.objects.get_or_create(user=user)

            # 检查配额
            allowed, message = quota.check_quota(file.size)
            if not allowed:
                raise ValidationError({"file": message})

        return attrs

    def create(self, validated_data):
        """
        创建上传文件记录
        """
        file = validated_data["file"]
        user = validated_data.get("user")

        # 计算文件哈希
        file_hash = self._calculate_file_hash(file)
        validated_data["file_hash"] = file_hash

        # 自动检测文件类型
        validated_data["file_type"] = self._detect_file_type(file.name)

        # 保存文件记录
        uploaded_file = super().create(validated_data)

        # 更新用户配额
        if user:
            quota, _created = FileQuota.objects.get_or_create(user=user)
            quota.update_usage(file.size, increment=True)

        return uploaded_file

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

    def _detect_file_type(self, filename):
        """
        根据文件名检测文件类型
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext in UploadedFile.IMAGE_EXTENSIONS:
            return "image"
        elif ext in UploadedFile.VIDEO_EXTENSIONS:
            return "video"
        elif ext in UploadedFile.DOCUMENT_EXTENSIONS:
            return "document"
        elif ext in UploadedFile.AUDIO_EXTENSIONS:
            return "audio"
        else:
            return "other"


class UploadedFileListSerializer(serializers.ModelSerializer):
    """
    上传文件列表序列化器（简化版）
    """

    file_size_human = serializers.ReadOnlyField()
    file_url = serializers.ReadOnlyField()
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UploadedFile
        fields = [
            "id",
            "username",
            "original_filename",
            "file_type",
            "file_size",
            "file_size_human",
            "mime_type",
            "file_url",
            "uploaded_at",
            "is_active",
        ]
        read_only_fields = fields


class FileQuotaSerializer(serializers.ModelSerializer):
    """
    文件配额序列化器
    """

    usage_percentage = serializers.FloatField(read_only=True)
    remaining_size = serializers.IntegerField(read_only=True)
    remaining_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FileQuota
        fields = [
            "user",
            "max_total_size",
            "max_single_file",
            "max_file_count",
            "used_total_size",
            "used_file_count",
            "usage_percentage",
            "remaining_size",
            "remaining_count",
        ]
        read_only_fields = [
            "used_total_size",
            "used_file_count",
            "usage_percentage",
            "remaining_size",
            "remaining_count",
        ]


class FileUploadSerializer(serializers.Serializer):
    """
    文件上传序列化器（专用）
    """

    file = serializers.FileField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "jpg",
                    "jpeg",
                    "png",
                    "gif",
                    "bmp",
                    "webp",
                    "svg",
                    "mp4",
                    "avi",
                    "mov",
                    "wmv",
                    "flv",
                    "webm",
                    "mkv",
                    "pdf",
                    "doc",
                    "docx",
                    "txt",
                    "md",
                    "html",
                    "json",
                    "csv",
                    "mp3",
                    "wav",
                    "flac",
                    "aac",
                    "ogg",
                ]
            )
        ],
    )
    file_type = serializers.ChoiceField(
        choices=UploadedFile.FILE_TYPE_CHOICES, required=False, default="other"
    )
    project = serializers.UUIDField(required=False, allow_null=True)

    def validate_file(self, value):
        """
        验证上传文件
        """
        # 检查文件大小
        max_size = 100 * 1024 * 1024  # 100MB
        if value.size > max_size:
            raise ValidationError(f"文件大小不能超过 {max_size / (1024 * 1024):.0f}MB")

        return value
