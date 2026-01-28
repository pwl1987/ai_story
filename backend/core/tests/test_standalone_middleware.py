"""
单元测试: APIResponseTimeMiddlewareStandalone
测试独立版本API响应时间监控中间件
"""

import time
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware.api_response_time import (
    SLOW_REQUEST_THRESHOLD_MS,
    APIResponseTimeMiddlewareStandalone,
)


class TestStandaloneMiddleware:
    """
    测试APIResponseTimeMiddlewareStandalone独立版本
    提高Story 2.5的测试覆盖率
    """

    def test_middleware_initialization(self):
        """测试中间件初始化"""
        get_response = Mock()
        middleware = APIResponseTimeMiddlewareStandalone(get_response)
        assert middleware.get_response == get_response
        # Epic 2优化: 阈值从settings读取，检查模块级常量
        assert SLOW_REQUEST_THRESHOLD_MS == 500

    def test_adds_response_time_header(self):
        """测试添加响应时间到响应头"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)
        response = middleware(request)

        # 验证响应头包含响应时间
        assert 'X-Response-Time-ms' in response
        response_time_str = response['X-Response-Time-ms']
        assert response_time_str.endswith('ms')
        response_time = float(response_time_str.replace('ms', ''))
        assert response_time >= 0

    @patch('core.middleware.api_response_time.logger')
    def test_logs_response_time(self, mock_logger):
        """测试记录响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)
        middleware(request)

        # 验证日志被调用
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args

        # 验证日志消息包含响应时间
        assert 'ms' in call_args[0][1]
        assert '/api/v1/test/' in call_args[0][1]

    @patch('core.middleware.api_response_time.logger')
    def test_slow_request_warning(self, mock_logger):
        """测试慢请求标记为WARNING"""
        factory = RequestFactory()
        request = factory.get('/api/v1/slow/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)

        # 模拟慢请求（>500ms）
        current = time.time()
        with patch('time.time', side_effect=[current, current + 0.6, current + 0.6]):
            middleware(request)

        # 验证日志级别为WARNING
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == 30  # logging.WARNING

        # 验证慢请求标记
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['is_slow_request'] is True

    @patch('core.middleware.api_response_time.logger')
    def test_normal_request_info(self, mock_logger):
        """测试正常请求标记为INFO"""
        factory = RequestFactory()
        request = factory.get('/api/v1/fast/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)

        # 模拟正常请求（<500ms）
        current = time.time()
        with patch('time.time', side_effect=[current, current + 0.1, current + 0.1]):
            middleware(request)

        # 验证日志级别为INFO
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == 20  # logging.INFO

        # 验证正常请求标记
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['is_slow_request'] is False

    @patch('core.middleware.api_response_time.logger')
    def test_includes_request_context(self, mock_logger):
        """测试日志包含请求上下文"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')
        request.request_id = 'test-request-123'

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)
        middleware(request)

        # 验证日志上下文
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})

        assert 'request_id' in extra_fields
        assert 'method' in extra_fields
        assert 'path' in extra_fields
        assert 'response_time_ms' in extra_fields
        assert 'is_slow_request' in extra_fields

    def test_response_time_calculation(self):
        """测试响应时间计算准确性"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)

        # 模拟已知延迟
        current = time.time()
        delay_seconds = 0.3
        with patch('time.time', side_effect=[current, current + delay_seconds, current + delay_seconds]):
            response = middleware(request)

        # 验证响应时间接近预期
        response_time_header = response['X-Response-Time-ms']
        response_time_value = float(response_time_header.replace('ms', ''))

        expected_ms = delay_seconds * 1000
        assert abs(response_time_value - expected_ms) < 50

    @patch('core.middleware.api_response_time.logger')
    def test_threshold_boundary(self, mock_logger):
        """测试慢请求阈值边界（500ms）"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddlewareStandalone(get_response)

        # 测试正好500ms的请求
        current = time.time()
        with patch('time.time', side_effect=[current, current + 0.5, current + 0.5]):
            middleware(request)

        # 验证慢请求标记
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['response_time_ms'] >= 500
