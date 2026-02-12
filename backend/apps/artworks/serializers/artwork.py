"""
作品序列化器 (Story 12-4 拆分 - artwork.py)

包含 ArtworkSerializer 和 ArtworkDetailSerializer
"""

from rest_framework import serializers

from apps.artworks.models import Artwork


class ArtworkSerializer(serializers.ModelSerializer):
    """作品序列化器"""
    artwork_type_display = serializers.CharField(source="get_artwork_type_display", read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    character_count = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = [
            "id",
            "title",
            "author",
            "artwork_type",
            "artwork_type_display",
            "progress_percentage",
            "character_count",
            "item_count",
        ]
        read_only_fields = ["id"]


class ArtworkDetailSerializer(ArtworkSerializer):
    """作品详情序列化器（包含角色和物品）"""
    characters = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = ArtworkSerializer.Meta.fields + ["characters", "items"]
