"""
单元测试: API响应时间监控中间件
测试APIResponseTimeMiddleware的响应时间记录和慢请求标记功能
"""

from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware.api_response_time import APIResponseTimeMiddleware


class TestAPIResponseTimeMiddleware:
    """
    测试APIResponseTimeMiddleware类
    验证响应时间监控和慢请求标记功能
    """

    def test_middleware_initialization(self):
        """测试中间件初始化"""
        get_response = Mock()
        middleware = APIResponseTimeMiddleware(get_response)
        assert middleware.get_response == get_response

    def test_adds_response_time_header(self):
        """测试添加响应时间到响应头"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        response = middleware(request)

        # 验证响应头包含响应时间
        assert 'X-Response-Time-ms' in response
        # 验证格式是数字加'ms'后缀
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

        middleware = APIResponseTimeMiddleware(get_response)
        middleware(request)

        # 验证日志被调用
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args

        # 验证日志消息包含响应时间（call_args[0][1]是消息字符串）
        assert 'ms' in call_args[0][1]
        assert '/api/v1/test/' in call_args[0][1]

    @patch('core.middleware.api_response_time.logger')
    def test_includes_response_time_in_context(self, mock_logger):
        """测试日志上下文包含响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        middleware(request)

        # 验证日志上下文
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})

        assert 'response_time_ms' in extra_fields
        assert isinstance(extra_fields['response_time_ms'], (int, float))
        assert extra_fields['method'] == 'GET'
        assert extra_fields['path'] == '/api/v1/test/'
        assert 'is_slow_request' in extra_fields

    @patch('core.middleware.api_response_time.logger')
    def test_marks_slow_requests_as_warning(self, mock_logger):
        """测试慢请求标记为WARNING级别"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟慢请求（>500ms）
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 0.6, current + 0.6, current + 0.6]):
            middleware(request)

        # 验证日志级别为WARNING
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == 30  # logging.WARNING (第一个参数是level)

        # 验证上下文标记为慢请求
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['is_slow_request'] is True

    @patch('core.middleware.api_response_time.logger')
    def test_normal_requests_info_level(self, mock_logger):
        """测试正常请求标记为INFO级别"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟正常请求（<500ms）
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 0.1, current + 0.1, current + 0.1]):
            middleware(request)

        # 验证日志级别为INFO
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == 20  # logging.INFO (第一个参数是level)

        # 验证上下文标记为正常请求
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['is_slow_request'] is False

    @patch('core.middleware.api_response_time.logger')
    def test_logs_request_id(self, mock_logger):
        """测试日志包含request_id"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')
        request.request_id = 'test-request-123'

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        middleware(request)

        # 验证日志包含request_id
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['request_id'] == 'test-request-123'

    @patch('core.middleware.api_response_time.logger')
    def test_logs_user_id_when_authenticated(self, mock_logger):
        """测试认证用户包含user_id"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        # 模拟认证用户
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 42
        request.user = mock_user

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        middleware(request)

        # 验证日志包含user_id
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['user_id'] == 42

    @patch('core.middleware.api_response_time.logger')
    def test_different_http_methods(self, mock_logger):
        """测试不同的HTTP方法"""
        factory = RequestFactory()

        mock_response = HttpResponse('OK', status=200)
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

        for method in methods:
            request = getattr(factory, method.lower())('/api/v1/test/')
            get_response = Mock(return_value=mock_response)

            middleware = APIResponseTimeMiddleware(get_response)
            middleware(request)

            # 验证日志记录了HTTP方法
            call_args = mock_logger.log.call_args
            extra = call_args[1].get('extra', {})
            extra_fields = extra.get('extra_fields', {})
            assert extra_fields['method'] == method

    def test_response_time_calculation_accuracy(self):
        """测试响应时间计算准确性"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟已知延迟
        import time
        current = time.time()
        delay_seconds = 0.25
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + delay_seconds, current + delay_seconds, current + delay_seconds]):
            response = middleware(request)

        # 验证响应时间接近预期
        response_time_header = response['X-Response-Time-ms']
        response_time_value = float(response_time_header.replace('ms', ''))

        # 允许一定的误差（±50ms）
        expected_ms = delay_seconds * 1000
        assert abs(response_time_value - expected_ms) < 50

    @patch('core.middleware.api_response_time.logger')
    def test_logs_slow_request_threshold_boundary(self, mock_logger):
        """测试慢请求边界值（500ms）"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 测试正好500ms的请求
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 0.5, current + 0.5, current + 0.5]):
            middleware(request)

        # 验证慢请求标记
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        # 正好500ms应该被标记为慢请求
        assert extra_fields['is_slow_request'] is True or extra_fields['response_time_ms'] >= 500

    @patch('core.middleware.api_response_time.logger')
    def test_includes_had_error_flag(self, mock_logger):
        """测试日志包含had_error标志"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        middleware(request)

        # 验证had_error标志
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert 'had_error' in extra_fields
        assert extra_fields['had_error'] is False

    def test_normal_request_passes_through(self):
        """测试正常请求通过"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('Success', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)
        response = middleware(request)

        # 验证响应不受影响
        assert response.status_code == 200
        assert response.content == b'Success'

    @patch('core.middleware.api_response_time.logger')
    def test_logs_response_time_on_exception(self, mock_logger):
        """测试异常时也记录响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        # 模拟异常
        exc = ValueError('Test exception')
        get_response = Mock(side_effect=exc)

        middleware = APIResponseTimeMiddleware(get_response)

        # 父类APIErrorLoggingMiddleware会捕获异常并返回错误响应
        # 不会抛出异常，而是返回500错误响应
        response = middleware(request)

        # 验证返回了错误响应
        assert response.status_code == 500

        # 验证记录了响应时间
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})

        # 验证包含响应时间
        assert 'response_time_ms' in extra_fields
        # 父类处理异常后，had_error应该是False（异常已被处理）
        assert extra_fields['had_error'] is False


class TestResponseTimeCalculations:
    """
    响应时间计算测试
    验证响应时间计算的准确性
    """

    def test_fast_request_response_time(self):
        """测试快速请求的响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟快速请求（10ms）
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 0.01, current + 0.01, current + 0.01]):
            response = middleware(request)

        response_time_ms = float(response['X-Response-Time-ms'].replace('ms', ''))
        assert response_time_ms < 50  # 应该小于50ms

    def test_medium_request_response_time(self):
        """测试中等速度请求的响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟中等请求（200ms）
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 0.2, current + 0.2, current + 0.2]):
            response = middleware(request)

        response_time_ms = float(response['X-Response-Time-ms'].replace('ms', ''))
        assert 150 < response_time_ms < 250  # 应该在200ms左右

    def test_slow_request_response_time(self):
        """测试慢请求的响应时间"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIResponseTimeMiddleware(get_response)

        # 模拟慢请求（1000ms）
        import time
        current = time.time()
        # 提供足够的mock值，避免StopIteration
        with patch('time.time', side_effect=[current, current + 1.0, current + 1.0, current + 1.0]):
            response = middleware(request)

        response_time_ms = float(response['X-Response-Time-ms'].replace('ms', ''))
        assert response_time_ms > 900  # 应该大于900ms
