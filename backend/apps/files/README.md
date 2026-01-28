# 文件管理API使用文档

> **Epic 6: 文件管理与预览**
> **Story 6.1: 文件上传API**
> **更新时间**: 2026-01-28

---

## 功能概述

文件管理API提供完整的文件上传、下载、预览、删除功能，支持：
- 图片上传（jpg, png, webp等）
- 视频上传（mp4, mov, avi等）
- 文档上传（pdf, txt, md等）
- 音频上传（mp3, wav, flac等）

---

## API端点

### 1. 上传文件

**端点**: `POST /api/v1/files/upload/`

**认证**: 需要JWT Token

**请求** (multipart/form-data):
```bash
curl -X POST http://localhost:8000/api/v1/files/upload/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@example.jpg" \
  -F "file_type=image" \
  -F "project=<project_id>"
```

**响应** (201 Created):
```json
{
    "message": "文件上传成功",
    "file": {
        "id": "uuid",
        "original_filename": "example.jpg",
        "file_type": "image",
        "file_size": 1234567,
        "file_size_human": "1.18 MB",
        "mime_type": "image/jpeg",
        "file_url": "/api/v1/files/uuid/download/",
        "uploaded_at": "2026-01-28T12:00:00Z"
    }
}
```

**文件限制**:
- 单文件最大: 100MB
- 支持的图片格式: jpg, jpeg, png, gif, bmp, webp, svg
- 支持的视频格式: mp4, avi, mov, wmv, flv, webm, mkv
- 支持的文档格式: pdf, doc, docx, txt, md, html, json, csv
- 支持的音频格式: mp3, wav, flac, aac, ogg

---

### 2. 获取文件列表

**端点**: `GET /api/v1/files/`

**认证**: 需要JWT Token

**查询参数**:
- `file_type`: 文件类型筛选 (image, video, document, audio)
- `is_active`: 是否有效 (true, false)

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/?file_type=image \
  -H "Authorization: Bearer <token>"
```

**响应** (200 OK):
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "username": "testuser",
            "original_filename": "example.jpg",
            "file_type": "image",
            "file_size": 1234567,
            "file_size_human": "1.18 MB",
            "mime_type": "image/jpeg",
            "file_url": "/api/v1/files/uuid/download/",
            "uploaded_at": "2026-01-28T12:00:00Z",
            "is_active": true
        }
    ]
}
```

---

### 3. 获取文件详情

**端点**: `GET /api/v1/files/{id}/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/{id}/ \
  -H "Authorization: Bearer <token>"
```

**响应**: 同上传文件的file字段

---

### 4. 下载文件

**端点**: `GET /api/v1/files/{id}/download/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/{id}/download/ \
  -H "Authorization: Bearer <token>" \
  -O -J
```

**响应**: 文件二进制流

---

### 5. 预览文件

**端点**: `GET /api/v1/files/{id}/preview/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/{id}/preview/ \
  -H "Authorization: Bearer <token>"
```

**响应**: 文件二进制流（inline模式，浏览器直接显示）

---

### 6. 删除文件

**端点**: `DELETE /api/v1/files/{id}/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X DELETE http://localhost:8000/api/v1/files/{id}/ \
  -H "Authorization: Bearer <token>"
```

**响应** (200 OK):
```json
{
    "message": "文件已删除"
}
```

**注意**: 删除文件会自动更新用户配额

---

### 7. 获取用户配额

**端点**: `GET /api/v1/files/quota/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/quota/ \
  -H "Authorization: Bearer <token>"
```

**响应** (200 OK):
```json
{
    "max_total_size": 5368709120,
    "max_single_file": 104857600,
    "max_file_count": 1000,
    "used_total_size": 52428800,
    "used_file_count": 10,
    "usage_percentage": 1.0,
    "remaining_size": 5316280320,
    "remaining_count": 990
}
```

**默认配额**:
- 总容量: 5GB
- 单文件最大: 100MB
- 最大文件数: 1000个

---

### 8. 获取文件统计

**端点**: `GET /api/v1/files/statistics/`

**认证**: 需要JWT Token

**请求**:
```bash
curl -X GET http://localhost:8000/api/v1/files/statistics/ \
  -H "Authorization: Bearer <token>"
```

**响应** (200 OK):
```json
{
    "total_files": 100,
    "total_size": 1073741824,
    "by_type": {
        "image": 50,
        "video": 30,
        "document": 20
    }
}
```

---

## 文件去重

系统自动根据文件内容（SHA256哈希）进行去重：

- 上传相同文件时，返回已存在的文件记录
- 避免重复占用存储空间
- 保留原始上传时间

---

## 错误处理

### 文件过大
```json
{
    "error": "文件大小不能超过 100MB"
}
```

### 不支持的文件类型
```json
{
    "error": "不支持的文件格式: .exe"
}
```

### 配额不足
```json
{
    "error": "存储空间不足，剩余 50MB"
}
```

---

## 配置说明

### 存储路径
文件存储在: `storage/{file_type}/{YYYY-MM-DD}/{uuid}{ext}`

例如: `storage/image/2026-01-28/abc123-def456.jpg`

### 配额管理
每个用户有独立的存储配额：
- 上传文件时自动检查配额
- 删除文件时自动释放配额
- 可通过Django Admin调整用户配额

---

## 测试

运行测试:
```bash
cd backend
uv run pytest apps/files/tests/test_file_upload.py -v
```

测试覆盖率: 76%

---

## 下一步

- Story 6.2: 文件存储服务（OSS/S3集成）
- Story 6.3: 文件预览功能（前端集成）
- Story 6.4: 文件管理和删除（批量操作）

---

*Epic 6: 文件管理与预览*
*Story 6.1: 文件上传API*
