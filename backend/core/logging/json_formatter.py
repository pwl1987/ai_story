"""
JSON日志格式化器
基于python-json-logger,提供结构化日志输出
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    自定义JSON日志格式化器
    符合SOLID原则: 单一职责,仅负责格式化
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        将日志记录格式化为JSON字符串

        Args:
            record: 日志记录对象

        Returns:
            str: JSON格式的日志字符串
        """
        # 基础日志信息
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息(如果有)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段(如果有)
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)
