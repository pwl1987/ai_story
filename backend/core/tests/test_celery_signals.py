"""
单元测试: Celery任务失败日志 (Story 2.4)
测试增强的Celery信号处理器
"""

from unittest.mock import Mock, patch

from celery.exceptions import Ignore, Retry

from config.celery import (
    _filter_sensitive_kwargs,
    task_failure_handler,
    task_postrun_handler,
    task_prerun_handler,
    task_retry_handler,
)


class TestTaskPrerunHandler:
    """
    测试任务开始前处理器
    """

    @patch('config.celery.logger')
    def test_logs_task_start(self, mock_logger):
        """测试记录任务开始"""
        # 模拟任务和请求
        mock_task = Mock()
        mock_task.name = 'test_task'
        mock_task.request.args = [1, 2, 3]
        mock_task.request.kwargs = {'key': 'value'}
        mock_task.request.retries = 0

        # 调用处理器
        task_prerun_handler(
            sender=mock_task,
            task_id='test-task-id',
            task=mock_task
        )

        # 验证日志被调用
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # 验证日志消息
        assert 'Task started' in call_args[0][0]

        # 验证日志上下文
        extra = call_args[1].get('extra', {})
        extra_fields = extra.get('extra_fields', {})

        assert extra_fields['task_id'] == 'test-task-id'
        assert extra_fields['task_name'] == 'test_task'
        assert extra_fields['event'] == 'task_prerun'
        assert extra_fields['retries'] == 0

    @patch('config.celery.logger')
    def test_includes_task_arguments(self, mock_logger):
        """测试日志包含任务参数"""
        mock_task = Mock()
        mock_task.name = 'test_task'
        mock_task.request.args = ['arg1', 'arg2']
        mock_task.request.kwargs = {'param1': 'value1'}
        mock_task.request.retries = 1

        task_prerun_handler(
            sender=mock_task,
            task_id='test-id',
            task=mock_task
        )

        call_args = mock_logger.info.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证参数被记录
        assert 'args' in extra_fields
        assert 'kwargs' in extra_fields


class TestTaskPostrunHandler:
    """
    测试任务完成后处理器
    """

    @patch('config.celery.logger')
    def test_logs_task_completion(self, mock_logger):
        """测试记录任务完成"""
        mock_task = Mock()
        mock_task.name = 'test_task'
        # Story 2.6: 需要设置start_time为None或有效值
        mock_task.request.start_time = None

        task_postrun_handler(
            sender=mock_task,
            task_id='test-id',
            task=mock_task,
            retval={'status': 'success'},
            args=(),
            kwargs={},
            state='SUCCESS'  # state 是信号的直接参数
        )

        # 验证日志被调用
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args

        # 验证日志消息
        assert 'Task completed' in call_args[0][1]

        # 验证日志上下文
        extra_fields = call_args[1]['extra']['extra_fields']
        assert extra_fields['task_id'] == 'test-id'
        assert extra_fields['task_name'] == 'test_task'
        assert extra_fields['state'] == 'SUCCESS'
        assert extra_fields['event'] == 'task_postrun'

    @patch('config.celery.logger')
    def test_limits_retval_length(self, mock_logger):
        """测试返回值长度限制"""
        mock_task = Mock()
        mock_task.name = 'test_task'
        # Story 2.6: 设置start_time为None
        mock_task.request.start_time = None

        # 创建一个很长的返回值
        long_retval = 'x' * 1000

        task_postrun_handler(
            sender=mock_task,
            task_id='test-id',
            task=mock_task,
            retval=long_retval,
            args=(),
            kwargs={},
            state='SUCCESS'
        )

        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证返回值被截断到500字符
        assert len(extra_fields['retval']) <= 500

    @patch('config.celery.logger')
    def test_ignores_retry_exception(self, mock_logger):
        """测试忽略Retry异常"""
        mock_task = Mock()
        mock_task.name = 'test_task'

        # Retry异常应该被忽略，不记录为完成
        task_postrun_handler(
            sender=mock_task,
            task_id='test-id',
            task=mock_task,
            retval=Retry("Retrying"),
            args=(),
            kwargs={},
            state='RETRY'
        )

        # 应该不记录日志
        mock_logger.info.assert_not_called()

    @patch('config.celery.logger')
    def test_ignores_ignore_exception(self, mock_logger):
        """测试忽略Ignore异常"""
        mock_task = Mock()
        mock_task.name = 'test_task'

        # Ignore异常应该被忽略，不记录为完成
        task_postrun_handler(
            sender=mock_task,
            task_id='test-id',
            task=mock_task,
            retval=Ignore(),
            args=(),
            kwargs={},
            state='IGNORE'
        )

        # 应该不记录日志
        mock_logger.info.assert_not_called()


