"""
JSON日志格式化器
基于python-json-logger,提供结构化日志输出
支持敏感信息脱敏、请求ID跟踪、用户ID上下文
"""

import logging
import re
from typing import Any, Dict, List

from pythonjsonlogger import json


class SensitiveDataFilter(logging.Filter):
    """
    敏感信息过滤器
    符合SOLID原则: 单一职责,仅负责敏感信息脱敏
    """

    # 敏感字段模式列表
    SENSITIVE_PATTERNS: List[re.Pattern] = [
        re.compile(r'("password"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r'("api_key"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r'("apikey"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r'("secret"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r'("token"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r'("authorization"\s*:\s*")([^"]+)"', re.IGNORECASE),
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录,脱敏敏感信息

        Args:
            record: 日志记录对象

        Returns:
            bool: 始终返回True(不阻止日志记录)
        """
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._sanitize(record.msg)

        if hasattr(record, "args") and record.args:
            record.args = tuple(
                self._sanitize(str(arg)) if isinstance(arg, str) else arg for arg in record.args
            )

        return True

    def _sanitize(self, text: str) -> str:
        """
        脱敏文本中的敏感信息

        Args:
            text: 原始文本

        Returns:
            str: 脱敏后的文本
        """
        for pattern in self.SENSITIVE_PATTERNS:
            text = pattern.sub(r"\1***", text)
        return text


class JSONFormatter(json.JsonFormatter):
    """
    自定义JSON日志格式化器
    符合SOLID原则: 单一职责,仅负责格式化

    功能:
    - 结构化JSON输出
    - 自动添加timestamp、level、logger、message
    - 支持请求ID跟踪(request_id)
    - 支持用户ID上下文(user_id)
    - 支持额外字段(extra_fields)
    - 自动脱敏敏感信息
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """
        初始化JSON格式化器

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        # 设置默认格式字符串,包含所有基础字段
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(process)d %(thread)d"
        kwargs.setdefault("fmt", fmt)
        super().__init__(*args, **kwargs)

    def add_fields(
        self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
    ) -> None:
        """
        添加自定义字段到日志记录

        Args:
            log_record: 日志记录字典
            record: 原始日志记录对象
            message_dict: 消息字典
        """
        # 调用父类方法添加基础字段
        super().add_fields(log_record, record, message_dict)

        # 重命名字段以符合我们的命名规范
        if "asctime" in log_record:
            log_record["timestamp"] = log_record.pop("asctime")
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname")
        if "name" in log_record:
            log_record["logger"] = log_record.pop("name")
        if "process" in log_record:
            log_record["process_id"] = log_record.pop("process")
        if "thread" in log_record:
            log_record["thread_id"] = log_record.pop("thread")

        # 添加额外的标准字段
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        log_record["thread_name"] = record.threadName

        # 添加异常信息(如果有)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            if record.exc_info and record.exc_info[0]:
                log_record["exception_type"] = record.exc_info[0].__name__

        # 添加请求ID(如果有)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # 添加用户ID(如果有)
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id

        # 添加额外字段(如果有)
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


class RequestContextFilter(logging.Filter):
    """
    请求上下文过滤器
    从Django request对象提取请求ID和用户ID

    符合SOLID原则: 单一职责,仅负责请求上下文提取
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        从请求对象提取上下文信息

        Args:
            record: 日志记录对象

        Returns:
            bool: 始终返回True(不阻止日志记录)
        """
        # 尝试从线程本地存储获取请求对象
        try:
            # 获取当前请求(如果存在)
            request = getattr(record, "request", None)
            if request is None:
                # 尝试从线程本地存储获取
                import threading

                local_storage = getattr(threading.current_thread(), "request", None)
                if local_storage:
                    request = local_storage

            if request:
                # 添加请求ID
                request_id = getattr(request, "request_id", None)
                if request_id:
                    record.request_id = request_id
                else:
                    # 生成UUID作为请求ID
                    import uuid

                    record.request_id = str(uuid.uuid4())

                # 添加用户ID
                user = getattr(request, "user", None)
                if user and hasattr(user, "id"):
                    record.user_id = user.id

        except Exception:
            # 如果获取失败,不影响日志记录
            pass

        return True
