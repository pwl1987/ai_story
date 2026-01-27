"""
健康检查视图
提供系统健康状态检查端点

功能:
- 数据库连接检查
- Redis连接检查（5个数据库）
- 响应时间监控
- 服务版本和启动时间
- 结果缓存（1秒）

遵循SOLID原则:
- 单一职责：仅负责健康检查
- 开闭原则：可扩展新的检查项
- 依赖倒置：依赖Django抽象接口
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from django.db import connections
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View
from django.core.cache import cache


class HealthCheckView(View):
    """
    健康检查视图

    提供系统健康状态检查接口，验证各服务组件的可用性
    """

    # 缓存时间（秒）
    CACHE_TIMEOUT = 1

    # 服务启动时间
    STARTUP_TIME = datetime.utcnow()

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        处理GET请求，返回健康检查结果

        Args:
            request: HTTP请求对象

        Returns:
            HttpResponse: JSON格式的健康检查结果
        """
        start_time = time.time()

        # 尝试从缓存获取结果（失败时跳过缓存）
        cache_key = 'health_check_result'
        try:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                # 添加缓存标识
                cached_result['cached'] = True
                return JsonResponse(cached_result)
        except Exception:
            # 缓存失败，继续执行健康检查
            pass

        # 执行健康检查
        health_data = self._perform_health_check()

        # 计算响应时间（毫秒）
        response_time_ms = (time.time() - start_time) * 1000
        health_data['response_time_ms'] = round(response_time_ms, 2)

        # 添加服务器信息
        health_data['server'] = {
            'request_id': str(uuid.uuid4()),
            'startup_time': self.STARTUP_TIME.isoformat() + 'Z',
            'current_time': datetime.utcnow().isoformat() + 'Z',
        }

        # 判断整体健康状态
        health_data['status'] = self._determine_overall_status(health_data['checks'])

        # 尝试缓存结果（失败时忽略）
        health_data['cached'] = False
        try:
            cache.set(cache_key, health_data, self.CACHE_TIMEOUT)
        except Exception:
            # 缓存失败，忽略
            pass

        # 返回结果
        status_code = 200 if health_data['status'] == 'healthy' else 503
        response = JsonResponse(health_data)
        response.status_code = status_code
        return response

    def _perform_health_check(self) -> Dict[str, Any]:
        """
        执行所有健康检查

        Returns:
            Dict[str, Any]: 包含所有检查结果的字典
        """
        checks = {
            'database': self._check_database(),
            'redis_broker': self._check_redis_broker(),
            'redis_backend': self._check_redis_backend(),
            'redis_pubsub': self._check_redis_pubsub(),
            'redis_channels': self._check_redis_channels(),
            'redis_cache': self._check_redis_cache(),
        }

        return {
            'checks': checks,
        }

    def _check_database(self) -> Dict[str, Any]:
        """
        检查数据库连接状态

        Returns:
            Dict[str, Any]: 数据库检查结果
        """
        check_result = {
            'name': 'Database',
            'status': 'unknown',
            'details': {},
        }

        try:
            # 获取默认数据库连接
            connection = connections['default']

            # 执行简单查询测试连接
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()

            if result and result[0] == 1:
                check_result['status'] = 'healthy'
            else:
                check_result['status'] = 'unhealthy'
                check_result['details']['error'] = 'Unexpected query result'

        except Exception as e:
            check_result['status'] = 'unhealthy'
            check_result['details']['error'] = str(e)
            check_result['details']['error_type'] = type(e).__name__

        return check_result

    def _check_redis_broker(self) -> Dict[str, Any]:
        """
        检查Celery任务队列Redis（数据库0）

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        return self._check_redis(
            name='Redis Broker (Celery Tasks)',
            db_index=0,
        )

    def _check_redis_backend(self) -> Dict[str, Any]:
        """
        检查Celery结果存储Redis（数据库1）

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        return self._check_redis(
            name='Redis Backend (Celery Results)',
            db_index=1,
        )

    def _check_redis_pubsub(self) -> Dict[str, Any]:
        """
        检查Redis Pub/Sub（数据库2）

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        return self._check_redis(
            name='Redis Pub/Sub',
            db_index=2,
        )

    def _check_redis_channels(self) -> Dict[str, Any]:
        """
        检查Channels WebSocket Redis（数据库3）

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        return self._check_redis(
            name='Redis Channels (WebSocket)',
            db_index=3,
        )

    def _check_redis_cache(self) -> Dict[str, Any]:
        """
        检查Django缓存Redis（数据库4）

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        return self._check_redis(
            name='Redis Cache (Django)',
            db_index=4,
        )

    def _check_redis(self, name: str, db_index: int) -> Dict[str, Any]:
        """
        检查指定Redis数据库的连接状态

        Args:
            name: Redis实例名称
            db_index: 数据库索引

        Returns:
            Dict[str, Any]: Redis检查结果
        """
        check_result = {
            'name': name,
            'status': 'unknown',
            'details': {
                'database': db_index,
            },
        }

        try:
            from django.conf import settings
            import redis

            # 从settings获取Redis连接信息
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)

            # 创建Redis连接
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=db_index,
                socket_connect_timeout=1,  # 1秒超时
                socket_timeout=1,
            )

            # 执行PING命令测试连接
            result = client.ping()

            if result:
                check_result['status'] = 'healthy'
                # 添加Redis信息
                info = client.info('server')
                check_result['details']['redis_version'] = info.get('redis_version', 'unknown')
            else:
                check_result['status'] = 'unhealthy'
                check_result['details']['error'] = 'PING command failed'

            # 关闭连接
            client.close()

        except ImportError:
            check_result['status'] = 'unhealthy'
            check_result['details']['error'] = 'redis module not installed'

        except Exception as e:
            check_result['status'] = 'unhealthy'
            check_result['details']['error'] = str(e)
            check_result['details']['error_type'] = type(e).__name__

        return check_result

    def _determine_overall_status(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """
        根据所有检查结果判断整体健康状态

        Args:
            checks: 所有检查结果

        Returns:
            str: 整体健康状态 (healthy/degraded/unhealthy)
        """
        statuses = [check['status'] for check in checks.values()]

        if all(status == 'healthy' for status in statuses):
            return 'healthy'
        elif any(status == 'unhealthy' for status in statuses):
            return 'unhealthy'
        else:
            return 'degraded'
