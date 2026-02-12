"""
帧选择策略

Epic 12 Story 12-5: 首尾帧自动提取服务
改进: 代码评审优化建议 (2026-02-12)
- ARCH-H-001: SRP 违反 - 帧选择策略独立

职责:
- 定义帧选择策略接口
- 实现默认帧选择逻辑
"""

import logging
from typing import Optional, Protocol

from django.db.models import QuerySet

from apps.artworks.models import Shot

logger = logging.getLogger(__name__)


# ============ 策略接口 (使用 Protocol) ============


class FrameSelectionStrategy(Protocol):
    """
    帧选择策略接口

    定义首尾帧选择策略的协议。
    """

    def select_head_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        选择首帧镜头

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 选中的首帧镜头，无合适镜头则返回 None
        """
        ...

    def select_tail_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        选择尾帧镜头

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 选中的尾帧镜头，无合适镜头则返回 None
        """
        ...


# ============ 默认策略实现 ============


class DefaultFrameSelectionStrategy:
    """
    默认帧选择策略

    选择逻辑:
    - 首帧: 优先 is_head_frame=True，否则 sort_order 最小
    - 尾帧: 优先 is_tail_frame=True，否则 sort_order 最大
    """

    def select_head_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        选择首帧镜头

        优先级：
        1. 用户标记 is_head_frame=True
        2. sort_order 最小的镜头

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 选中的首帧镜头
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

    def select_tail_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        选择尾帧镜头

        优先级：
        1. 用户标记 is_tail_frame=True
        2. sort_order 最大的镜头

        Args:
            shots: Shot QuerySet

        Returns:
            Optional[Shot]: 选中的尾帧镜头
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



__all__ = [
    "DefaultFrameSelectionStrategy",
    "FrameSelectionStrategy",
]
