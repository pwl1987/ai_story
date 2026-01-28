"""
文件管理数据模型
Epic 6: 文件管理与预览
Story 6.1: 文件上传API
遵循单一职责原则(SRP): 每个模型只负责一种文件类型
"""

import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def file_upload_path(instance, filename):
    """
    动态生成文件上传路径
    格式: storage/{file_type}/{year}-{month}-{day}/{uuid}_{filename}
    """
    from django.utils import timezone

    file_type = instance.file_type
    ext = os.path.splitext(filename)[1]
    new_filename = f"{instance.id}{ext}"

    # 使用当前时间（因为instance.uploaded_at在创建时还未设置）
    now = timezone.now()
    return f"storage/{file_type}/{now:%Y-%m-%d}/{new_filename}"


class UploadedFile(models.Model):
    """
    上传文件模型
    职责: 存储所有上传文件的元数据
    """

    FILE_TYPE_CHOICES = [
        ('image', '图片'),
        ('video', '视频'),
        ('document', '文档'),
        ('audio', '音频'),
        ('other', '其他'),
    ]

    # 文件类型分类
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
    DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.md', '.html', '.json'}
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg'}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='上传用户',
        null=True,  # 允许匿名上传
        blank=True
    )

    # 文件信息
    original_filename = models.CharField('原始文件名', max_length=255)
    file = models.FileField('文件路径', upload_to=file_upload_path, max_length=1024)

    # 文件类型
    file_type = models.CharField(
        '文件类型',
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default='other'
    )

    # 文件属性
    file_size = models.BigIntegerField('文件大小(字节)', editable=False)
    mime_type = models.CharField('MIME类型', max_length=100, editable=False)

    # 文件哈希（用于去重）
    file_hash = models.CharField('文件哈希(SHA256)', max_length=64, blank=True, editable=False)

    # 关联项目（可选）
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        related_name='uploaded_files',
        verbose_name='关联项目',
        null=True,
        blank=True
    )

    # 上传元数据
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    uploaded_from = models.CharField('上传来源', max_length=50, default='web')  # web, api, cli

    # 状态
    is_active = models.BooleanField('是否有效', default=True)

    class Meta:
        db_table = 'uploaded_files'
        verbose_name = '上传文件'
        verbose_name_plural = '上传文件'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['project', 'file_type']),
            models.Index(fields=['file_hash']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return f'{self.original_filename} ({self.file_type})'

    def clean(self):
        """验证文件"""
        super().clean()

        # 验证文件扩展名
        ext = os.path.splitext(self.original_filename)[1].lower()

        # 检查文件类型
        if ext in self.IMAGE_EXTENSIONS:
            expected_type = 'image'
        elif ext in self.VIDEO_EXTENSIONS:
            expected_type = 'video'
        elif ext in self.DOCUMENT_EXTENSIONS:
            expected_type = 'document'
        elif ext in self.AUDIO_EXTENSIONS:
            expected_type = 'audio'
        else:
            expected_type = 'other'

        if self.file_type != expected_type:
            raise ValidationError({
                'file_type': f'文件类型不匹配，应该是 {expected_type}'
            })

    def save(self, *args, **kwargs):
        # 自动设置文件大小
        if self.file:
            self.file_size = self.file.size

        # 自动检测MIME类型
        if self.file:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(self.original_filename)
            self.mime_type = mime_type or 'application/octet-stream'

        super().save(*args, **kwargs)

    @property
    def file_url(self):
        """获取文件访问URL"""
        from django.conf import settings
        if settings.DEBUG:
            return f'/api/v1/files/{self.id}/download/'
        else:
            return self.file.url

    @property
    def file_size_human(self):
        """人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.2f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.2f} TB"


class FileQuota(models.Model):
    """
    用户文件配额
    职责: 管理用户的存储配额和限制
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='file_quota',
        verbose_name='用户'
    )

    # 配额设置（字节）
    max_total_size = models.BigIntegerField('最大总容量', default=5 * 1024 * 1024 * 1024)  # 5GB
    max_single_file = models.BigIntegerField('单文件最大', default=100 * 1024 * 1024)  # 100MB
    max_file_count = models.IntegerField('最大文件数量', default=1000)

    # 当前使用量
    used_total_size = models.BigIntegerField('已用容量', default=0, editable=False)
    used_file_count = models.IntegerField('已用文件数', default=0, editable=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'file_quotas'
        verbose_name = '文件配额'
        verbose_name_plural = '文件配额'

    def __str__(self):
        return f'{self.user.username} - {self.used_total_size}/{self.max_total_size}'

    @property
    def usage_percentage(self):
        """使用百分比"""
        if self.max_total_size == 0:
            return 0
        return (self.used_total_size / self.max_total_size) * 100

    @property
    def remaining_size(self):
        """剩余容量"""
        return max(0, self.max_total_size - self.used_total_size)

    @property
    def remaining_count(self):
        """剩余文件数"""
        return max(0, self.max_file_count - self.used_file_count)

    def check_quota(self, file_size):
        """
        检查配额是否允许上传
        返回: (is_allowed, error_message)
        """
        if file_size > self.max_single_file:
            return False, f'单文件大小不能超过 {self.max_single_file / (1024*1024):.0f}MB'

        if self.used_file_count >= self.max_file_count:
            return False, f'文件数量已达上限 {self.max_file_count} 个'

        if self.used_total_size + file_size > self.max_total_size:
            return False, f'存储空间不足，剩余 {self.remaining_size / (1024*1024):.0f}MB'

        return True, ''

    def update_usage(self, file_size, increment=True):
        """
        更新使用量
        increment: True增加，False减少
        """
        if increment:
            self.used_total_size += file_size
            self.used_file_count += 1
        else:
            self.used_total_size = max(0, self.used_total_size - file_size)
            self.used_file_count = max(0, self.used_file_count - 1)
        self.save(update_fields=['used_total_size', 'used_file_count'])
