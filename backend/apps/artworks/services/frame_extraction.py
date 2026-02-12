"""
首尾帧自动提取服务

职责:
- 智能识别场景的首帧和尾帧
- 优化图片质量（统一 1080p JPEG）
- 保存到 ScriptScene 模型
- 支持重新提取，覆盖已有的首尾帧

Epic 12 Story 12-5: 首尾帧自动提取服务
改进: 代码评审优化建议 (2026-02-12)
"""

import functools
import io
import logging
import time
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

from apps.artworks.models import ScriptScene, Shot

logger = logging.getLogger(__name__)


# ========== 配置常量 (从 Django settings 读取) ==========
# 如果 settings 中没有配置，使用默认值
FRAME_TARGET_SIZE: Tuple[int, int] = getattr(
    settings, 'FRAME_EXTRACTION_TARGET_SIZE', (1920, 1080)
)
FRAME_JPEG_QUALITY: int = getattr(
    settings, 'FRAME_EXTRACTION_JPEG_QUALITY', 85
)
FRAME_MAX_RETRIES: int = getattr(
    settings, 'FRAME_EXTRACTION_MAX_RETRIES', 2
)


def log_extraction_time(func):
    """
    性能监控装饰器

    记录帧提取操作的执行时间，用于性能分析和监控

    Args:
        func: 被装饰的函数

    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.info(f"{func.__name__} 执行时间: {elapsed:.3f}秒")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"{func.__name__} 执行失败 ({elapsed:.3f}秒): {str(e)}")
            raise
    return wrapper


class FrameExtractionService:
    """
    首尾帧提取服务

    职责:
    - 智能识别场景的首帧和尾帧
    - 优化图片质量（统一 1080p JPEG）
    - 保存到 ScriptScene 模型

    配置:
    - FRAME_TARGET_SIZE: 目标分辨率 (1920x1080) - 从 settings 读取
    - FRAME_JPEG_QUALITY: JPEG 质量 (1-100) - 从 settings 读取
    """

    @log_extraction_time
    def extract_frames(self, scene_id: int) -> Dict[str, Any]:
        """
        提取场景的首帧和尾帧

        Args:
            scene_id: 场景 ID (必须大于 0)

        Returns:
            dict: {
                'success': bool,
                'head_frame_url': str | None,
                'tail_frame_url': str | None,
                'message': str,
                'extraction_time': float  # 提取耗时（秒）
            }

        Raises:
            ValueError: 场景不存在、没有镜头或 scene_id 无效
        """
        # 输入验证: scene_id 必须大于 0
        if not isinstance(scene_id, int) or scene_id <= 0:
            raise ValueError(f"无效的场景 ID: {scene_id} (必须为正整数)")

        try:
            scene = ScriptScene.objects.get(pk=scene_id)
        except ScriptScene.DoesNotExist:
            raise ValueError(f"场景 {scene_id} 不存在")

        shots = scene.shots.all()
        if not shots.exists():
            raise ValueError(f"场景 {scene_id} 没有可提取的镜头")

        start_time = time.perf_counter()
        head_shot = self._find_head_shot(shots)
        tail_shot = self._find_tail_shot(shots)
        extraction_time = time.perf_counter() - start_time

        result = {
            'success': True,
            'head_frame_url': None,
            'tail_frame_url': None,
            'message': '提取成功',
            'extraction_time': round(extraction_time, 3)
        }

        if head_shot:
            head_frame_file = self._extract_and_optimize_frame(head_shot, 'head', scene)
            if head_frame_file:
                scene.head_frame = head_frame_file
                result['head_frame_url'] = scene.head_frame.name if scene.head_frame else None
                logger.info(f"首帧提取成功: scene={scene_id}, shot={head_shot.id}")

        if tail_shot:
            tail_frame_file = self._extract_and_optimize_frame(tail_shot, 'tail', scene)
            if tail_frame_file:
                scene.tail_frame = tail_frame_file
                result['tail_frame_url'] = scene.tail_frame.name if scene.tail_frame else None
                logger.info(f"尾帧提取成功: scene={scene_id}, shot={tail_shot.id}")

        scene.save(update_fields=['head_frame', 'tail_frame'])
        return result

    def _find_head_shot(self, shots) -> Optional[Shot]:
        """
        查找首帧镜头

        优先级：is_head_frame=True > sort_order=1

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 找到的首帧镜头，如果没有则返回 None
        """
        # 优先使用用户标记的首帧
        marked_head = shots.filter(is_head_frame=True).first()
        if marked_head:
            logger.debug(f"使用标记的首帧: shot={marked_head.id}")
            return marked_head

        # 否则使用序列第一个
        first_shot = shots.order_by("sort_order").first()
        if first_shot:
            logger.debug(f"使用序列首帧: shot={first_shot.id}")
        return first_shot

    def _find_tail_shot(self, shots) -> Optional[Shot]:
        """
        查找尾帧镜头

        优先级：is_tail_frame=True > max(sort_order)

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 找到的尾帧镜头，如果没有则返回 None
        """
        # 优先使用用户标记的尾帧
        marked_tail = shots.filter(is_tail_frame=True).first()
        if marked_tail:
            logger.debug(f"使用标记的尾帧: shot={marked_tail.id}")
            return marked_tail

        # 否则使用序列最后一个
        last_shot = shots.order_by("-sort_order").first()
        if last_shot:
            logger.debug(f"使用序列尾帧: shot={last_shot.id}")
        return last_shot

    @log_extraction_time
    def _extract_and_optimize_frame(
        self, shot: Shot, frame_type: str, scene: ScriptScene
    ) -> Optional[ContentFile]:
        """
        提取并优化单帧图片

        Args:
            shot: Shot 实例
            frame_type: 'head' 或 'tail'
            scene: ScriptScene 实例（用于生成文件名）

        Returns:
            Optional[ContentFile]: 优化后的图片文件，如果失败则返回 None

        Raises:
            IOError: 图片文件损坏或不存在
        """
        if not shot.generated_image or not shot.generated_image.path:
            logger.warning(f"镜头 {shot.id} 没有图片文件")
            return None

        try:
            # 打开原始图片
            with Image.open(shot.generated_image.path) as img:
                # 转换为 RGB（处理 RGBA 等格式）
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # 调整大小到 1080p（保持宽高比）
                original_size = img.size
                img.thumbnail(FRAME_TARGET_SIZE, Image.Resampling.LANCZOS)

                # 保存到内存
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=FRAME_JPEG_QUALITY, optimize=True)
                buffer.seek(0)

                # 生成文件名
                filename = f"{frame_type}_{scene.id}_{shot.id}.jpg"

                logger.debug(
                    f"图片优化完成: shot={shot.id}, "
                    f"{original_size[0]}x{original_size[1]} -> {img.size[0]}x{img.size[1]}"
                )

                return ContentFile(buffer.read(), name=filename)

        except OSError as e:
            # 记录错误但不中断流程
            logger.error(f"图片处理失败: shot={shot.id}, error={str(e)}")
            return None


# 单例模式，便于导入使用
_service_instance: Optional[FrameExtractionService] = None


def get_frame_extraction_service() -> FrameExtractionService:
    """
    获取首尾帧提取服务单例

    Returns:
        FrameExtractionService: 服务实例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = FrameExtractionService()
    return _service_instance
