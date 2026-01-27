"""
Celery配置
用于异步任务处理和Redis Pub/Sub集成

Story 2.4: 增强的任务失败日志记录
- 结构化日志记录
- 失败原因追踪
- 重试信息记录
- 任务上下文捕获

Story 2.6: 任务执行时间监控
- 任务执行时间记录
- 慢任务检测和告警
- P95/P99执行时间统计支持

Epic 2优化: 阈值从settings配置读取，便于运维调整
"""

import logging
import os
import time
import traceback
from typing import Any, Dict

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry
from celery.exceptions import Retry, Ignore
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('ai_story')

# 任务日志记录器
logger = logging.getLogger('apps.celery')


def _get_slow_task_threshold():
    """
    获取慢任务阈值（从settings读取）

    Epic 2优化: 从settings配置读取，便于运维调整
    使用延迟加载避免循环依赖

    Returns:
        int: 慢任务阈值（秒）
    """
    return getattr(settings, 'SLOW_TASK_THRESHOLD_S', 60)  # 60秒默认值


# 从Django settings加载配置
app.config_from_object('django.conf:settings')

# 自动发现任务
app.autodiscover_tasks()

# Celery配置优化
# 注意: broker_url 和 result_backend 必须在这里显式设置
# 否则会使用 Celery 的默认值 redis://localhost:6379/0

app.conf.update(
    # Broker和Backend配置 (必须显式设置)
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,

    # Broker连接配置
    broker_connection_retry_on_startup=True,  # Celery 6.0+ 启动时重试连接

    # 任务结果过期时间 (1小时)
    result_expires=3600,

    # 任务序列化
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,

    # # 任务路由 (可选，用于任务分发到不同队列)
    # task_routes={
    #     'apps.projects.tasks.execute_llm_stage': {'queue': 'llm'},
    #     'apps.projects.tasks.execute_text2image_stage': {'queue': 'image'},
    #     'apps.projects.tasks.execute_image2video_stage': {'queue': 'video'},
    # },

    # 任务优先级
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker配置
    worker_prefetch_multiplier=1,  # 每次只预取1个任务
    worker_max_tasks_per_child=100,  # 每个worker处理100个任务后重启
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')


# Celery信号处理 - Story 2.4 + 2.6: 增强的结构化日志记录 + 执行时间监控
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """
    任务开始前记录

    Story 2.4: 记录任务开始信息，用于性能分析和故障排查
    Story 2.6: 记录任务开始时间，用于执行时间计算
    """
    # 记录开始时间到任务请求上下文（Story 2.6）
    if hasattr(task, 'request'):
        task.request.start_time = time.time()

    logger.info(
        f"Task started: {sender.name}",
        extra={'extra_fields': {
            'task_id': task_id,
            'task_name': sender.name,
            'args': str(task.request.args) if hasattr(task, 'request') else [],
            'kwargs': str(task.request.kwargs) if hasattr(task, 'request') else {},
            'retries': task.request.retries if hasattr(task, 'request') else 0,
            'event': 'task_prerun'
        }}
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """
    任务完成后记录

    Story 2.4: 记录任务完成信息，包括返回值和状态
    Story 2.6: 记录任务执行时间，检测慢任务
    """
    # 忽略 Retry 和 Ignore 异常（不是真正的失败）
    if isinstance(retval, (Retry, Ignore)):
        return

    # 计算执行时间（Story 2.6）
    runtime_s = None
    is_slow_task = False

    if hasattr(task, 'request') and hasattr(task.request, 'start_time') and task.request.start_time is not None:
        runtime_s = time.time() - task.request.start_time
        slow_threshold = _get_slow_task_threshold()
        is_slow_task = runtime_s > slow_threshold

    # 确定日志级别（Story 2.6: 慢任务使用WARNING）
    log_level = logging.WARNING if is_slow_task else logging.INFO
    log_message = f"Task completed: {sender.name}"
    if runtime_s is not None:
        log_message += f" ({runtime_s:.2f}s)"

    # 构建日志上下文
    context = {
        'task_id': task_id,
        'task_name': sender.name,
        'state': kwargs.get('state', 'UNKNOWN'),
        'retval': str(retval)[:500] if retval else None,  # 限制长度
        'event': 'task_postrun'
    }

    # 添加执行时间信息（Story 2.6）
    if runtime_s is not None:
        context['runtime_s'] = round(runtime_s, 2)
        context['is_slow_task'] = is_slow_task

    logger.log(
        log_level,
        log_message,
        extra={'extra_fields': context}
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """
    任务重试记录

    Story 2.4: 记录任务重试信息，包括重试原因和堆栈信息
    """
    logger.warning(
        f"Task retrying: {sender.name if sender else 'unknown'}",
        extra={'extra_fields': {
            'task_id': task_id,
            'task_name': sender.name if sender else 'unknown',
            'reason': str(reason) if reason else 'Unknown reason',
            'traceback': traceback.format_exc() if einfo else None,
            'retries': sender.request.retries if hasattr(sender, 'request') else 0,
            'max_retries': sender.max_retries if hasattr(sender, 'max_retries') else None,
            'event': 'task_retry'
        }}
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwargs):
    """
    任务失败记录

    Story 2.4: 增强的任务失败日志记录
    - 记录详细的异常信息
    - 记录任务参数和上下文
    - 记录堆栈跟踪
    - 支持故障排查和分析
    """
    # 获取任务信息
    task_name = sender.name if sender else 'unknown'
    exc_type = type(exception).__name__ if exception else 'Unknown'
    exc_message = str(exception) if exception else 'No exception message'

    # 获取任务请求信息
    args = []
    kwargs_dict = {}
    retries = 0

    if sender and hasattr(sender, 'request'):
        request = sender.request
        args = request.args if hasattr(request, 'args') else []
        kwargs_dict = request.kwargs if hasattr(request, 'kwargs') else {}
        retries = request.retries if hasattr(request, 'retries') else 0

    # 过滤敏感参数
    filtered_kwargs = _filter_sensitive_kwargs(kwargs_dict)

    # 构建日志上下文
    context = {
        'task_id': task_id,
        'task_name': task_name,
        'exception_type': exc_type,
        'exception_message': exc_message,
        'traceback': traceback.format_exception(type(exception), exception, exception.__traceback__) if exception else [],
        'args': str(args)[:1000],  # 限制长度
        'kwargs': str(filtered_kwargs)[:1000],  # 限制长度并过滤敏感信息
        'retries': retries,
        'event': 'task_failure'
    }

    # 记录错误日志
    logger.error(
        f"Task failed: {task_name} - {exc_type}: {exc_message}",
        extra={'extra_fields': context}
    )


def _filter_sensitive_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    过滤敏感参数

    Story 2.4: 防止敏感数据（如密码、API密钥）被记录到日志中

    Args:
        kwargs: 任务参数字典

    Returns:
        过滤后的参数字典
    """
    sensitive_fields = {
        'password', 'api_key', 'apikey', 'secret', 'token',
        'authorization', 'csrf_token', 'access_token', 'refresh_token'
    }

    filtered = {}
    for key, value in kwargs.items():
        if key.lower() in sensitive_fields:
            filtered[key] = '***FILTERED***'
        elif isinstance(value, dict):
            # 递归过滤嵌套字典
            filtered[key] = _filter_sensitive_kwargs(value)
        else:
            filtered[key] = value

    return filtered
