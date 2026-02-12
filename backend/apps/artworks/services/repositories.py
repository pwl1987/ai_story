"""
仓储模式实现 - 数据访问抽象层

Epic 12 Story 12-5: 首尾帧自动提取服务
改进: 代码评审优化建议 (2026-02-12)
- ARCH-H-002: DIP 违反 - 引入仓储模式

遵循依赖倒置原则 (DIP):
- 服务层依赖抽象接口而非具体实现
- 便于单元测试和业务逻辑隔离
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from django.core.files.base import File
from django.db.models import QuerySet

from apps.artworks.models import ScriptScene, Shot

logger = logging.getLogger(__name__)


# ============ 仓储接口定义 ============


class ISceneRepository(ABC):
    """
    场景仓储接口

    定义场景数据访问的抽象接口，遵循依赖倒置原则。
    """

    @abstractmethod
    def get_by_id(self, scene_id: int) -> Optional[ScriptScene]:
        """
        根据 ID 获取场景

        Args:
            scene_id: 场景 ID

        Returns:
            ScriptScene 实例，不存在则返回 None
        """
        pass

    @abstractmethod
    def update_frames(
        self,
        scene: ScriptScene,
        head_frame: Optional[File],
        tail_frame: Optional[File],
    ) -> None:
        """
        更新场景的首尾帧

        Args:
            scene: ScriptScene 实例
            head_frame: 首帧文件 (None 表示不更新)
            tail_frame: 尾帧文件 (None 表示不更新)
        """
        pass

    @abstractmethod
    def get_shots_queryset(self, scene: ScriptScene) -> QuerySet[Shot]:
        """
        获取场景的所有镜头

        Args:
            scene: ScriptScene 实例

        Returns:
            Shot QuerySet
        """
        pass


class IShotRepository(ABC):
    """
    镜头仓储接口

    定义镜头数据访问的抽象接口。
    """

    @abstractmethod
    def find_head_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        查找首帧镜头

        优先级：is_head_frame=True > sort_order 最小

        Args:
            shots: Shot QuerySet

        Returns:
            Shot 实例，不存在则返回 None
        """
        pass

    @abstractmethod
    def find_tail_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        查找尾帧镜头

        优先级：is_tail_frame=True > sort_order 最大

        Args:
            shots: Shot QuerySet

        Returns:
            Shot 实例，不存在则返回 None
        """
        pass


# ============ Django ORM 实现 ============


class DjangoSceneRepository(ISceneRepository):
    """
    基于 Django ORM 的场景仓储实现

    使用 Django ORM 提供数据访问功能。
    """

    def get_by_id(self, scene_id: int) -> Optional[ScriptScene]:
        """
        根据 ID 获取场景

        Args:
            scene_id: 场景 ID

        Returns:
            ScriptScene 实例，不存在则返回 None
        """
        try:
            return ScriptScene.objects.get(pk=scene_id)
        except ScriptScene.DoesNotExist:
            logger.warning(f"场景不存在: scene_id={scene_id}")
            return None

    def update_frames(
        self,
        scene: ScriptScene,
        head_frame: Optional[File],
        tail_frame: Optional[File],
    ) -> None:
        """
        更新场景的首尾帧

        Args:
            scene: ScriptScene 实例
            head_frame: 首帧文件 (None 表示不更新)
            tail_frame: 尾帧文件 (None 表示不更新)
        """
        update_fields = []

        if head_frame is not None:
            scene.head_frame = head_frame
            update_fields.append("head_frame")

        if tail_frame is not None:
            scene.tail_frame = tail_frame
            update_fields.append("tail_frame")

        if update_fields:
            scene.save(update_fields=update_fields)
            logger.info(f"场景首尾帧已更新: scene_id={scene.id}, fields={update_fields}")

    def get_shots_queryset(self, scene: ScriptScene) -> QuerySet[Shot]:
        """
        获取场景的所有镜头

        Args:
            scene: ScriptScene 实例

        Returns:
            Shot QuerySet
        """
        return scene.shots.all()


class DjangoShotRepository(IShotRepository):
    """
    基于 Django ORM 的镜头仓储实现
    """

    def find_head_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        查找首帧镜头

        优先级：is_head_frame=True > sort_order 最小

        Args:
            shots: Shot QuerySet

        Returns:
            Shot 实例，不存在则返回 None
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

    def find_tail_shot(self, shots: QuerySet[Shot]) -> Optional[Shot]:
        """
        查找尾帧镜头

        优先级：is_tail_frame=True > sort_order 最大

        Args:
            shots: Shot QuerySet

        Returns:
            Shot 实例，不存在则返回 None
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


# ============ 仓储工厂 ============


class RepositoryFactory:
    """
    仓储工厂

    负责创建仓储实例，便于依赖注入和测试。
    """

    @staticmethod
    def create_scene_repository() -> ISceneRepository:
        """
        创建场景仓储实例

        Returns:
            ISceneRepository: 场景仓储实例
        """
        return DjangoSceneRepository()

    @staticmethod
    def create_shot_repository() -> IShotRepository:
        """
        创建镜头仓储实例

        Returns:
            IShotRepository: 镜头仓储实例
        """
        return DjangoShotRepository()
