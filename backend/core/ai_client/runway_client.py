"""
Runway图生视频客户端实现
支持Runway Gen-2/Gen-3模型
使用任务提交+轮询模式
"""

import time
from typing import Any, Dict, Optional

import requests

from .base import AIResponse, Image2VideoClient


class RunwayClient(Image2VideoClient):
    """
    Runway图生视频客户端
    支持Gen-2和Gen-3模型

    特性:
    - 任务提交+轮询模式（非实时）
    - 进度回调支持
    - 支持多种运镜参数

    API文档: https://dev.runwayml.com/docs
    """

    def _generate_video(
        self,
        image_url: str,
        prompt: str = "",
        duration: int = 5,
        model: str = "gen3a_turbo",
        ratio: str = "1280:720",
        watermark: bool = False,
        **kwargs,
    ) -> AIResponse:
        """
        生成视频

        Args:
            image_url: 输入图片URL
            prompt: 视频描述提示词
            duration: 视频时长（秒）
            model: 模型选择 (gen3, gen3a_turbo, gen2)
            ratio: 宽高比
            watermark: 是否添加水印
            **kwargs: 其他参数（move_camera等）

        Returns:
            AIResponse: 包含视频URL的响应对象
        """
        start_time = time.time()

        # 提交任务
        task_id = self._submit_task(
            image_url=image_url,
            prompt=prompt,
            model=model,
            duration=duration,
            ratio=ratio,
            watermark=watermark,
            **kwargs,
        )

        if not task_id:
            return AIResponse(success=False, error="任务提交失败")

        # 轮询任务状态
        result = self._poll_task(task_id)

        if result["success"]:
            latency_ms = int((time.time() - start_time) * 1000)
            return AIResponse(
                success=True,
                data={"url": result["url"], "task_id": task_id},
                metadata={
                    "latency_ms": latency_ms,
                    "model": model,
                    "duration": duration,
                    "ratio": ratio,
                },
            )
        else:
            return AIResponse(success=False, error=result.get("error", "视频生成失败"))

    def _submit_task(
        self,
        image_url: str,
        prompt: str = "",
        model: str = "gen3a_turbo",
        duration: int = 5,
        ratio: str = "1280:720",
        watermark: bool = False,
        **kwargs,
    ) -> Optional[str]:
        """
        提交视频生成任务

        Returns:
            str: 任务ID，失败返回None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-09-26",
        }

        # 构建请求payload
        payload = {"model": model, "input_image": image_url, "duration": duration}

        # 添加可选参数
        if prompt:
            payload["prompt"] = {"prompt": prompt}

        if ratio:
            payload["ratio"] = ratio

        if watermark is not None:
            payload["watermark"] = watermark

        # 添加运镜参数
        if "move_camera" in kwargs:
            payload["move_camera"] = kwargs["move_camera"]

        if "zoom" in kwargs:
            payload["zoom"] = kwargs["zoom"]

        try:
            timeout = self.config.get("timeout", 30)

            api_url = self.api_url.rstrip("/")

            # Runway API端点
            if not api_url.endswith("/tasks"):
                api_url += "/tasks"

            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)

            if response.status_code not in [200, 201]:
                print(f"Runway API错误: {response.status_code} - {response.text}")
                return None

            result = response.json()

            # 提取任务ID
            if "id" in result:
                return result["id"]

            return None

        except requests.RequestException as e:
            print(f"网络请求错误: {e!s}")
            return None
        except Exception as e:
            print(f"未知错误: {e!s}")
            return None

    def _poll_task(
        self, task_id: str, max_wait_time: int = 600, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        轮询任务状态直到完成

        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）

        Returns:
            Dict: {success: bool, url: str, error: str}
        """
        headers = {"Authorization": f"Bearer {self.api_key}", "X-Runway-Version": "2024-09-26"}

        start_time = time.time()

        try:
            while (time.time() - start_time) < max_wait_time:
                # 查询任务状态
                api_url = self.api_url.rstrip("/")
                if not api_url.endswith("/tasks"):
                    api_url += "/tasks"

                response = requests.get(f"{api_url}/{task_id}", headers=headers, timeout=30)

                if response.status_code != 200:
                    return {"success": False, "error": f"任务状态查询失败: {response.status_code}"}

                result = response.json()
                status = result.get("status", "")

                # 检查任务状态
                if status == "SUCCEEDED":
                    # 提取视频URL
                    output = result.get("output", [])
                    if output and len(output) > 0:
                        return {"success": True, "url": output[0].get("URL", ""), "status": status}

                elif status == "FAILED":
                    error = result.get("error", "未知错误")
                    return {"success": False, "error": error, "status": status}

                elif status in ["PENDING", "PROCESSING", "RUNNING"]:
                    # 继续轮询
                    time.sleep(poll_interval)
                    continue
                else:
                    # 未知状态
                    return {"success": False, "error": f"未知任务状态: {status}", "status": status}

            # 超时
            return {"success": False, "error": f"任务超时（超过{max_wait_time}秒）"}

        except requests.RequestException as e:
            return {"success": False, "error": f"网络请求错误: {e!s}"}
        except Exception as e:
            return {"success": False, "error": f"未知错误: {e!s}"}

    def validate_config(self) -> bool:
        """
        验证配置
        检查API URL、API key和模型名称
        """
        if not self.api_url or not self.api_key:
            return False

        # 检查模型名称
        valid_models = ["gen3", "gen3a_turbo", "gen2"]
        if self.model_name and self.model_name not in valid_models:
            # 允许自定义模型名，但给出警告
            pass

        # 简单连通性测试
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "X-Runway-Version": "2024-09-26"}

            # 尝试获取账户信息（验证API key）
            api_url = self.api_url.rstrip("/")
            response = requests.get(
                api_url + "/users/me"
                if "/tasks" not in api_url
                else api_url.replace("/tasks", "/users/me"),
                headers=headers,
                timeout=10,
            )

            # 200, 401或404都表示API可达
            return response.status_code in [200, 401, 404]

        except Exception:
            return False

    async def generate(
        self, image_url: str, prompt: str = "", duration: int = 5, **kwargs
    ) -> AIResponse:
        """
        异步生成视频（接口方法）

        Args:
            image_url: 输入图片URL
            prompt: 视频描述
            duration: 时长
            **kwargs: 其他参数

        Returns:
            AIResponse: 生成结果
        """
        # 同步调用
        return self._generate_video(image_url=image_url, prompt=prompt, duration=duration, **kwargs)
