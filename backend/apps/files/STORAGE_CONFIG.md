# 文件存储服务配置指南

> **Epic 6.2: 文件存储服务实现**
> **更新时间**: 2026-01-28

---

## 概述

文件存储服务提供统一的存储接口，支持多种存储后端：
- **本地文件系统** (开发环境)
- **AWS S3** (生产环境 - 海外部署)
- **阿里云OSS** (生产环境 - 国内部署)

---

## 存储后端类型

### 1. 本地存储 (Local)

**适用场景**: 开发环境、测试环境

**配置**:
```python
# .env 或环境变量
DEFAULT_STORAGE_BACKEND=local

# config/settings/base.py
STORAGE_ROOT = BASE_DIR.parent / 'storage'
STORAGE_URL = 'storage/'
```

**特点**:
- ✅ 无需额外配置
- ✅ 开箱即用
- ❌ 不适合生产环境
- ❌ 无法水平扩展

---

### 2. AWS S3

**适用场景**: 生产环境、海外部署

**配置**:
```bash
# .env 文件
DEFAULT_STORAGE_BACKEND=s3
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_REGION=us-east-1
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com  # 可选
AWS_S3_CUSTOM_DOMAIN=cdn.yourdomain.com  # 可选，用于CDN
```

**特点**:
- ✅ 高可用性
- ✅ 无限扩展
- ✅ CDN集成
- ✅ 全球部署

**创建S3存储桶**:
```bash
# 使用AWS CLI
aws s3 mb s3://your-bucket-name --region us-east-1

# 配置CORS
aws s3api put-bucket-cors --bucket your-bucket-name --cors-configuration file://cors.json
```

**cors.json**:
```json
{
    "CORSRules": [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "HEAD"],
            "AllowedOrigins": ["*"],
            "ExposeHeaders": ["ETag"]
        }
    ]
}
```

---

### 3. 阿里云OSS

**适用场景**: 生产环境、国内部署

**配置**:
```bash
# .env 文件
DEFAULT_STORAGE_BACKEND=oss
ALIYUN_OSS_BUCKET_NAME=your-bucket-name
ALIYUN_ACCESS_KEY_ID=your-access-key
ALIYUN_ACCESS_KEY_SECRET=your-secret-key
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_CUSTOM_DOMAIN=cdn.yourdomain.com  # 可选，用于CDN
```

**区域列表**:
- 华东1（杭州）: `oss-cn-hangzhou.aliyuncs.com`
- 华东2（上海）: `oss-cn-shanghai.aliyuncs.com`
- 华北2（北京）: `oss-cn-beijing.aliyuncs.com`
- 华南1（深圳）: `oss-cn-shenzhen.aliyuncs.com`

**特点**:
- ✅ 国内访问速度快
- ✅ 成本较低
- ✅ CDN集成
- ✅ 防护能力（DDoS）

**创建OSS存储桶**:
```python
import oss2

# 创建Bucket
auth = oss2.Auth('your-access-key', 'your-secret-key')
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'your-bucket-name')
bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ)

# 配置CORS（通过阿里云控制台）
```

---

## 使用示例

### 代码中使用存储后端

```python
from apps.files.storage_backends import get_storage_backend
from django.core.files.uploadedfile import SimpleUploadedFile

# 获取当前配置的存储后端
storage = get_storage_backend()

# 保存文件
uploaded_file = SimpleUploadedFile('test.jpg', file_content)
file_url = storage.save(uploaded_file, 'images/test.jpg')

# 检查文件是否存在
exists = storage.exists('images/test.jpg')

# 获取文件URL
url = storage.url('images/test.jpg')

# 删除文件
storage.delete('images/test.jpg')

# 获取文件绝对路径（仅本地存储）
absolute_path = storage.get_absolute_path('images/test.jpg')
```

### 在模型中使用

```python
from apps.files.storage_backends import get_storage_backend

class UploadedFile(models.Model):
    file = models.FileField(upload_to='...', storage=get_storage_backend())
```

---

## 环境变量配置模板

创建 `.env` 文件：

```bash
# ========== 存储后端配置 ==========

# 存储类型: local, s3, oss
DEFAULT_STORAGE_BACKEND=local

# ========== AWS S3 配置 ==========
# (仅在 DEFAULT_STORAGE_BACKEND=s3 时需要)

AWS_S3_BUCKET_NAME=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_REGION=us-east-1
AWS_S3_ENDPOINT_URL=
AWS_S3_CUSTOM_DOMAIN=

# ========== 阿里云 OSS 配置 ==========
# (仅在 DEFAULT_STORAGE_BACKEND=oss 时需要)

ALIYUN_OSS_BUCKET_NAME=
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_CUSTOM_DOMAIN=

# ========== 本地存储配置 ==========
# (仅在 DEFAULT_STORAGE_BACKEND=local 时需要)

STORAGE_ROOT=/path/to/storage
STORAGE_URL=storage/
```

