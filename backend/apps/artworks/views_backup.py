"""
角色资产管理 API ViewSets

遵循DRF最佳实践:
- ViewSet分离
- 权限控制
- 自定义Action
"""

import io
import pytest
from PIL import Image
from apps.artworks.models import ScriptScene, Shot, Chapter, Artwork
from apps.artworks.services import (
    FrameExtractionService,
    get_frame_extraction_service,
)
from rest_framework import status, viewsets


class ScriptSceneViewSet(viewsets.ModelViewSet):
    """场景管理 ViewSet（包含首尾帧提取功能）"""

    @action(detail=True, methods=["post"])
    def extract_frames(self, request, pk=None):
        """提取场景的首帧和尾帧"""
        scene = self.get_object()

        if not scene.shots.exists():
            return Response(
                {"error": "该场景没有可提取的镜头"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 获取服务并执行提取
        service = get_frame_extraction_service()
        result = service.extract_frames(scene.id)

        # 添加完整的 URL 路径
        if result.get("head_frame_url"):
            result["head_frame_url"] = scene.head_frame.url if scene.head_frame else None
        if result.get("tail_frame_url"):
            result["tail_frame_url"] = scene.tail_frame.url if scene.tail_frame else None

        return Response(result, status=status.HTTP_200_OK)