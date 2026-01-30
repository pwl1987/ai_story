"""
Django基础配置
遵循SOLID原则,使用分层设置
"""

import os
from datetime import timedelta
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 安全配置
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-key-change-in-production")
DEBUG = True
ALLOWED_HOSTS = []

# 应用定义
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方应用
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_celery_beat",
    "channels",
    # 本地应用
    "apps.projects",
    "apps.prompts",
    "apps.models",
    "apps.content",
    "apps.users",
    "apps.mock_api",
    "apps.core",
    "apps.files",  # Epic 6: 文件管理与预览
    "health",  # 健康检查端点 (Story 2.2)
    # API文档 (Epic 7.1: OpenAPI文档自动生成)
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.users.middleware.MustChangePasswordMiddleware",  # Epic 8 Story 8.4: 强制修改密码
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.api_response_time.APIResponseTimeMiddleware",  # API错误日志 + 响应时间监控 (Story 2.3 + 2.5)
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# 数据库配置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "ATOMIC_REQUESTS": True,  # 启用原子性请求（Django 5.2需要显式配置）
    }
}

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 国际化
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# 媒体文件
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Storage文件 (用于存储生成的图片、视频等)
STORAGE_URL = "storage/"
STORAGE_ROOT = BASE_DIR.parent / "storage"  # 项目根目录的storage文件夹

# Epic 6.2: 文件存储服务配置
# 存储后端类型: 'local', 's3', 'oss'
DEFAULT_STORAGE_BACKEND = os.getenv("DEFAULT_STORAGE_BACKEND", "local")

# 存储后端配置
STORAGE_BACKENDS = {
    # 本地存储（开发环境）
    "local": {
        "root": STORAGE_ROOT,
        "base_url": STORAGE_URL,
    },
    # AWS S3（生产环境）
    "s3": {
        "bucket_name": os.getenv("AWS_S3_BUCKET_NAME"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region": os.getenv("AWS_S3_REGION", "us-east-1"),
        "endpoint_url": os.getenv("AWS_S3_ENDPOINT_URL"),  # 可选，用于S3兼容服务
        "custom_domain": os.getenv("AWS_S3_CUSTOM_DOMAIN"),  # 可选，用于CDN
    },
    # 阿里云OSS（生产环境）
    "oss": {
        "bucket_name": os.getenv("ALIYUN_OSS_BUCKET_NAME"),
        "access_key": os.getenv("ALIYUN_ACCESS_KEY_ID"),
        "secret_key": os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
        "endpoint": os.getenv("ALIYUN_OSS_ENDPOINT"),  # 如：oss-cn-hangzhou.aliyuncs.com
        "custom_domain": os.getenv("ALIYUN_OSS_CUSTOM_DOMAIN"),  # 可选，用于CDN
    },
}


# 默认主键字段
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework配置
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Epic 7.1: OpenAPI文档自动生成
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Redis配置 - 使用不同的数据库避免冲突
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Celery配置
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"  # 数据库0: Celery任务队列
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"  # 数据库0: Celery任务队列
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"  # 数据库1: Celery结果存储
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Redis Pub/Sub配置 (用于实时流式推送)
REDIS_PUBSUB_URL = os.getenv(
    "REDIS_PUBSUB_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
)  # 数据库2: Pub/Sub专用

# Channels配置 (WebSocket)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://{REDIS_HOST}:{REDIS_PORT}/3"],  # 数据库3: Channels专用
        },
    },
}

# CORS配置
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:3000"]

# JWT配置
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
}

# Epic 2: 系统可观测性 - 监控阈值配置
# 将阈值提取到配置文件，便于运维调整
# 可以通过环境变量覆盖这些默认值
SLOW_REQUEST_THRESHOLD_MS = int(
    os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500")
)  # API慢请求阈值(毫秒)
SLOW_TASK_THRESHOLD_S = int(os.getenv("SLOW_TASK_THRESHOLD_S", "60"))  # Celery慢任务阈值(秒)

# 缓存配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/4",  # 数据库4: Django缓存
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# 日志目录配置
LOG_DIR = BASE_DIR / "logs"
# 确保日志目录存在（如果可写）
try:
    LOG_DIR.mkdir(exist_ok=True)
except (OSError, PermissionError):
    # 如果无法创建目录，仅使用console日志
    LOG_DIR = None

# 日志配置
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.logging.json_formatter.JSONFormatter",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "filters": {
        "sensitive_data": {
            "()": "core.logging.json_formatter.SensitiveDataFilter",
        },
        "request_context": {
            "()": "core.logging.json_formatter.RequestContextFilter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["sensitive_data", "request_context"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"] + (["file"] if LOG_DIR else []),
            "level": "DEBUG",
            "propagate": False,
        },
        "core": {
            "handlers": ["console"] + (["file"] if LOG_DIR else []),
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# 如果日志目录可用，添加file handler
if LOG_DIR:
    LOGGING["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(LOG_DIR / "django.log"),
        "maxBytes": 1024 * 1024 * 10,  # 10MB
        "backupCount": 5,
        "formatter": "json",
        "filters": ["sensitive_data", "request_context"],
    }


# =============================================================================
# Epic 7.1: OpenAPI文档自动生成配置
# =============================================================================

# drf-spectacular配置
REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"

# API文档配置
SPECTACULAR_SETTINGS = {
    "TITLE": "AI Story Generation API",
    "DESCRIPTION": """
AI Story生成系统 - 基于Django + Vue的AI驱动的故事脚本到视频的自动化生成平台。

## 核心工作流
文案改写 → 分镜生成 → 文生图 → 运镜生成 → 图生视频

## 认证方式
- JWT Token Authentication: 在请求头中添加 `Authorization: Bearer <token>`
- Session Authentication: 基于Django的会话认证

## 核心API端点
- **项目管理**: `/api/v1/projects/` - 项目CRUD、启动工作流、进度查询
- **内容管理**: `/api/v1/content/` - 分镜、图片、视频内容管理
- **Prompt管理**: `/api/v1/prompts/` - 提示词模板管理
- **模型管理**: `/api/v1/models/` - AI模型配置
- **健康检查**: `/api/v1/health/` - 系统健康状态

## 实时通信
- WebSocket: `ws://localhost:8000/ws/projects/{project_id}/` - 实时进度推送

## 版本
当前版本: v1.0.0
""".strip(),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {
            "name": "projects",
            "description": "项目管理接口 - 创建、查询、更新、删除项目，启动工作流",
        },
        {"name": "content", "description": "内容管理接口 - 分镜、图片、视频内容"},
        {"name": "prompts", "description": "Prompt模板管理 - 文案改写、分镜生成等提示词模板"},
        {"name": "models", "description": "AI模型管理 - LLM、Text2Image、Image2Video模型配置"},
        {"name": "health", "description": "健康检查 - 系统组件状态监控"},
    ],
    "OPERATION_ID_PREFIX": "ai_story",
    "SCHEMA_PATH_PREFIX_INSERT": "api/v1",
}
