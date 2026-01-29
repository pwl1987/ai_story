"""
文生图客户端实现
支持通用的文生图API接口
"""

import json
import time

import requests

from .base import AIResponse
from .base import Text2ImageClient as BaseText2ImageClient


class Text2ImageClient(BaseText2ImageClient):
    """
    文生图客户端实现
    支持通用的文生图API接口
    """

    def _generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        **kwargs,
    ) -> AIResponse:
        """
        生成图片

        Args:
            prompt: 图片提示词
            negative_prompt: 负面提示词
            width: 宽度
            height: 高度
            steps: 生成步数
            **kwargs: 其他参数（ratio, resolution等）

        Returns:
            AIResponse: 包含图片URL的响应对象
        """
        start_time = time.time()

        # 构建请求头
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

        # 从kwargs获取ratio和resolution，或使用默认值
        ratio = kwargs.get("ratio", "1:1")
        resolution = kwargs.get("resolution", "2k")

        # 构建请求体
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "ratio": ratio,
            "resolution": resolution,
        }

        # 添加可选参数
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        # 添加其他可选参数
        if "sample_strength" in kwargs:
            payload["sample_strength"] = kwargs["sample_strength"]
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]

        try:
            timeout = self.config.get("timeout", 60)

            # 发送POST请求
            response = requests.post(
                self.api_url, headers=headers, data=json.dumps(payload), timeout=timeout
            )

            # 检查响应状态
            response.raise_for_status()

            # 解析响应数据 {"data": [{"url": "xxx"}]}
            result = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            if "data" not in result or not result["data"]:
                return AIResponse(success=False, error="响应格式错误: 缺少data字段或data为空")

            # 提取图片URL列表
            image_urls = [item.get("url", "") for item in result["data"]]

            return AIResponse(
                success=True,
                data={
                    "urls": image_urls,
                    "images": result["data"],  # 包含完整的图片信息
                },
                metadata={
                    "latency_ms": latency_ms,
                    "model": self.model_name,
                    "ratio": ratio,
                    "resolution": resolution,
                },
            )

        except requests.exceptions.RequestException as e:
            return AIResponse(success=False, error=f"网络请求错误: {e!s}")
        except Exception as e:
            return AIResponse(success=False, error=f"未知错误: {e!s}")

    def validate_config(self) -> bool:
        """验证配置"""
        if not self.api_url or not self.api_key or not self.model_name:
            return False

        # 简单的连通性测试（可选实现）
        return True


# 保留旧的函数接口以保持向后兼容
def generate_image(
    api_url,
    session_id,
    model,
    prompt,
    ratio="1:1",
    resolution="2k",
    negative_prompt=None,
    sample_strength=None,
    response_format=None,
):
    """
    调用图像生成API（向后兼容的函数接口）

    参数:
        api_url (str): API地址
        session_id (str): 会话ID，用于Authorization
        model (str): 使用的模型名称，如"jimeng-4.0"
        prompt (str): 图像描述文本
        ratio (str, 可选): 图像比例，默认"1:1"
        resolution (str, 可选): 分辨率级别，默认"2k"
        negative_prompt (str, 可选): 负面提示词
        sample_strength (float, 可选): 采样强度 (0.0-1.0)
        response_format (str, 可选): 响应格式 ("url" 或 "b64_json")

    返回:
        dict: 接口响应数据
    """
    # 构建请求头
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {session_id}"}

    # 构建请求体
    payload = {"model": model, "prompt": prompt, "ratio": ratio, "resolution": resolution}

    # 添加可选参数
    if negative_prompt is not None:
        payload["negative_prompt"] = negative_prompt
    if sample_strength is not None:
        payload["sample_strength"] = sample_strength
    if response_format is not None:
        payload["response_format"] = response_format

    try:
        # 发送POST请求
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))

        # 检查响应状态
        response.raise_for_status()

        # 返回解析后的JSON数据 {"data": [{"url": "xxx"}]}
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        # 可根据需要处理异常，如返回None或重新抛出
        return None