class TestTaskRetryHandler:
    """
    测试任务重试处理器
    """

    @patch('config.celery.logger')
    def test_logs_task_retry(self, mock_logger):
        """测试记录任务重试"""
        mock_task = Mock()
        mock_task.name = 'retry_task'
        mock_task.request.retries = 2
        mock_task.max_retries = 3

        Exception("Temporary failure")

        task_retry_handler(
            sender=mock_task,
            task_id='retry-id',
            reason="Connection timeout",
            einfo=None
        )

        # 验证WARNING日志被调用
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args

        # 验证日志消息
        assert 'Task retrying' in call_args[0][0]

        # 验证日志上下文
        extra_fields = call_args[1]['extra']['extra_fields']
        assert extra_fields['task_id'] == 'retry-id'
        assert extra_fields['task_name'] == 'retry_task'
        assert extra_fields['reason'] == 'Connection timeout'
        assert extra_fields['retries'] == 2
        assert extra_fields['max_retries'] == 3
        assert extra_fields['event'] == 'task_retry'

    @patch('config.celery.logger')
    def test_handles_missing_sender(self, mock_logger):
        """测试处理缺失sender的情况"""
        task_retry_handler(
            sender=None,
            task_id='retry-id',
            reason="Unknown error",
            einfo=None
        )

        call_args = mock_logger.warning.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证默认值
        assert extra_fields['task_name'] == 'unknown'


class TestTaskFailureHandler:
    """
    测试任务失败处理器
    """

    @patch('config.celery.logger')
    def test_logs_task_failure(self, mock_logger):
        """测试记录任务失败"""
        mock_task = Mock()
        mock_task.name = 'failing_task'
        mock_task.request.args = ['arg1']
        mock_task.request.kwargs = {'key': 'value'}
        mock_task.request.retries = 1

        exception = ValueError("Test error")

        task_failure_handler(
            sender=mock_task,
            task_id='fail-id',
            exception=exception,
            einfo=None
        )

        # 验证ERROR日志被调用
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        # 验证日志消息
        assert 'Task failed' in call_args[0][0]
        assert 'failing_task' in call_args[0][0]
        assert 'ValueError' in call_args[0][0]

        # 验证日志上下文
        extra_fields = call_args[1]['extra']['extra_fields']
        assert extra_fields['task_id'] == 'fail-id'
        assert extra_fields['task_name'] == 'failing_task'
        assert extra_fields['exception_type'] == 'ValueError'
        assert extra_fields['exception_message'] == 'Test error'
        assert extra_fields['retries'] == 1
        assert extra_fields['event'] == 'task_failure'

    @patch('config.celery.logger')
    def test_includes_traceback(self, mock_logger):
        """测试包含堆栈跟踪"""
        mock_task = Mock()
        mock_task.name = 'failing_task'
        mock_task.request.args = []
        mock_task.request.kwargs = {}
        mock_task.request.retries = 0

        exception = RuntimeError("Runtime error")

        task_failure_handler(
            sender=mock_task,
            task_id='fail-id',
            exception=exception,
            einfo=None
        )

        call_args = mock_logger.error.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证traceback被记录
        assert 'traceback' in extra_fields
        assert isinstance(extra_fields['traceback'], list)

    @patch('config.celery.logger')
    def test_limits_args_length(self, mock_logger):
        """测试参数长度限制"""
        mock_task = Mock()
        mock_task.name = 'failing_task'
        mock_task.request.args = ['x' * 2000]  # 超长参数
        mock_task.request.kwargs = {}
        mock_task.request.retries = 0

        exception = Exception("Test")

        task_failure_handler(
            sender=mock_task,
            task_id='fail-id',
            exception=exception,
            einfo=None
        )

        call_args = mock_logger.error.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证参数被截断到1000字符
        assert len(extra_fields['args']) <= 1000

    @patch('config.celery.logger')
    def test_filters_sensitive_data_in_kwargs(self, mock_logger):
        """测试过滤kwargs中的敏感数据"""
        mock_task = Mock()
        mock_task.name = 'failing_task'
        mock_task.request.args = []
        mock_task.request.kwargs = {
            'username': 'admin',
            'password': 'secret123',
            'api_key': 'sk-123456'
        }
        mock_task.request.retries = 0

        exception = Exception("Test")

        task_failure_handler(
            sender=mock_task,
            task_id='fail-id',
            exception=exception,
            einfo=None
        )

        call_args = mock_logger.error.call_args
        extra_fields = call_args[1]['extra']['extra_fields']

        # 验证敏感数据被过滤
        kwargs_str = extra_fields['kwargs']
        assert 'admin' in kwargs_str  # 用户名保留
        assert 'secret123' not in kwargs_str  # 密码被过滤
        assert 'sk-123456' not in kwargs_str  # API密钥被过滤
        assert '***FILTERED***' in kwargs_str


