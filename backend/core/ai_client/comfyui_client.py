"""
ComfyUI 文生图客户端实现
支持 ComfyUI API 接口，包括 WebSocket 实时进度监听
"""

import json
import os
import time
import uuid
from io import BytesIO
from typing import Any, Callable, Dict, Optional

import requests
import websocket
from PIL import Image

from core.utils.file_storage import image_storage, video_storage

from .base import Text2ImageClient as BaseText2ImageClient


class ComfyUIClient(BaseText2ImageClient):
    """
    ComfyUI 文生图客户端实现
    支持自定义工作流、实时进度监听、批量生成
    """


    def __init__(self, api_url: str, api_key: str, model_name: str, **kwargs):
        """
        初始化 ComfyUI 客户端

        Args:
            api_url: ComfyUI 服务器地址 (例如: http://127.0.0.1:8188)
            api_key: API密钥 (ComfyUI 通常不需要，保留用于兼容)
            model_name: 模型检查点名称
            **kwargs: 其他配置参数
                - server_address: 服务器地址 (默认从 api_url 解析)
                - checkpoint_name: 模型检查点名称 (默认使用 model_name)
                - workflow_template: 自定义工作流模板
                - timeout: 超时时间 (秒，默认 300)
                - save_images: 是否保存图片到本地 (默认 True)
                - output_dir: 输出目录 (默认 storage/images/comfyui)
        """
        super().__init__(api_url, api_key, model_name, **kwargs)

        # 解析服务器地址
        self.server_address = self._parse_server_address(api_url)
        self.checkpoint_name = kwargs.get('checkpoint_name', model_name)
        self.workflow_template = kwargs.get('workflow_template', {})
        self.timeout = kwargs.get('timeout', 300)
        self.save_images = kwargs.get('save_images', True)
        self.output_dir = kwargs.get('output_dir', 'storage/image')
        self.video_output_dir = kwargs.get('video_output_dir', 'storage/video')
        self.client_id = str(uuid.uuid4())

    def _parse_server_address(self, api_url: str) -> str:
        """
        从 API URL 解析服务器地址

        Args:
            api_url: API URL (例如: http://127.0.0.1:8188)

        Returns:
            str: 服务器地址 (例如: 127.0.0.1:8188)
        """
        # 移除协议前缀
        address = api_url.replace('http://', '').replace('https://', '')
        # 移除尾部斜杠
        address = address.rstrip('/')
        return address

    def _prepare_workflow(
        self,
        prompt: str,
    ) -> Dict[str, Any]:
        """
        准备工作流，注入动态参数

        Args:
            prompt: 正向提示词
            negative_prompt: 负向提示词
            width: 图片宽度
            height: 图片高度
            steps: 采样步数
            cfg: CFG 强度
            seed: 随机种子 (None 则随机生成)
            num_images: 批量生成数量
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 准备好的工作流
        """
        # 深拷贝工作流模板
        prompt = prompt.replace("\n", "")
        workflow = json.loads(prompt)
        return workflow

    def _queue_prompt(self, prompt: Dict[str, Any], prompt_id: str) -> None:
        """
        提交任务到队列

        Args:
            prompt: 工作流数据
            prompt_id: 任务ID

        Raises:
            Exception: 提交失败
        """
        url = f"http://{self.server_address}/prompt"
        payload = {
            "prompt": prompt,
            "client_id": self.client_id,
            "prompt_id": prompt_id
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"提交任务失败: HTTP {response.status_code}")

    def _get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        获取任务历史

        Args:
            prompt_id: 任务ID

        Returns:
            Dict[str, Any]: 任务历史数据
        """
        url = f"http://{self.server_address}/history/{prompt_id}"

        response = requests.get(url, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"获取历史失败: HTTP {response.status_code}")
        return response.json()

    def _get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """
        下载生成的图片

        Args:
            filename: 文件名
            subfolder: 子文件夹
            folder_type: 文件夹类型

        Returns:
            bytes: 图片数据
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url = f"http://{self.server_address}/view"
        response = requests.get(url, params=params, timeout=self.timeout)
        if response.status_code != 200:
            raise Exception(f"下载图片失败: HTTP {response.status_code}")
        return response.content

    def _get_video(
        self,
        filename: str,
        subfolder: str,
        folder_type: str,
        output_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        chunk_size: int = 8192
    ) -> bytes:
        """
        流式下载生成的视频文件

        Args:
            filename: 文件名
            subfolder: 子文件夹
            folder_type: 文件夹类型
            output_path: 输出文件路径 (如果提供则直接写入文件,否则返回字节数据)
            progress_callback: 进度回调函数 callback(downloaded_bytes, total_bytes)
            chunk_size: 分块大小 (字节,默认 8KB)

        Returns:
            bytes: 视频数据 (仅当 output_path 为 None 时返回)

        Raises:
            Exception: 下载失败时抛出异常
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url = f"http://{self.server_address}/view"

        # 使用流式请求
        response = requests.get(url, params=params, stream=True, timeout=self.timeout)

        if response.status_code != 200:
            raise Exception(f"下载视频失败: HTTP {response.status_code}")

        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        # 如果提供了输出路径,流式写入文件
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤掉保持连接的空块
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 调用进度回调
                        if progress_callback:
                            progress_callback(downloaded_size, total_size)

            return b''  # 已写入文件,返回空字节

        # 否则,流式读取到内存
        else:
            chunks = []
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    chunks.append(chunk)
                    downloaded_size += len(chunk)

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(downloaded_size, total_size)

            return b''.join(chunks)

    def _get_images_sync(
        self,
        ws: websocket.WebSocket,
        prompt: Dict[str, Any],
        prompt_id: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, list]:
        """
        通过 WebSocket 监听进度并获取结果 (同步版本)

        Args:
            ws: WebSocket 连接
            prompt: 工作流数据
            prompt_id: 任务ID
            progress_callback: 进度回调函数

        Returns:
            Dict[str, list]: 输出图片数据 {node_id: [image_data, ...]}
        """
        output_images = {}
        current_progress = 20

        if progress_callback:
            progress_callback(current_progress)
        null_queue= []
        while True:
            try:
                out = ws.recv()
            except Exception as e:
                raise Exception(f"WebSocket 接收失败: {e!s}")

            if isinstance(out, str):
                message = json.loads(out)
                print(message['type'])
                if message['type'] == 'progress':
                    null_queue = []
                    # 处理进度信息
                    if 'data' in message:
                        progress_data = message['data']
                        if 'value' in progress_data and 'max' in progress_data:
                            progress_percent = (progress_data['value'] / progress_data['max']) * 70
                            current_progress = 20 + progress_percent
                            if progress_callback:
                                progress_callback(min(90, current_progress))

                elif message['type'] == 'executing':
                    null_queue = []
                    data = message['data']
                    if data['node'] is not None:
                        # 节点开始执行
                        current_progress = max(current_progress, 30)
                        if progress_callback:
                            progress_callback(current_progress)
                    else:
                        # 执行完成
                        break
                else:
                    null_queue.append("null")
                    if len(null_queue) > 10:
                        history = self._get_history(prompt_id)
                        if prompt_id in history:
                            break
                        else:
                            null_queue = []
        return output_images

    def _generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        **kwargs
    ) -> dict:
        """
        生成图片

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            steps: 生成步数
            **kwargs: 其他参数
                - cfg: CFG 强度 (默认 7.0)
                - seed: 随机种子
                - num_images: 批量生成数量 (默认 1)
                - sampler_name: 采样器名称
                - scheduler: 调度器名称
                - progress_callback: 进度回调函数

        Returns:
            AIResponse: 包含图片URL的响应对象
        """
        start_time = time.time()
        prompt_id = str(uuid.uuid4())

        try:
            # 提取参数
            cfg = kwargs.get('cfg', 7.0)
            kwargs.get('seed')
            num_images = kwargs.get('num_images', 1)
            progress_callback = kwargs.get('progress_callback')

            # 准备工作流
            workflow = self._prepare_workflow(
                prompt=prompt,
            )

            if progress_callback:
                progress_callback(10.0)

            # 提交任务
            self._queue_prompt(workflow, prompt_id)

            if progress_callback:
                progress_callback(15.0)

            # 建立 WebSocket 连接并监听进度
            ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
            ws = websocket.WebSocket()

            try:
                ws.connect(ws_url)
                self._get_images_sync(
                    ws,
                    workflow,
                    prompt_id,
                    progress_callback
                )

            finally:
                ws.close()

            if progress_callback:
                progress_callback(95.0)

            # 获取结果
            history = self._get_history(prompt_id)

            if prompt_id not in history:
                return {
                    'success': False,
                    'error': f'任务 {prompt_id} 未找到历史记录'
                }

            task_history = history[prompt_id]

            # 提取图片
            image_urls = []

            for node_id in task_history.get('outputs', {}):
                node_output = task_history['outputs'][node_id]

                if 'images' in node_output:
                    for idx, image_info in enumerate(node_output['images']):
                        # 下载图片
                        image_data = self._get_image(
                            image_info['filename'],
                            image_info['subfolder'],
                            image_info['type']
                        )

                        # 保存图片 (如果启用)
                        if self.save_images:
                            # 使用日期分层存储
                            filename = f"{node_id}_{idx}_{prompt_id[:8]}.png"

                            # 保存图片到PIL对象
                            image = Image.open(BytesIO(image_data))

                            # 将PIL图片转换为字节
                            img_bytes = BytesIO()
                            image.save(img_bytes, format='PNG')
                            img_bytes.seek(0)

                            # 使用日期分层存储保存文件
                            _full_path, relative_path = image_storage.save_file(
                                filename=filename,
                                content=img_bytes.getvalue()
                            )

                            # 构建 URL (使用相对路径)
                            image_url = f"http://127.0.0.1:8010/api/v1/content/storage/image/{relative_path}"
                            image_urls.append({"url": image_url})

                        else:
                            # 不保存，只返回原始信息
                            image_url = f"http://{self.server_address}/view?filename={image_info['filename']}&subfolder={image_info['subfolder']}&type={image_info['type']}"
                            image_urls.append({"url": image_url})

            if progress_callback:
                progress_callback(100.0)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                'success': True,
                'data': image_urls,
                'metadata': {
                    'latency_ms': latency_ms,
                    'model': self.checkpoint_name,
                    'prompt_id': prompt_id,
                    'num_images': num_images,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'cfg': cfg,
                }
            }

        except requests.Timeout:
            return {
                'success': False,
                'error': f'请求超时 (超过 {self.timeout} 秒)'
            }
        except Exception as e:
            print(f"生成图片失败: {e!s}")
            return {
                'success': False,
                'error': f'生成图片失败: {e!s}'
            }
    def _generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        **kwargs
    ) -> dict:
        """
        生成图片

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            steps: 生成步数
            **kwargs: 其他参数
                - cfg: CFG 强度 (默认 7.0)
                - seed: 随机种子
                - num_images: 批量生成数量 (默认 1)
                - sampler_name: 采样器名称
                - scheduler: 调度器名称
                - progress_callback: 进度回调函数

        Returns:
            AIResponse: 包含图片URL的响应对象
        """
        start_time = time.time()
        prompt_id = str(uuid.uuid4())

        try:
            # 提取参数
            cfg = kwargs.get('cfg', 7.0)
            kwargs.get('seed')
            num_images = kwargs.get('num_images', 1)
            progress_callback = kwargs.get('progress_callback')

            # 准备工作流
            workflow = self._prepare_workflow(
                prompt=prompt,
            )

            if progress_callback:
                progress_callback(10.0)

            # 提交任务
            self._queue_prompt(workflow, prompt_id)

            if progress_callback:
                progress_callback(15.0)

            # 建立 WebSocket 连接并监听进度
            ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
            ws = websocket.WebSocket()

            try:
                ws.connect(ws_url)
                self._get_images_sync(
                    ws,
                    workflow,
                    prompt_id,
                    progress_callback
                )

            finally:
                ws.close()

            if progress_callback:
                progress_callback(95.0)

            # 获取结果
            history = self._get_history(prompt_id)

            if prompt_id not in history:
                return {
                    'success': False,
                    'error': f'任务 {prompt_id} 未找到历史记录'
                }

            task_history = history[prompt_id]

            # 提取图片
            image_urls = []

            for node_id in task_history.get('outputs', {}):
                node_output = task_history['outputs'][node_id]

                if 'gifs' in node_output:
                    for idx, image_info in enumerate(node_output['gifs']):
                        # 保存视频 (如果启用)
                        if self.save_images:
                            # 使用日期分层存储
                            filename = f"{node_id}_{idx}_{prompt_id[:8]}.mp4"

                            # 获取唯一的文件路径
                            full_path, relative_path = video_storage.get_unique_filepath(
                                filename=filename,
                                create_dirs=True
                            )

                            # 定义下载进度回调
                            def download_progress(downloaded: int, total: int):
                                if total > 0:
                                    percent = (downloaded / total) * 100
                                    print(f"下载进度: {downloaded}/{total} bytes ({percent:.1f}%)")

                            # 流式下载并直接写入文件 (使用完整路径)
                            self._get_video(
                                image_info['filename'],
                                image_info['subfolder'],
                                image_info['type'],
                                output_path=str(full_path),
                                progress_callback=download_progress
                            )

                            # 构建 URL (使用相对路径)
                            image_url = f"http://127.0.0.1:8010/api/v1/content/storage/video/{relative_path}"
                            image_urls.append({"url": image_url})

                        else:
                            # 不保存，只返回原始信息
                            image_url = f"http://{self.server_address}/view?filename={image_info['filename']}&subfolder={image_info['subfolder']}&type={image_info['type']}"
                            image_urls.append({"url": image_url})

            if progress_callback:
                progress_callback(100.0)

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                'success': True,
                'data': image_urls,
                'metadata': {
                    'latency_ms': latency_ms,
                    'model': self.checkpoint_name,
                    'prompt_id': prompt_id,
                    'num_images': num_images,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'cfg': cfg,
                }
            }

        except requests.Timeout:
            return {
                'success': False,
                'error': f'请求超时 (超过 {self.timeout} 秒)'
            }
        except Exception as e:
            print(f"生成图片失败: {e!s}")
            return {
                'success': False,
                'error': f'生成图片失败: {e!s}'
            }
    def validate_config(self) -> bool:
        """
        验证配置

        Returns:
            bool: 配置是否有效
        """
        if not self.server_address or not self.checkpoint_name:
            return False

        # 尝试连接服务器
        try:
            url = f"http://{self.server_address}/system_stats"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
