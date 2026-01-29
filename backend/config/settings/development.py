"""
开发环境配置
"""

from .base import *

CELERY_ALWAYS_EAGER = True
CELERY_TASK_ALWAYS_EAGER = True

DEBUG = True
ALLOWED_HOSTS = ["*"]

# CORS配置 - 开发环境允许所有源
CORS_ALLOW_ALL_ORIGINS = True

# 数据库 - 开发环境使用SQLite
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# 日志配置 - 开发环境使用JSON格式
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.logging.json_formatter.JSONFormatter",
        },
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",  # 使用JSON格式化器
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
JIANYING_DRAFT_FOLDER = r"D:\JianyingPro Drafts"