class TestFilterSensitiveKwargs:
    """
    测试敏感参数过滤函数
    """

    def test_filters_password(self):
        """测试过滤password字段"""
        kwargs = {
            'username': 'admin',
            'password': 'secret123'
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        assert filtered['username'] == 'admin'
        assert filtered['password'] == '***FILTERED***'

    def test_filters_api_key(self):
        """测试过滤api_key字段"""
        kwargs = {
            'api_key': 'sk-123456',
            'other': 'value'
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        assert filtered['api_key'] == '***FILTERED***'
        assert filtered['other'] == 'value'

    def test_filters_nested_sensitive_data(self):
        """测试过滤嵌套字典中的敏感数据"""
        kwargs = {
            'user': {
                'username': 'admin',
                'password': 'secret123'
            }
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        assert filtered['user']['username'] == 'admin'
        assert filtered['user']['password'] == '***FILTERED***'

    def test_case_insensitive_matching(self):
        """测试大小写不敏感匹配"""
        kwargs = {
            'PASSWORD': 'secret',
            'Api_Key': 'key123',
            'SECRET': 'topsecret'
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        assert filtered['PASSWORD'] == '***FILTERED***'
        assert filtered['Api_Key'] == '***FILTERED***'
        assert filtered['SECRET'] == '***FILTERED***'

    def test_filters_all_sensitive_fields(self):
        """测试过滤所有敏感字段"""
        kwargs = {
            'password': 'pass1',
            'api_key': 'key1',
            'secret': 'secret1',
            'token': 'token1',
            'authorization': 'auth1',
            'csrf_token': 'csrf1',
            'access_token': 'access1',
            'refresh_token': 'refresh1'
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        # 验证所有敏感字段都被过滤
        for key in kwargs:
            assert filtered[key] == '***FILTERED***'

    def test_preserves_non_sensitive_data(self):
        """测试保留非敏感数据"""
        kwargs = {
            'username': 'admin',
            'email': 'admin@example.com',
            'project_id': '123'
        }

        filtered = _filter_sensitive_kwargs(kwargs)

        # 验证非敏感数据被保留
        assert filtered['username'] == 'admin'
        assert filtered['email'] == 'admin@example.com'
        assert filtered['project_id'] == '123'
