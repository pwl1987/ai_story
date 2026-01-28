"""
Stable Diffusion文生图客户端实现
支持Automatic1111 WebUI和Stability AI API
"""

import requests
import json
import time
import base64
from typing import Dict, Any, List
from .base import Text2ImageClient, AIResponse


class StableDiffusionClient(Text2ImageClient):
    """
    Stable Diffusion客户端实现
    支持多种SD API接口:
    - Automatic1111 WebUI (/sdapi/v1/txt2img)
    - Stability AI (https://api.stability.ai)

    参数:
    - prompt: 图片提示词
    - negative_prompt: 负面提示词
    - width: 宽度 (默认512)
    - height: 高度 (默认512)
    - steps: 采样步数 (默认20)
    - cfg_scale: 提示词相关性 (默认7.0)
    - sampler_name: 采样器 (默认"Euler a")
    - seed: 随机种子 (默认-1)
    """

    def _generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "Euler a",
        seed: int = -1,
        **kwargs
    ) -> AIResponse:
        """
        生成图片

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度 (必须是64的倍数)
            height: 高度 (必须是64的倍数)
            steps: 采样步数
            cfg_scale: 提示词相关性
            sampler_name: 采样器名称
            seed: 随机种子 (-1为随机)
            **kwargs: 其他参数

        Returns:
            AIResponse: 包含base64图片数据的响应对象
        """
        start_time = time.time()

        # 判断API类型
        api_url = self.api_url
        if 'sdapi' in api_url or 'automatic' in api_url.lower():
            # Automatic1111 WebUI API
            return self._generate_a111(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                sampler_name=sampler_name,
                seed=seed,
                **kwargs
            )
        elif 'stability.ai' in api_url:
            # Stability AI API
            return self._generate_stability_ai(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                **kwargs
            )
        else:
            # 通用API（使用父类实现）
            return super()._generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                **kwargs
            )

    def _generate_a111(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        cfg_scale: float = 7.0,
        sampler_name: str = "Euler a",
        seed: int = -1,
        **kwargs
    ) -> AIResponse:
        """
        使用Automatic1111 WebUI API生成图片
        API端点: POST /sdapi/v1/txt2img

        文档: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
        """
        start_time = time.time()

        # 构建请求头
        headers = {
            "Content-Type": "application/json"
        }

        # 如果有API key，添加到headers
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 构建A111 API payload
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler_name,
            "seed": seed,
            "batch_size": 1,
            "n_iter": 1,
            "save_images": False,
            "send_images": True  # 返回base64图片数据
        }

        # 添加可选参数
        if 'override_settings' in kwargs:
            payload['override_settings'] = kwargs['override_settings']

        try:
            timeout = self.config.get('timeout', 120)

            # 发送请求
            api_url = self.api_url if self.api_url.endswith('/') else self.api_url + '/'
            api_url = api_url + 'sdapi/v1/txt2img'

            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                return AIResponse(
                    success=False,
                    error=f'A111 API请求失败: {response.status_code} - {response.text}'
                )

            result = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            # 检查响应
            if 'images' not in result:
                return AIResponse(
                    success=False,
                    error=f'A111响应格式错误: {result}'
                )

            # 提取图片数据（base64）
            images = result.get('images', [])
            if not images:
                return AIResponse(
                    success=False,
                    error='未生成图片'
                )

            # 如果是base64数据
            image_data = images[0]
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # base64图片数据
                image_b64 = image_data.split(',')[1]
                image_url = f"data:image/png;base64,{image_b64}"
            else:
                # 可能是URL
                image_url = image_data

            return AIResponse(
                success=True,
                data={
                    'url': image_url,
                    'images': [image_url]
                },
                metadata={
                    'latency_ms': latency_ms,
                    'model': self.model_name,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'sampler': sampler_name,
                    'seed': result.get('info', {}).get('all_seeds', [seed])[0] if seed == -1 else seed,
                    'api_type': 'automatic1111'
                }
            )

        except requests.RequestException as e:
            return AIResponse(
                success=False,
                error=f'网络请求错误: {str(e)}'
            )
        except Exception as e:
            return AIResponse(
                success=False,
                error=f'未知错误: {str(e)}'
            )

    def _generate_stability_ai(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg_scale: float = 7.0,
        seed: int = 0,
        **kwargs
    ) -> AIResponse:
        """
        使用Stability AI API生成图片
        文档: https://platform.stability.ai/docs/api-reference

        注意: 需要Stability AI API key
        """
        start_time = time.time()

        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # 构建Stability AI payload
        # 注意: SDXL模型的参数
        payload = {
            "text_prompts": [
                {"text": prompt}
            ],
            "cfg_scale": cfg_scale,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": steps,
            "seed": seed
        }

        # 添加负面提示词
        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })

        # 添加可选参数
        if 'init_image' in kwargs:
            payload["init_image"] = kwargs['init_image']

        try:
            timeout = self.config.get('timeout', 120)

            # Stability AI API端点
            api_url = self.api_url.rstrip('/')
            if not api_url.endswith('v1/generation'):
                api_url += '/v1/generation/stable-diffusion-xl-1024-v1-0'

            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                return AIResponse(
                    success=False,
                    error=f'Stability AI请求失败: {response.status_code} - {response.text}'
                )

            result = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            # 提取图片URL
            artifacts = result.get('artifacts', [])
            if not artifacts:
                return AIResponse(
                    success=False,
                    error='未生成图片'
                )

            image_urls = [artifact.get('finishReason') for artifact in artifacts]

            return AIResponse(
                success=True,
                data={
                    'urls': image_urls,
                    'images': artifacts
                },
                metadata={
                    'latency_ms': latency_ms,
                    'model': self.model_name,
                    'width': width,
                    'height': height,
                    'api_type': 'stability_ai',
                    'seed': seed
                }
            )

        except requests.RequestException as e:
            return AIResponse(
                success=False,
                error=f'网络请求错误: {str(e)}'
            )
        except Exception as e:
            return AIResponse(
                success=False,
                error=f'未知错误: {str(e)}'
            )

    def validate_config(self) -> bool:
        """
        验证配置
        检查API URL、API key和模型名称
        """
        if not self.api_url:
            return False

        # Stability AI需要API key
        if 'stability.ai' in self.api_url and not self.api_key:
            return False

        # 模型名称
        if not self.model_name:
            return False

        # 简单连通性测试
        try:
            if 'sdapi' in self.api_url:
                # A111: GET /sdapi/v1/sd-models
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                api_url = self.api_url if self.api_url.endswith('/') else self.api_url + '/'
                response = requests.get(
                    api_url + 'sdapi/v1/sd-models',
                    headers=headers,
                    timeout=10
                )
                # 200或401都表示API可达
                return response.status_code in [200, 401]

            elif 'stability.ai' in self.api_url:
                # Stability AI: 验证API key
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                response = requests.get(
                    "https://api.stability.ai/v1/user/balance",
                    headers=headers,
                    timeout=10
                )
                return response.status_code in [200, 401]

            return True

        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        **kwargs
    ) -> AIResponse:
        """
        异步生成图片（接口方法）

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            steps: 采样步数
            **kwargs: 其他参数

        Returns:
            AIResponse: 生成结果
        """
        # 同步调用
        return self._generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            **kwargs
        )
