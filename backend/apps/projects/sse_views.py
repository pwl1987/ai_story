"""
SSE流式视图
职责: 提供基于Redis Pub/Sub的Server-Sent Events接口
遵循单一职责原则(SRP)
"""

import json
import logging
from typing import Generator

from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.redis.subscriber import RedisStreamSubscriber

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ProjectStageSSEView(View):
    """
    项目阶段SSE流式视图

    通过Redis Pub/Sub订阅项目阶段的实时数据流
    使用Server-Sent Events (SSE)协议推送给前端

    """

    def get(self, request, project_id: str, stage_name: str):
        """
        GET请求处理

        Args:
            project_id: 项目ID
            stage_name: 阶段名称 (rewrite/storyboard/image_generation等)

        Returns:
            StreamingHttpResponse: SSE流式响应
        """
        # TODO: 添加权限验证
        # 验证用户是否有权限访问该项目
        # user = request.user
        # if not user.is_authenticated:
        #     return HttpResponse('Unauthorized', status=401)

        logger.info(f"SSE连接建立: project_id={project_id}, stage_name={stage_name}")

        # 创建事件流生成器
        event_stream = self._create_event_stream(project_id, stage_name)

        # 返回SSE响应
        response = StreamingHttpResponse(
            event_stream,
            content_type='text/event-stream; charset=utf-8'
        )

        # SSE必需的响应头
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'  # 禁用Nginx缓冲

        # CORS支持 (如果需要)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response

    def _create_event_stream(self, project_id: str, stage_name: str) -> Generator[bytes, None, None]:
        """
        创建SSE事件流生成器

        Args:
            project_id: 项目ID
            stage_name: 阶段名称

        Yields:
            bytes: SSE格式的事件数据
        """
        subscriber = None

        try:
            # 创建Redis订阅器
            subscriber = RedisStreamSubscriber(project_id, stage_name)

            # 发送连接成功消息
            yield self._format_sse_message({
                'type': 'connected',
                'project_id': project_id,
                'stage': stage_name,
                'message': 'SSE连接已建立'
            })

            # 监听Redis消息
            for message in subscriber.listen(timeout=600):  # 10分钟超时
                # 格式化为SSE消息
                sse_message = self._format_sse_message(message)
                yield sse_message

                # 如果收到done或error消息,结束流
                if message.get('type') in ('done', 'error'):
                    logger.info(f"SSE流结束: {message.get('type')}")
                    break

        except Exception as e:
            logger.error(f"SSE流异常: {e!s}")
            # 发送错误消息
            yield self._format_sse_message({
                'type': 'error',
                'error': f'SSE流异常: {e!s}',
                'project_id': project_id
            })

        finally:
            # 清理资源
            if subscriber:
                subscriber.close()

            # 发送流结束消息
            yield self._format_sse_message({
                'type': 'stream_end',
                'project_id': project_id,
                'message': 'SSE流已关闭'
            })

            logger.info(f"SSE连接关闭: project_id={project_id}, stage_name={stage_name}")

    def _format_sse_message(self, data: dict) -> bytes:
        """
        格式化SSE消息

        SSE格式:
        data: {"type": "token", "content": "..."}

        Args:
            data: 消息数据字典

        Returns:
            bytes: SSE格式的消息
        """
        try:
            # 序列化为JSON
            json_data = json.dumps(data, ensure_ascii=False)

            # SSE格式: data: {json}\n\n
            sse_message = f"data: {json_data}\n\n"

            return sse_message.encode('utf-8')

        except Exception as e:
            logger.error(f"SSE消息格式化失败: {e!s}")
            # 返回错误消息
            error_data = json.dumps({
                'type': 'error',
                'error': f'消息格式化失败: {e!s}'
            }, ensure_ascii=False)
            return f"data: {error_data}\n\n".encode()


@method_decorator(csrf_exempt, name='dispatch')
class ProjectAllStagesSSEView(View):
    """
    项目所有阶段SSE流式视图

    订阅项目的所有阶段消息 (使用Redis模式匹配)

    URL: /api/v1/sse/projects/{project_id}/
    """

    def get(self, request, project_id: str):
        """
        GET请求处理

        Args:
            project_id: 项目ID

        Returns:
            StreamingHttpResponse: SSE流式响应
        """
        logger.info(f"SSE连接建立(所有阶段): project_id={project_id}")

        # 创建事件流生成器 (stage_name=None表示订阅所有阶段)
        event_stream = self._create_event_stream(project_id)

        # 返回SSE响应
        response = StreamingHttpResponse(
            event_stream,
            content_type='text/event-stream; charset=utf-8'
        )

        # SSE必需的响应头
        response['Cache-Control'] = 'no-cache, no-transform'
        response['X-Accel-Buffering'] = 'no'

        # CORS支持
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response

    def _create_event_stream(self, project_id: str) -> Generator[bytes, None, None]:
        """
        创建SSE事件流生成器

        Args:
            project_id: 项目ID

        Yields:
            bytes: SSE格式的事件数据
        """
        subscriber = None

        try:
            # 创建Redis订阅器 (订阅所有阶段)
            subscriber = RedisStreamSubscriber(project_id, stage_name=None)

            # 发送连接成功消息
            yield self._format_sse_message({
                'type': 'connected',
                'project_id': project_id,
                'message': 'SSE连接已建立(所有阶段)'
            })

            # 监听Redis消息
            for message in subscriber.listen(timeout=1800):  # 30分钟超时
                # 格式化为SSE消息
                sse_message = self._format_sse_message(message)
                yield sse_message

        except Exception as e:
            logger.error(f"SSE流异常: {e!s}")
            yield self._format_sse_message({
                'type': 'error',
                'error': f'SSE流异常: {e!s}',
                'project_id': project_id
            })

        finally:
            if subscriber:
                subscriber.close()

            yield self._format_sse_message({
                'type': 'stream_end',
                'project_id': project_id,
                'message': 'SSE流已关闭'
            })

            logger.info(f"SSE连接关闭(所有阶段): project_id={project_id}")

    def _format_sse_message(self, data: dict) -> bytes:
        """
        格式化SSE消息

        Args:
            data: 消息数据字典

        Returns:
            bytes: SSE格式的消息
        """
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            sse_message = f"data: {json_data}\n\n"
            return sse_message.encode('utf-8')
        except Exception as e:
            logger.error(f"SSE消息格式化失败: {e!s}")
            error_data = json.dumps({
                'type': 'error',
                'error': f'消息格式化失败: {e!s}'
            }, ensure_ascii=False)
            return f"data: {error_data}\n\n".encode()

