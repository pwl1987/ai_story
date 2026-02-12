"""
物品序列化器 (Story 12-4 拆分 - item.py)

包含物品档案序列化器
"""

from rest_framework import serializers

from apps.artworks.models import ItemProfile


class ItemProfileSerializer(serializers.ModelSerializer):
    """物品档案序列化器"""
    
    item_type_display = serializers.CharField(source="get_item_type_display", read_only=True)
    item_image_url = serializers.ImageField(source="item_image", read_only=True)
    character_name = serializers.CharField(
        source="associated_character.display_name", read_only=True, allow_null=True
    )
    
    class Meta:
        model = ItemProfile
        fields = [
            "id",
            "artwork",
            "name",
            "item_type",
            "item_type_display",
            "description",
            "appearance_context",
            "item_image",
            "item_image_url",
            "usage_count",
            "first_appearance_chapter",
            "associated_character",
            "character_name",
            "created_at",
            "updated_at",
        ]
