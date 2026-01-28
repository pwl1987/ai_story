"""
文件存储服务抽象层
Epic 6.2: 文件存储服务实现

提供统一的存储接口，支持：
1. 本地文件系统（开发环境）
2. AWS S3（生产环境）
3. 阿里云OSS（生产环境）
4. 腾讯云COS（生产环境）

设计模式：策略模式 + 工厂模式
"""

import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class BaseStorageBackend:
    """
    存储后端抽象基类
    遵循依赖倒置原则(DIP)：定义抽象接口
    """

    def __init__(self, config=None):
        """
        初始化存储后端
        :param config: 存储配置字典
        """
        self.config = config or {}

    def save(self, file, file_path):
        """
        保存文件
        :param file: Django File对象
        :param file_path: 文件路径
        :return: 文件URL
        """
        raise NotImplementedError

    def delete(self, file_path):
        """
        删除文件
        :param file_path: 文件路径
        """
        raise NotImplementedError

    def exists(self, file_path):
        """
        检查文件是否存在
        :param file_path: 文件路径
        :return: bool
        """
        raise NotImplementedError

    def url(self, file_path):
        """
        获取文件访问URL
        :param file_path: 文件路径
        :return: URL字符串
        """
        raise NotImplementedError

    def get_absolute_path(self, file_path):
        """
        获取文件绝对路径（如果适用）
        :param file_path: 文件路径
        :return: 绝对路径或None
        """
        raise NotImplementedError


