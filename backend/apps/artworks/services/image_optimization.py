"""
图片优化服务

Epic 12 Story 12-5: 首尾帧自动提取服务
改进: 代码评审优化建议 (2026-02-12)
- ARCH-H
器独立


职责:
- 图片格式转换 (RGBA -> RGB)
- 图片尺寸调整 (保持宽高比)
- JPEG 质量优化
"""

from .config import FrameExtractionConfig

import io
import logging
from typing import TYPE_CHECKING, Optional

from django.core.files.base import ContentFile
from PIL import Image

if TYPE_CHECKING:
    from apps.artworks.models import Shot, ScriptScene

logger = logging.getLogger(__name__)


class ImageOptimizationService:
    """
    图片优化服务

    单独职责：处理图片优化逻辑，包括尺寸调整和质量优化。

    Attributes:
        config: 帧提取配置

    Example:
        >>> service = ImageOptimizationService(config)
        >>> result = service.optimize_shot_image(shot, 'head', scene)
        >>> print(result.name if result else None)
        'head_1_5.jpg'
    """

    def __init__(self, config: FrameExtractionConfig):
        """
        初始化图片优化服务

        Args:
            config: 帧提取配置
        """
        self.config = config

    def optimize_shot_image(
        self, shot: "Shot", frame_type: str, scene: "ScriptScene"
    ) -> Optional[ContentFile]:
        """
        优化单张图片

        处理流程:
        1. 验证图片文件存在
        2. 转换为 RGB 格式
        3. 调整尺寸到目标分辨率
        4. 保存为 JPEG 格式

        Args:
            shot: Shot 实例
            frame_type: 'head' 或 'tail'
            scene: ScriptScene 实例（用于生成文件名）

        Returns:
            Optional[ContentFile]: 优化后的图片文件，失败则返回 None

        Raises:
            ValueError: 如果 frame_type 不是 'head' 或 'tail'
        """
        # 参数校验
        """
        优化单张图片

        处理流程:
        1. 验证图片文件存在
        2. 转换为 RGB 格式
        3. 调整尺寸到目标分辨率
        4. 保存为 JPEG 格式

        Args:
            shot: Shot 实例
            frame_type: 'head' 或 'tail'
            scene: ScriptScene 实例（用于生成文件名）

        Returns:
            Optional[ContentFile]: 优化后的图片文件，失败则返回 None

        Raises:
            ValueError: 如果 frame_type 不是 'head' 或 'tail'
        """
        # 参数校验
        if frame_type not in ("head", "tail"):
            raise ValueError(f"无效的 frame_type: {frame_type} (必须是 'head' 或 'tail')")

        # 验证图片文件存在
        if not shot.generated_image or not shot.generated_image.path:
            logger.warning(f"镜头 {shot.id} 没有图片文件")
            return None

        # 验证图片文件有效性
        if not self._is_valid_image_file(shot.generated_image.path):
            logger.error(f"镜头 {shot.id} 的图片文件无效")
            return None

        try:
            # 打开原始图片
            with Image.open(shot.generated_image.path) as img:
                # 转换为 RGB（处理 RGBA 等格式）
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # 调整大小到目标分辨率（保持宽高比）
                original_size = img.size
                img.thumbnail(self.config.target_size, Image.Resampling.LANCZOS)

                # 保存到内存
                buffer = io.BytesIO()
                img.save(
                    buffer,
                    format="JPEG",
                    quality=self.config.jpeg_quality,
                    optimize=True,
                )
                buffer.seek(0)

                # 生成文件名
                filename = f"{frame_type}_{scene.id}_{shot.id}.jpg"

                logger.debug(
                    f"图片优化完成: shot={shot.id}, "
                    f"{original_size[0]}x{original_size[1]} -> {img.size[0]}x{img.size[1]}"
                )

                return ContentFile(buffer.read(), name=filename)

        except OSError as e:
            logger.error(f"图片处理失败: shot={shot.id}, error={e!s}")
            return None
        finally:
            # 确保资源释放
            if "buffer" in locals():
                buffer.close()

    def _is_valid_image_file(self, file_path: str) -> bool:
        """
        验证图片文件有效性

        检查:
        - 文件存在
        - 文件大小合理 (>100 字节)
        - 图片可正常打开
        - 图片尺寸合理

        Args:
            file_path: 图片文件路径

        Returns:
            bool: 文件是否有效
        """
        import os

        if not os.path.exists(file_path):
            return False

        file_size = os.path.getsize(file_path)
        if file_size < 100:  # 小于 100 字节视为无效
            return False

        try:
            with Image.open(file_path) as img:
                img.verify()  # 验证图片完整性
            # 重新打开读取尺寸 (verify() 会关闭文件)
            with Image.open(file_path) as img:
                if img.width < 1 or img.height < 1:
                    return False
                # 超过 100MP 视为异常
                if img.width * img.height > 100000000:
                    logger.warning(f"图片尺寸异常大: {img.width}x{img.height}")
            return True
        except Exception as e:
            logger.warning(f"图片验证失败: {file_path}, error={e}")
            return False
