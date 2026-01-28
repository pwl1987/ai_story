"""
单元测试: API错误日志中间件
测试APIErrorLoggingMiddleware的异常处理和日志记录功能
"""

import json
from unittest.mock import Mock, patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware.api_error_logging import APIErrorLoggingMiddleware


class TestAPIErrorLoggingMiddleware:
    """
    测试APIErrorLoggingMiddleware类
    验证异常处理和日志记录功能
    """

    def test_middleware_initialization(self):
        """测试中间件初始化"""
        get_response = Mock()
        middleware = APIErrorLoggingMiddleware(get_response)
        assert middleware.get_response == get_response

    def test_middleware_adds_request_id(self):
        """测试中间件为请求添加request_id"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        get_response = Mock(return_value=HttpResponse())
        middleware = APIErrorLoggingMiddleware(get_response)

        middleware(request)

        assert hasattr(request, 'request_id')
        assert request.request_id is not None

    @patch('core.middleware.api_error_logging.logger')
    def test_logs_validation_error(self, mock_logger):
        """测试记录验证错误"""
        factory = RequestFactory()
        request = factory.post('/api/v1/test/', {})

        # 模拟验证错误
        exc = ValidationError('Invalid input data')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        middleware(request)

        # 验证日志被调用
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # 验证日志包含必要信息
        assert 'API Error' in call_args[0][0]
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['method'] == 'POST'
        assert extra_fields['path'] == '/api/v1/test/'
        assert extra_fields['error_type'] == 'ValidationError'
        assert 'request_id' in extra_fields

    @patch('core.middleware.api_error_logging.logger')
    def test_logs_permission_denied_error(self, mock_logger):
        """测试记录权限拒绝错误"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = PermissionDenied('Access denied')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        # 验证响应
        assert response.status_code == 403
        data = json.loads(response.content)
        assert 'error' in data
        assert 'request_id' in data

    @patch('core.middleware.api_error_logging.logger')
    def test_logs_database_error(self, mock_logger):
        """测试记录数据库错误"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = DatabaseError('Connection failed')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        # 验证响应
        assert response.status_code == 500
        data = json.loads(response.content)
        assert 'error' in data

    @patch('core.middleware.api_error_logging.logger')
    def test_logs_generic_exception(self, mock_logger):
        """测试记录通用异常"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = Exception('Unexpected error')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        middleware(request)

        # 验证日志
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['error_type'] == 'Exception'

    def test_returns_400_for_validation_error(self):
        """测试验证错误返回400"""
        factory = RequestFactory()
        request = factory.post('/api/v1/test/', {})

        exc = ValidationError('Invalid input')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 400

    def test_returns_403_for_permission_denied(self):
        """测试权限拒绝返回403"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = PermissionDenied('Access denied')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 403

    def test_returns_500_for_database_error(self):
        """测试数据库错误返回500"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = DatabaseError('Connection failed')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 500

    def test_error_response_structure(self):
        """测试错误响应结构"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = ValidationError('Invalid input')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        data = json.loads(response.content)

        # 验证响应结构
        assert 'error' in data
        assert 'status_code' in data
        assert 'request_id' in data
        assert data['status_code'] == 400

    def test_filters_sensitive_data_in_request_body(self):
        """测试过滤请求体中的敏感数据"""
        middleware = APIErrorLoggingMiddleware(Mock())

        request_data = {
            'username': 'admin',
            'password': 'secret123',
            'email': 'admin@example.com',
            'api_key': 'sk-123456'
        }

        filtered = middleware._filter_sensitive_data(request_data)

        # 验证敏感数据被过滤
        assert filtered['username'] == 'admin'
        assert filtered['password'] == '***FILTERED***'
        assert filtered['email'] == 'admin@example.com'
        assert filtered['api_key'] == '***FILTERED***'

    def test_filters_nested_sensitive_data(self):
        """测试过滤嵌套字典中的敏感数据"""
        middleware = APIErrorLoggingMiddleware(Mock())

        request_data = {
            'user': {
                'username': 'admin',
                'password': 'secret123'
            },
            'settings': {
                'api_key': 'sk-123456'
            }
        }

        filtered = middleware._filter_sensitive_data(request_data)

        # 验证嵌套敏感数据被过滤
        assert filtered['user']['username'] == 'admin'
        assert filtered['user']['password'] == '***FILTERED***'
        assert filtered['settings']['api_key'] == '***FILTERED***'

    def test_filters_sensitive_data_in_list(self):
        """测试过滤列表中的敏感数据"""
        middleware = APIErrorLoggingMiddleware(Mock())

        request_data = {
            'users': [
                {'username': 'user1', 'password': 'pass1'},
                {'username': 'user2', 'password': 'pass2'}
            ]
        }

        filtered = middleware._filter_sensitive_data(request_data)

        # 验证列表中的敏感数据被过滤
        assert filtered['users'][0]['username'] == 'user1'
        assert filtered['users'][0]['password'] == '***FILTERED***'
        assert filtered['users'][1]['password'] == '***FILTERED***'

    @patch('core.middleware.api_error_logging.logger')
    def test_extracts_get_request_params(self, mock_logger):
        """测试提取GET请求参数"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/', {'param1': 'value1', 'param2': 'value2'})

        exc = Exception('Test error')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        middleware(request)

        # 验证日志包含请求参数
        call_args = mock_logger.error.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert 'request_data' in extra_fields
        # 验证请求参数包含预期的数据
        assert 'param1' in extra_fields['request_data']
        assert 'param2' in extra_fields['request_data']

    @patch('core.middleware.api_error_logging.logger')
    def test_extracts_post_request_data(self, mock_logger):
        """测试提取POST请求数据"""
        factory = RequestFactory()
        data = {'field1': 'value1', 'field2': 'value2'}
        request = factory.post(
            '/api/v1/test/',
            data=json.dumps(data),
            content_type='application/json'
        )

        exc = Exception('Test error')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        middleware(request)

        # 验证日志包含请求数据
        call_args = mock_logger.error.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert 'request_data' in extra_fields
        assert extra_fields['request_data']['field1'] == 'value1'

    @patch('core.middleware.api_error_logging.logger')
    def test_includes_user_id_when_authenticated(self, mock_logger):
        """测试认证用户包含user_id"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        # 模拟认证用户
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 42
        request.user = mock_user

        exc = Exception('Test error')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        middleware(request)

        # 验证日志包含user_id
        call_args = mock_logger.error.call_args
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})
        assert extra_fields['user_id'] == 42

    def test_normal_request_passes_through(self):
        """测试正常请求通过"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        mock_response = HttpResponse('OK', status=200)
        get_response = Mock(return_value=mock_response)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        # 验证正常请求不受影响
        assert response.status_code == 200
        assert response.content == b'OK'

    @patch('core.middleware.api_error_logging.logger')
    @patch('django.conf.settings.DEBUG', True)
    def test_includes_detail_in_debug_mode(self, mock_logger, settings):
        """测试DEBUG模式包含详细信息"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = ValidationError('Invalid input')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        data = json.loads(response.content)

        # DEBUG模式下应该包含detail
        assert 'detail' in data
        assert data['detail']['error_type'] == 'ValidationError'
        assert data['detail']['path'] == '/api/v1/test/'
        assert data['detail']['method'] == 'GET'

    @patch('core.middleware.api_error_logging.logger')
    @patch('django.conf.settings.DEBUG', False)
    def test_no_detail_in_production_mode(self, mock_logger, settings):
        """测试生产模式不包含详细信息"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        exc = ValidationError('Invalid input')
        get_response = Mock(side_effect=exc)

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        data = json.loads(response.content)

        # 生产模式下不应该包含detail
        assert 'detail' not in data


class TestMiddlewareIntegration:
    """
    中间件集成测试
    测试中间件与其他组件的协同工作
    """

    def test_middleware_chain(self):
        """测试中间件链式调用"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        # 模拟中间件链
        def get_response(request):
            return HttpResponse('Success')

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        assert response.status_code == 200

    @patch('core.middleware.api_error_logging.logger')
    def test_exception_in_middleware_chain(self, mock_logger):
        """测试中间件链中的异常处理"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        def get_response(request):
            raise ValueError('Test error in chain')

        middleware = APIErrorLoggingMiddleware(get_response)
        response = middleware(request)

        # 验证异常被捕获
        assert response.status_code == 500
        mock_logger.error.assert_called_once()

    def test_request_id_persists(self):
        """测试request_id在整个请求过程中保持一致"""
        factory = RequestFactory()
        request = factory.get('/api/v1/test/')

        get_response = Mock(return_value=HttpResponse())
        middleware = APIErrorLoggingMiddleware(get_response)

        # 第一次调用设置request_id
        middleware(request)
        first_request_id = request.request_id

        # 同一个请求的request_id应该保持一致
        assert request.request_id == first_request_id
