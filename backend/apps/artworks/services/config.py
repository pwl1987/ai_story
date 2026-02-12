"""
首尾帧提取服务配置

Epic 12 Story 12-5: 首尾帧自动提取服务
改进: 代码评审优化建议 (2026-02-12)
- ARCH-H-003: OCP 违反 - 配置对象化
"""

from dataclasses import dataclass
from typing import Tuple

from django.conf import settings


@dataclass
class FrameExtractionConfig:
    """
    帧提取配置

    配置项:
    - target_size: 目标分辨率 (宽, 高)
    - jpeg_quality: JPEG 质量 (1-100)
    - max_retries: 最大重试次数
    - max_reasonable_id: 最大合理场景 ID (用于 DoS 防护)

    Example:
        >>> config = FrameExtractionConfig.from_settings()
        >>> print(config.target_size)
        (1920, 1080)
    """

    target_size: Tuple[int, int] = (1920, 1080)
    jpeg_quality: int = 85
    max_retries: int = 2
    max_reasonable_id: int = 10**9  # 10 亿

    @classmethod
    def from_settings(cls) -> "FrameExtractionConfig":
        """
        从 Django settings 加载配置

        读取以下配置项:
        - FRAME_EXTRACTION_TARGET_SIZE: 目标分辨率
        - FRAME_EXTRACTION_JPEG_QUALITY: JPEG 质量
        - FRAME_EXTRACTION_MAX_RETRIES: 最大重试次数

        Returns:
            FrameExtractionConfig: 配置实例
        """
        target_size = getattr(settings, "FRAME_EXTRACTION_TARGET_SIZE", (1920, 1080))
        jpeg_quality = getattr(settings, "FRAME_EXTRACTION_JPEG_QUALITY", 85)
        max_retries = getattr(settings, "FRAME_EXTRACTION_MAX_RETRIES", 2)
        max_reasonable_id = getattr(settings, "FRAME_EXTRACTION_MAX_REASONABLE_ID", 10**9)

        # 验证配置
        cls._validate_config(target_size, jpeg_quality, max_retries, max_reasonable_id)

        return cls(
            target_size=target_size,
            jpeg_quality=jpeg_quality,
            max_retries=max_retries,
            max_reasonable_id=max_reasonable_id,
        )

    @staticmethod
    def _validate_config(
        target_size: Tuple[int, int],
        jpeg_quality: int,
        max_retries: int,
        max_reasonable_id: int,
    ) -> None:
        """
        验证配置有效性

        Args:
            target_size: 目标分辨率
            jpeg_quality: JPEG 质量
            max_retries: 最大重试次数
            max_reasonable_id: 最大合理场景 ID

        Raises:
            ValueError: 配置无效时
        """
        # 验证目标尺寸
        if not isinstance(target_size, (tuple, list)) or len(target_size) != 2:
            raise ValueError("FRAME_EXTRACTION_TARGET_SIZE 必须是包含两个整数的元组")

        width, height = target_size
        if not (isinstance(width, int) and isinstance(height, int)):
            raise ValueError("FRAME_EXTRACTION_TARGET_SIZE 的宽度和高度必须是整数")

        if width <= 0 or height <= 0:
            raise ValueError(f"无效的目标尺寸: {width}x{height} (必须为正数)")

        if width > 7680 or height > 4320:  # 8K 上限
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"目标尺寸过大: {width}x{height}, 可能影响性能")

        # 验证 JPEG 质量
        if not isinstance(jpeg_quality, int):
            raise ValueError("FRAME_EXTRACTION_JPEG_QUALITY 必须是整数")

        if not (1 <= jpeg_quality <= 100):
            raise ValueError(f"无效的 JPEG 质量: {jpeg_quality} (范围: 1-100)")

        # 验证重试次数
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("FRAME_EXTRACTION_MAX_RETRIES 必须是非负整数")

        # 验证最大合理 ID
        if not isinstance(max_reasonable_id, int) or max_reasonable_id <= 0:
            raise ValueError("FRAME_EXTRACTION_MAX_REASONABLE_ID 必须是正整数")


# 默认配置实例
_default_config: FrameExtractionConfig | None = None


def get_frame_config() -> FrameExtractionConfig:
    """
    获取帧提取配置 (单例模式)

    Returns:
        FrameExtractionConfig: 配置实例
    """
    global _default_config
    if _default_config is None:
        _default_config = FrameExtractionConfig.from_settings()
    return _default_config
