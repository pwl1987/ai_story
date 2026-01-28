"""
API错误日志中间件
自动捕获和记录API错误，返回友好错误消息

功能:
- 自动捕获API异常（数据库错误、Redis错误、验证错误等）
- 记录结构化日志（请求路径、方法、参数、错误堆栈）
- 不向用户暴露敏感信息（堆栈跟踪、密钥）
- 返回友好的错误消息和HTTP状态码
- 记录请求ID（用于日志关联）

遵循SOLID原则:
- 单一职责：仅负责API错误处理和日志记录
- 开闭原则：可扩展新的异常类型处理
- 依赖倒置：依赖Django抽象接口
"""

import logging
import uuid
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger('apps.api')


class APIErrorLoggingMiddleware:
    """
    API错误日志中间件

    自动捕获Django REST Framework API错误，
    记录结构化日志并返回友好的错误响应
    """

    # 敏感信息字段（不记录到日志）
    SENSITIVE_FIELDS = {
        'password', 'api_key', 'apikey', 'secret',
        'token', 'authorization', 'csrf_token'
    }

    def __init__(self, get_response):
        """
        初始化中间件

        Args:
            get_response: 下一个中间件或视图的响应函数
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        处理请求

        Args:
            request: HTTP请求对象

        Returns:
            HttpResponse: HTTP响应对象
        """
        # 为请求生成唯一ID（用于日志关联）
        request.request_id = getattr(request, 'request_id', str(uuid.uuid4()))

        try:
            # 调用下一个中间件或视图
            response = self.get_response(request)
            return response
        except Exception as exc:
            # 捕获异常并处理
            return self._handle_exception(request, exc)

    def _handle_exception(self, request: HttpRequest, exc: Exception) -> HttpResponse:
        """
        处理异常

        Args:
            request: HTTP请求对象
            exc: 异常对象

        Returns:
            HttpResponse: 错误响应
        """
        # 记录错误日志
        self._log_error(request, exc)

        # 确定HTTP状态码
        status_code = self._get_status_code_for_exception(exc)

        # 构建友好的错误响应
        error_response = self._build_error_response(request, exc, status_code)

        return JsonResponse(error_response, status=status_code)

    def _log_error(self, request: HttpRequest, exc: Exception) -> None:
        """
        记录错误日志（结构化）

        Args:
            request: HTTP请求对象
            exc: 异常对象
        """
        # 构建日志上下文
        context = {
            'request_id': getattr(request, 'request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'user_id': self._get_user_id(request),
            'error_type': type(exc).__name__,
            'error_message': str(exc),
            'status_code': self._get_status_code_for_exception(exc),
        }

        # 添加请求参数（过滤敏感信息）
        request_data = self._extract_request_data(request)
        if request_data:
            context['request_data'] = request_data

        # 记录错误日志
        logger.error(
            f"API Error: {type(exc).__name__}",
            extra={'extra_fields': context},
            exc_info=True  # 包含堆栈跟踪
        )

    def _get_status_code_for_exception(self, exc: Exception) -> int:
        """
        根据异常类型确定HTTP状态码

        Args:
            exc: 异常对象

        Returns:
            int: HTTP状态码
        """
        # 验证错误
        if isinstance(exc, ValidationError):
            return 400

        # 权限错误
        if isinstance(exc, PermissionDenied):
            return 403

        # 数据库错误
        if isinstance(exc, DatabaseError):
            return 500

        # 默认：内部服务器错误
        return 500

    def _build_error_response(self, request: HttpRequest,
                            exc: Exception, status_code: int) -> Dict[str, Any]:
        """
        构建友好的错误响应

        Args:
            request: HTTP请求对象
            exc: 异常对象
            status_code: HTTP状态码

        Returns:
            Dict[str, Any]: 错误响应字典
        """
        # 友好的错误消息
        friendly_message = self._get_friendly_message(exc, status_code)

        error_response = {
            'error': friendly_message,
            'status_code': status_code,
            'request_id': getattr(request, 'request_id', 'unknown'),
        }

        # 开发环境下提供更多调试信息（但不暴露敏感信息）
        if settings.DEBUG:
            error_response['detail'] = {
                'error_type': type(exc).__name__,
                'path': request.path,
                'method': request.method,
            }

        return error_response

    def _get_friendly_message(self, exc: Exception, status_code: int) -> str:
        """
        获取友好的错误消息

        Args:
            exc: 异常对象
            status_code: HTTP状态码

        Returns:
            str: 友好的错误消息
        """
        # 验证错误
        if isinstance(exc, ValidationError):
            return '请求参数验证失败，请检查输入数据'

        # 权限错误
        if isinstance(exc, PermissionDenied):
            return '您没有权限执行此操作'

        # 数据库错误
        if isinstance(exc, DatabaseError):
            # 开发环境显示详细信息
            if settings.DEBUG:
                return f'数据库错误: {exc!s}'
            # 生产环境隐藏细节
            return '服务暂时不可用，请稍后重试'

        # 其他错误
        if status_code == 500:
            if settings.DEBUG:
                return f'服务器错误: {exc!s}'
            return '服务器内部错误，请联系管理员'

        return str(exc)

    def _extract_request_data(self, request: HttpRequest) -> Optional[Dict[str, Any]]:
        """
        提取请求数据（过滤敏感信息）

        Args:
            request: HTTP请求对象

        Returns:
            Optional[Dict[str, Any]]: 过滤后的请求数据
        """
        if request.method in ('POST', 'PUT', 'PATCH'):
            # 对于POST/PUT/PATCH请求，提取请求体
            try:
                content_type = request.content_type
                if content_type == 'application/json':
                    import json
                    data = json.loads(request.body)
                    return self._filter_sensitive_data(data)
            except (json.JSONDecodeError, TypeError):
                pass

        elif request.method == 'GET':
            # 对于GET请求，提取查询参数
            return dict(request.GET)

        return None

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤敏感数据

        Args:
            data: 原始数据字典

        Returns:
            Dict[str, Any]: 过滤后的数据
        """
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            # 检查是否是敏感字段
            if key.lower() in self.SENSITIVE_FIELDS:
                filtered[key] = '***FILTERED***'
            elif isinstance(value, dict):
                # 递归过滤嵌套字典
                filtered[key] = self._filter_sensitive_data(value)
            elif isinstance(value, list):
                # 过滤列表中的字典项
                filtered[key] = [
                    self._filter_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered

    def _get_user_id(self, request: HttpRequest) -> Optional[int]:
        """
        获取用户ID

        Args:
            request: HTTP请求对象

        Returns:
            Optional[int]: 用户ID
        """
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                return request.user.id
        except Exception:
            pass
        return None
