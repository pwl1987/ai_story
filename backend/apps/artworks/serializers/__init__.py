"""
角色资产管理 API 序列化器模块

按功能域拆分序列化器，提高代码可维护性。

Story 12-4 修复 - P2-1
"""

from .workflow import ChapterWorkflowSerializer, WorkflowEventSerializer
from .scene import (
    ScriptSceneSerializer,
    ShotSerializer,
    ShotVersionSerializer,
    ScriptSceneDetailSerializer,
    ShotDetailSerializer,
    ShotVersionDetailSerializer,
)
from .character import (
    CharacterPoseSerializer,
    CharacterVoiceConfigSerializer,
    CharacterProfileSerializer,
    CharacterProfileDetailSerializer,
    RegenerateShotSerializer,
)
from .artwork import ArtworkSerializer, ArtworkDetailSerializer
from .item import ItemProfileSerializer
from .batch import GenerationProgressSerializer, GenerationHistorySerializer

__all__ = [
    # Workflow (Story 12-4)
    "ChapterWorkflowSerializer",
    "WorkflowEventSerializer",
    # Scene (Story 11.2.x)
    "ScriptSceneSerializer",
    "ShotSerializer",
    "ShotVersionSerializer",
    "ScriptSceneDetailSerializer",
    "ShotDetailSerializer",
    "ShotVersionDetailSerializer",
    # Character (Story 11.1.x)
    "CharacterPoseSerializer",
    "CharacterVoiceConfigSerializer",
    "CharacterProfileSerializer",
    "CharacterProfileDetailSerializer",
    "RegenerateShotSerializer",
    # Artwork
    "ArtworkSerializer",
    "ArtworkDetailSerializer",
    # Item
    "ItemProfileSerializer",
    # Batch Generation (Story 11.1.4)
    "GenerationProgressSerializer",
    "GenerationHistorySerializer",
]
