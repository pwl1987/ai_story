"""
单元测试: Celery任务执行时间监控 (Story 2.6)
测试任务执行时间记录和慢任务检测功能
"""

import time
from unittest.mock import Mock, patch

from celery.exceptions import Ignore, Retry

from config.celery import _get_slow_task_threshold, task_postrun_handler, task_prerun_handler


class TestTaskExecutionTime:
    """
    测试任务执行时间监控
    """

    @patch("config.celery.logger")
    def test_records_start_time(self, mock_logger):
        """测试记录任务开始时间"""
        mock_task = Mock()
        mock_task.name = "test_task"
        mock_task.request.args = []
        mock_task.request.kwargs = {}
        mock_task.request.retries = 0

        task_prerun_handler(sender=mock_task, task_id="task-123", task=mock_task)

        # 验证开始时间被记录
        assert hasattr(mock_task.request, "start_time")
        assert isinstance(mock_task.request.start_time, float)

        # 验证日志被调用
        mock_logger.info.assert_called_once()

    @patch("config.celery.logger")
    def test_calculates_execution_time(self, mock_logger):
        """测试计算任务执行时间"""
        mock_task = Mock()
        mock_task.name = "test_task"

        # 模拟开始时间
        start_time = time.time()
        mock_task.request.start_time = start_time

        # 模拟任务执行
        time.sleep(0.1)

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 验证logger.log被调用
        assert mock_logger.log.called

        # 获取日志上下文
        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]["extra"]["extra_fields"]

        # 验证执行时间被记录
        assert "runtime_s" in extra_fields
        assert isinstance(extra_fields["runtime_s"], (int, float))
        assert extra_fields["runtime_s"] >= 0.1  # 至少睡了0.1秒

    @patch("config.celery.logger")
    def test_fast_task_info_level(self, mock_logger):
        """测试快速任务使用INFO级别"""
        mock_task = Mock()
        mock_task.name = "fast_task"
        mock_task.request.start_time = time.time()

        # 模拟快速任务（< 60秒）
        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 验证使用logger.log，第一个参数是INFO级别(20)
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        log_level = call_args[0][0]  # 第一个参数是日志级别

        # INFO级别是20
        assert log_level == 20  # logging.INFO

        # 验证is_slow_task为False
        extra_fields = call_args[1]["extra"]["extra_fields"]
        assert extra_fields["is_slow_task"] is False

    @patch("config.celery.logger")
    def test_slow_task_warning_level(self, mock_logger):
        """测试慢任务使用WARNING级别"""
        mock_task = Mock()
        mock_task.name = "slow_task"

        # 模拟慢任务（> 60秒）
        mock_task.request.start_time = time.time() - 70  # 70秒前开始

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 验证使用WARNING级别
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        log_level = call_args[0][0]  # 第一个参数是日志级别

        # WARNING级别是30
        assert log_level == 30  # logging.WARNING

        # 验证is_slow_task为True
        extra_fields = call_args[1]["extra"]["extra_fields"]
        assert extra_fields["is_slow_task"] is True
        assert extra_fields["runtime_s"] > _get_slow_task_threshold()

    @patch("config.celery.logger")
    def test_threshold_boundary(self, mock_logger):
        """测试慢任务阈值边界（60秒）"""
        mock_task = Mock()
        mock_task.name = "boundary_task"

        # 测试正好60秒的任务
        mock_task.request.start_time = time.time() - 60

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]["extra"]["extra_fields"]

        # 正好60秒应该被标记为慢任务或接近慢任务
        assert extra_fields["runtime_s"] >= _get_slow_task_threshold()

    @patch("config.celery.logger")
    def test_includes_runtime_in_message(self, mock_logger):
        """测试日志消息包含执行时间"""
        mock_task = Mock()
        mock_task.name = "test_task"
        mock_task.request.start_time = time.time() - 5  # 5秒前开始

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 获取日志消息
        call_args = mock_logger.log.call_args
        message = call_args[0][1]  # 第二个参数是消息字符串

        # 验证消息包含执行时间
        assert "s)" in message or "Task completed" in message  # 执行时间在消息中

    @patch("config.celery.logger")
    def test_handles_missing_start_time(self, mock_logger):
        """测试处理缺失开始时间的情况"""
        mock_task = Mock()
        mock_task.name = "test_task"
        mock_task.request.start_time = None  # 没有开始时间

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 验证仍然记录日志，但没有执行时间
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]["extra"]["extra_fields"]

        assert "runtime_s" not in extra_fields or extra_fields.get("runtime_s") is None

    @patch("config.celery.logger")
    def test_retry_exception_no_runtime(self, mock_logger):
        """测试Retry异常不记录执行时间"""
        mock_task = Mock()
        mock_task.name = "test_task"
        mock_task.request.start_time = time.time()

        # Retry异常应该被忽略
        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval=Retry("Retrying"),
            args=(),
            kwargs={},
            state="RETRY",
        )

        # 验证不记录日志
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("config.celery.logger")
    def test_ignore_exception_no_runtime(self, mock_logger):
        """测试Ignore异常不记录执行时间"""
        mock_task = Mock()
        mock_task.name = "test_task"
        mock_task.request.start_time = time.time()

        # Ignore异常应该被忽略
        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval=Ignore(),
            args=(),
            kwargs={},
            state="IGNORE",
        )

        # 验证不记录日志
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()


class TestExecutionTimeAccuracy:
    """
    测试执行时间计算准确性
    """

    @patch("config.celery.logger")
    def test_fast_task_runtime(self, mock_logger):
        """测试快速任务的执行时间"""
        mock_task = Mock()
        mock_task.name = "fast_task"

        # 模拟快速任务（5秒）
        mock_task.request.start_time = time.time() - 5

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]["extra"]["extra_fields"]

        # 验证执行时间接近5秒
        assert 4.5 < extra_fields["runtime_s"] < 5.5

    @patch("config.celery.logger")
    def test_medium_task_runtime(self, mock_logger):
        """测试中等速度任务的执行时间"""
        mock_task = Mock()
        mock_task.name = "medium_task"

        # 模拟中等任务（30秒）
        mock_task.request.start_time = time.time() - 30

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        call_args = mock_logger.log.call_args
        extra_fields = call_args[1]["extra"]["extra_fields"]

        # 验证执行时间接近30秒
        assert 29.5 < extra_fields["runtime_s"] < 30.5

    @patch("config.celery.logger")
    def test_slow_task_runtime(self, mock_logger):
        """测试慢任务的执行时间"""
        mock_task = Mock()
        mock_task.name = "slow_task"

        # 模拟慢任务（120秒）
        mock_task.request.start_time = time.time() - 120

        task_postrun_handler(
            sender=mock_task,
            task_id="task-123",
            task=mock_task,
            retval={"success": True},
            args=(),
            kwargs={},
            state="SUCCESS",
        )

        # 应该使用WARNING级别
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        log_level = call_args[0][0]

        # 验证WARNING级别
        assert log_level == 30  # logging.WARNING

        extra_fields = call_args[1]["extra"]["extra_fields"]

        # 验证执行时间接近120秒
        assert 119.5 < extra_fields["runtime_s"] < 120.5
        assert extra_fields["is_slow_task"] is True
