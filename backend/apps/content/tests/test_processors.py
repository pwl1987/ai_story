"""
处理器测试
测试LLMStageProcessor, Text2ImageStageProcessor, Image2VideoStageProcessor
遵循单一职责原则(SRP)
"""

from unittest.mock import Mock

import pytest

from apps.content.processors.image2video_stage import Image2VideoStageProcessor
from apps.content.processors.llm_stage import LLMStageProcessor
from apps.content.processors.text2image_stage import Text2ImageStageProcessor

# ============================================================================
# LLMStageProcessor 测试
# ============================================================================


@pytest.mark.django_db
class TestLLMStageProcessor:
    """
    测试LLM阶段处理器
    职责: 验证处理器初始化和基本属性
    遵循单一职责原则(SRP)
    """

    def test_init_valid_stage_types(self):
        """测试初始化 - 有效阶段类型"""
        valid_stage_types = ["rewrite", "storyboard", "camera_movement"]

        for stage_type in valid_stage_types:
            processor = LLMStageProcessor(stage_type=stage_type)
            assert processor.stage_type == stage_type

    def test_validate_context_not_found(self):
        """测试验证 - 项目不存在"""
        processor = LLMStageProcessor(stage_type="rewrite")
        context = Mock(project_id="00000000-0000-0000-0000-000000000000")

        result = processor.validate(context)

        assert result is False

    def test_processor_has_stage_type(self):
        """测试处理器有stage_type属性"""
        processor = LLMStageProcessor(stage_type="rewrite")

        assert hasattr(processor, "stage_type")
        assert processor.stage_type == "rewrite"


# ============================================================================
# Text2ImageStageProcessor 测试
# ============================================================================


@pytest.mark.django_db
class TestText2ImageStageProcessor:
    """
    测试文生图处理器
    职责: 验证处理器初始化和基本属性
    遵循单一职责原则(SRP)
    """

    def test_init(self):
        """测试初始化"""
        processor = Text2ImageStageProcessor()

        assert processor is not None
        assert processor.stage_type == "image_generation"

    def test_processor_has_required_methods(self):
        """测试处理器有必需的方法"""
        processor = Text2ImageStageProcessor()

        # 检查是否有核心方法
        assert hasattr(processor, "validate")
        assert hasattr(processor, "process_stream")


# ============================================================================
# Image2VideoStageProcessor 测试
# ============================================================================


@pytest.mark.django_db
class TestImage2VideoStageProcessor:
    """
    测试图生视频处理器
    职责: 验证处理器初始化和基本属性
    遵循单一职责原则(SRP)
    """

    def test_init(self):
        """测试初始化"""
        processor = Image2VideoStageProcessor()

        assert processor is not None
        assert processor.stage_type == "video_generation"

    def test_processor_has_required_methods(self):
        """测试处理器有必需的方法"""
        processor = Image2VideoStageProcessor()

        # 检查是否有核心方法
        assert hasattr(processor, "validate")
        assert hasattr(processor, "process_stream")