---

## 存储后端切换

### 从本地切换到S3

1. **更新环境变量**:
```bash
DEFAULT_STORAGE_BACKEND=s3
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

2. **重启应用**:
```bash
# Django应用
./run_asgi.sh

# Celery Worker
uv run celery -A config worker -Q llm,image,video -l info
```

3. **迁移现有文件** (可选):
```python
from apps.files.models import UploadedFile
from apps.files.storage_backends import LocalStorageBackend, S3StorageBackend

local_storage = LocalStorageBackend()
s3_storage = S3StorageBackend()

for uploaded_file in UploadedFile.objects.all():
    if local_storage.exists(uploaded_file.file.name):
        # 从本地读取文件
        with open(local_storage.get_absolute_path(uploaded_file.file.name), 'rb') as f:
            # 上传到S3
            s3_storage.save(f, uploaded_file.file.name)
```

### 从S3切换到OSS

1. **更新环境变量**:
```bash
DEFAULT_STORAGE_BACKEND=oss
ALIYUN_OSS_BUCKET_NAME=your-bucket-name
ALIYUN_ACCESS_KEY_ID=your-access-key
ALIYUN_ACCESS_KEY_SECRET=your-secret-key
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

2. **重启应用**

3. **迁移文件** (使用阿里云数据迁移服务)

---

## 安全建议

### 1. 访问控制

**本地存储**:
```python
# 通过Nginx配置访问控制
location /storage/ {
    internal;  # 仅内部访问
}
```

**S3存储**:
```python
# 使用Bucket Policy限制访问
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "arn:aws:iam::account:user/app"},
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

**OSS存储**:
```python
# 设置Bucket ACL
bucket.put_bucket_acl(oss2.BUCKET_ACL_PRIVATE)
```

### 2. 加密

**S3服务端加密**:
```python
# 在config/settings/base.py中配置
S3_STORAGE_CONFIG = {
    'encryption': 'AES256',
}
```

**OSS服务端加密**:
```python
# 上传时指定加密
bucket.put_object('file.txt', content, headers={
    'x-oss-server-side-encryption': 'AES256'
})
```

### 3. 签名URL

对于敏感文件，使用签名URL而不是公开URL：

```python
from apps.files.storage_backends import get_storage_backend
from botocore.exceptions import ClientError

storage = get_storage_backend()

# 生成临时签名URL（1小时有效）
if isinstance(storage, S3StorageBackend):
    from botocore.client import Config
    import boto3

    s3_client = boto3.client('s3')
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'your-bucket', 'Key': 'file.txt'},
        ExpiresIn=3600
    )
```

---

## 性能优化

### 1. CDN集成

**S3 + CloudFront**:
```bash
AWS_S3_CUSTOM_DOMAIN=cdn.yourdomain.com
```

**OSS + 阿里云CDN**:
```bash
ALIYUN_OSS_CUSTOM_DOMAIN=cdn.yourdomain.com
```

### 2. 分片上传

对于大文件（>100MB），使用分片上传：

```python
# S3分片上传
from boto3.s3.transfer import TransferConfig

config = TransferConfig(
    multipart_threshold=100 * 1024 * 1024,  # 100MB
    max_concurrency=10,
    multipart_chunksize=10 * 1024 * 1024,  # 10MB
)

s3_client.upload_file(
    'large_file.txt',
    'your-bucket',
    'large_file.txt',
    Config=config
)
```

### 3. 缓存策略

```python
# 在Django中设置缓存头
response['Cache-Control'] = 'public, max-age=31536000'  # 1年
```

---

## 故障排查

### 问题1: S3连接失败

**错误**: `ConnectionError`

**解决方案**:
1. 检查网络连接
2. 验证AWS凭证
3. 确认S3端点URL正确

```bash
# 测试S3连接
aws s3 ls s3://your-bucket-name
```

### 问题2: OSS认证失败

**错误**: `AccessDenied`

**解决方案**:
1. 验证AccessKey ID和Secret
2. 检查Bucket ACL
3. 确认Endpoint正确

```python
import oss2

# 测试OSS连接
auth = oss2.Auth('your-key', 'your-secret')
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'your-bucket')
bucket.get_bucket_info()
```

### 问题3: 文件上传后无法访问

**错误**: `404 Not Found`

**解决方案**:
1. 检查文件路径
2. 验证Bucket/文件夹权限
3. 确认CORS配置

---

## 测试

运行存储后端测试：

```bash
cd backend
uv run pytest apps/files/tests/test_storage_backends.py -v
```

---

## 下一步

- 集成到UploadedFile模型
- 添加文件预览功能
- 实现分片上传

---

*Epic 6.2: 文件存储服务实现*