class LocalStorageBackend(BaseStorageBackend):
    """
    本地文件系统存储后端
    适用场景：开发环境、测试环境
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.root = config.get('root', settings.STORAGE_ROOT)
        self.base_url = config.get('base_url', settings.STORAGE_URL)

        # 确保根目录存在
        os.makedirs(self.root, exist_ok=True)

        # 使用Django的FileSystemStorage
        self.storage = FileSystemStorage(
            location=self.root,
            base_url=self.base_url
        )

    def save(self, file, file_path):
        """
        保存文件到本地文件系统
        """
        return self.storage.save(file_path, file)

    def delete(self, file_path):
        """
        从本地文件系统删除文件
        """
        if self.exists(file_path):
            self.storage.delete(file_path)

    def exists(self, file_path):
        """
        检查文件是否存在
        """
        return self.storage.exists(file_path)

    def url(self, file_path):
        """
        获取文件访问URL
        """
        return self.storage.url(file_path)

    def get_absolute_path(self, file_path):
        """
        获取文件绝对路径
        """
        return self.storage.path(file_path)


class S3StorageBackend(BaseStorageBackend):
    """
    AWS S3存储后端
    适用场景：生产环境、海外部署

    配置参数:
    - bucket_name: S3存储桶名称
    - access_key: AWS访问密钥
    - secret_key: AWS秘密密钥
    - region: AWS区域（如：us-east-1）
    - endpoint_url: S3端点URL（可选，用于S3兼容服务）
    - custom_domain: 自定义域名（可选，用于CDN）
    """

    def __init__(self, config=None):
        super().__init__(config)

        # 从环境变量或配置中获取S3配置
        self.bucket_name = config.get('bucket_name') or os.getenv('AWS_S3_BUCKET_NAME')
        self.access_key = config.get('access_key') or os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = config.get('secret_key') or os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = config.get('region') or os.getenv('AWS_S3_REGION', 'us-east-1')
        self.endpoint_url = config.get('endpoint_url') or os.getenv('AWS_S3_ENDPOINT_URL')
        self.custom_domain = config.get('custom_domain') or os.getenv('AWS_S3_CUSTOM_DOMAIN')

        # 初始化S3存储
        self.storage = S3Boto3Storage(
            bucket_name=self.bucket_name,
            access_key=self.access_key,
            secret_key=self.secret_key,
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            custom_domain=self.custom_domain,
        )

    def save(self, file, file_path):
        """
        保存文件到S3
        """
        return self.storage.save(file_path, file)

    def delete(self, file_path):
        """
        从S3删除文件
        """
        if self.exists(file_path):
            self.storage.delete(file_path)

    def exists(self, file_path):
        """
        检查文件是否存在
        """
        return self.storage.exists(file_path)

    def url(self, file_path):
        """
        获取文件访问URL
        如果配置了custom_domain，返回自定义域名URL
        否则返回S3 URL
        """
        return self.storage.url(file_path)

    def get_absolute_path(self, file_path):
        """
        S3不支持绝对路径
        """
        return None


class OSSStorageBackend(BaseStorageBackend):
    """
    阿里云OSS存储后端
    适用场景：生产环境、国内部署

    配置参数:
    - bucket_name: OSS存储桶名称
    - access_key: 阿里云AccessKey ID
    - secret_key: 阿里云AccessKey Secret
    - endpoint: OSS端点（如：oss-cn-hangzhou.aliyuncs.com）
    - custom_domain: 自定义域名（可选，用于CDN）
    """

    def __init__(self, config=None):
        super().__init__(config)

        try:
            import oss2
        except ImportError:
            raise ImportError('oss2库未安装，请运行: uv pip install oss2')

        # 从环境变量或配置中获取OSS配置
        self.bucket_name = config.get('bucket_name') or os.getenv('ALIYUN_OSS_BUCKET_NAME')
        self.access_key = config.get('access_key') or os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.secret_key = config.get('secret_key') or os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        self.endpoint = config.get('endpoint') or os.getenv('ALIYUN_OSS_ENDPOINT')
        self.custom_domain = config.get('custom_domain') or os.getenv('ALIYUN_OSS_CUSTOM_DOMAIN')

        # 创建Auth实例
        self.auth = oss2.Auth(self.access_key, self.secret_key)

        # 创建Bucket实例
        self.bucket = oss2.Bucket(self.auth, f"https://{self.endpoint}", self.bucket_name)

    def save(self, file, file_path):
        """
        保存文件到OSS
        """
        # 重置文件指针
        file.seek(0)

        # 上传文件
        self.bucket.put_object(file_path, file)

        # 返回文件URL
        if self.custom_domain:
            return f"https://{self.custom_domain}/{file_path}"
        else:
            return f"https://{self.bucket_name}.{self.endpoint}/{file_path}"

    def delete(self, file_path):
        """
        从OSS删除文件
        """
        if self.exists(file_path):
            self.bucket.delete_object(file_path)

    def exists(self, file_path):
        """
        检查文件是否存在
        """
        try:
            self.bucket.head_object(file_path)
            return True
        except Exception:
            # 文件不存在或其他OSS错误
            return False

    def url(self, file_path):
        """
        获取文件访问URL
        """
        if self.custom_domain:
            return f"https://{self.custom_domain}/{file_path}"
        else:
            return f"https://{self.bucket_name}.{self.endpoint}/{file_path}"

    def get_absolute_path(self, file_path):
        """
        OSS不支持绝对路径
        """
        return None


class StorageBackendFactory:
    """
    存储后端工厂类
    设计模式：工厂模式

    根据配置自动创建合适的存储后端实例
    """

    # 存储类型映射
    BACKEND_MAP = {
        'local': LocalStorageBackend,
        's3': S3StorageBackend,
        'oss': OSSStorageBackend,
        # 未来可以扩展：
        # 'cos': COSStorageBackend,  # 腾讯云
        # 'azure': AzureStorageBackend,  # Azure
        # 'gcs': GCSStorageBackend,  # Google Cloud Storage
    }

    @classmethod
    def create_backend(cls, storage_type=None, config=None):
        """
        创建存储后端实例

        :param storage_type: 存储类型 ('local', 's3', 'oss')
                            如果为None，从环境变量DEFAULT_STORAGE_BACKEND读取
        :param config: 存储配置字典
        :return: 存储后端实例
        """
        # 从环境变量读取默认存储类型
        if storage_type is None:
            storage_type = os.getenv('DEFAULT_STORAGE_BACKEND', 'local')

        # 获取存储后端类
        backend_class = cls.BACKEND_MAP.get(storage_type)

        if backend_class is None:
            raise ValueError(f'不支持的存储类型: {storage_type}，支持的类型: {list(cls.BACKEND_MAP.keys())}')

        # 创建并返回实例
        return backend_class(config)

    @classmethod
    def get_current_backend(cls):
        """
        获取当前配置的存储后端
        便捷方法，用于快速获取默认存储后端

        :return: 存储后端实例
        """
        storage_type = getattr(settings, 'DEFAULT_STORAGE_BACKEND', 'local')
        storage_backends = getattr(settings, 'STORAGE_BACKENDS', {})
        storage_config = storage_backends.get(storage_type, {})

        return cls.create_backend(storage_type, storage_config)


def get_storage_backend():
    """
    获取存储后端实例（便捷函数）

    使用示例:
    >>> storage = get_storage_backend()
    >>> url = storage.save(file, 'path/to/file.jpg')
    >>> storage.delete('path/to/file.jpg')

    :return: 存储后端实例
    """
    return StorageBackendFactory.get_current_backend()
