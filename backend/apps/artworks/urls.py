"""
角色资产管理 API URL配置

遵循RESTful API设计规范
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .batch_views import BatchGenerationViewSet
from .views import (
    ArtworkViewSet,
    CharacterPoseViewSet,
    CharacterProfileViewSet,
    CharacterVoiceConfigViewSet,
    GenerationProgressViewSet,
    ItemProfileViewSet,
    ScriptSceneViewSet,
    ShotViewSet,
    ShotVersionViewSet,
)

app_name = "artworks"

router = DefaultRouter()
router.register(r"artworks", ArtworkViewSet, basename="artwork")
router.register(r"characters", CharacterProfileViewSet, basename="character")
router.register(r"poses", CharacterPoseViewSet, basename="pose")
router.register(r"voice-configs", CharacterVoiceConfigViewSet, basename="voice-config")
router.register(r"items", ItemProfileViewSet, basename="item")
router.register(r"script-scenes", ScriptSceneViewSet, basename="script-scene")
router.register(r"shots", ShotViewSet, basename="shot")
router.register(r"shot-versions", ShotVersionViewSet, basename="shot-version")
router.register(r"batch-generation", BatchGenerationViewSet, basename="batch-generation")
router.register(r"progress", GenerationProgressViewSet, basename="progress")

urlpatterns = [
    path("", include(router.urls)),
]
