#!/usr/bin/env python
"""
测试JSON日志输出

验证结构化日志配置正确
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import logging
import json

# 获取logger
logger = logging.getLogger(__name__)

print("=== 测试JSON日志输出 ===\n")

# 测试不同级别的日志
logger.info("测试信息日志", extra={"custom_field": "custom_value"})
logger.warning("测试警告日志", extra={"warning_code": "W001"})
logger.error("测试错误日志", extra={"error_code": 500, "user_id": 12345})

# 测试带异常的日志
try:
    1 / 0
except Exception as e:
    logger.error("测试异常日志", exc_info=True, extra={"exception_type": type(e).__name__})

print("\n=== 日志输出测试完成 ===")
print("如果上面的输出是JSON格式，则配置成功！")
